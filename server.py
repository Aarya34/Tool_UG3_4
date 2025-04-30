from flask import Flask, request, jsonify
from flask_cors import CORS
from detector.app import analyze_repo
import traceback
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage
import re
from refactor.js_refactor import refactor_js_code
from refactor.py_refactor import refactor_python_code

load_dotenv()  # loads .env file
ref = ChatGroq(
    temperature=0.6,
    max_tokens=4096,
    groq_api_key=os.getenv("GROQ_API_KEY"),  # Fetch API key securely from environment
    model_name="deepseek-r1-distill-llama-70b"  # Model name for ChatGroq
)

app = Flask(__name__)
CORS(app, resources={r"/analyze": {"origins": "*"}})
CORS(app, resources={r"/refactor_code_ref": {"origins": "http://127.0.0.1:5500"}})
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json()
        repo_url = data.get("repo_url")
        if not repo_url:
            return jsonify({"error": "Missing 'repo_url' in request body"}), 400

        results = analyze_repo(repo_url)

        # Transform results to include just the file names as keys
        transformed = {
            "python": {
                os.path.basename(path): details 
                for path, details in results["python"].items()
            },
            "javascript": {
                os.path.basename(path): details
                for path, details in results["javascript"].items()
            },
            "metadata": results.get("metadata", {})
        }

        return jsonify(transformed)

    except Exception as e:
        print(f"[SERVER ERROR] {traceback.format_exc()}")  # Optional: log full traceback
        return jsonify({"error": f"Backend error: {str(e)}"}), 500

def extract_code_from_response(response_text):
    code_blocks = re.findall(r"```(?:\w*\n)?(.*?)```", response_text, re.DOTALL)
    if code_blocks:
        return code_blocks[0].strip()
    return response_text.strip()

@app.route('/refactor_code_ref', methods=['POST'])
def refactor_code_ref():
    data = request.get_json()
    input_code = data.get("code", "")
    input_smells = data.get("fileSmells", [])

    # print(input_smells)

    if not input_code.strip():
        return jsonify({"error": "No code provided"}), 400

    try:
        with open("refactor.txt", "r") as file:
            text_template = file.read()

        smell_text = "\n".join([f"{i+1}. {smell}" for i, smell in enumerate(input_smells)])

        text = (
            text_template
            .replace("{input_code}", input_code)
            .replace("{smells}", smell_text)
        )
        
        text = text.replace("{input_code}", input_code)

        response = ref.invoke([HumanMessage(content=text)])
        full_response = response.content if hasattr(response, 'content') else str(response)
        refactored_code = extract_code_from_response(full_response)
        return jsonify({"refactored_code": refactored_code})

    except Exception as e:
        print(f"Error: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True, host='0.0.0.0')