from flask import Flask, request, jsonify
from flask_cors import CORS
from detector.app import analyze_repo
import traceback
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage
import re

load_dotenv()  # loads .env file
llm = ChatGroq(
    temperature=0.6,
    max_tokens=4096,
    groq_api_key=os.getenv("GROQ_API_KEY"),  # Fetch API key securely from environment
    model_name="deepseek-r1-distill-llama-70b"  # Model name for ChatGroq
)

app = Flask(__name__)
CORS(app, resources={r"/analyze": {"origins": "*"}})
CORS(app, resources={r"/refactor_code_llm": {"origins": "http://127.0.0.1:3000"}})
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
    """
    Extracts the first code block from the LLM response.
    Assumes code is enclosed in triple backticks.
    """
    code_blocks = re.findall(r"(?:\w*\n)?(.*?)", response_text, re.DOTALL)
    if code_blocks:
        return code_blocks[0].strip()
    return response_text.strip()

@app.route('/refactor_code_llm', methods=['POST'])
def refactor_code_llm():
    data = request.get_json()
    input_code = data.get("code", "")
    input_smells = data.get("fileSmells", [])

    # print(input_smells)

    if not input_code.strip():
        return jsonify({"error": "No code provided"}), 400

    try:
        # Read the prompt from the file
        with open("refactor.txt", "r") as file:
            prompt_template = file.read()

        smell_text = "\n".join([f"{i+1}. {smell}" for i, smell in enumerate(input_smells)])

        # Replace placeholders
        prompt = (
            prompt_template
            .replace("{input_code}", input_code)
            .replace("{smells}", smell_text)
        )
        
        prompt = prompt.replace("{input_code}", input_code)

        # Extract the refactored code from the response
        response = llm.invoke([HumanMessage(content=prompt)])
        full_response = response.content if hasattr(response, 'content') else str(response)
        refactored_code = extract_code_from_response(full_response)
        return jsonify({"refactored_code": refactored_code})

    except Exception as e:
        # Log the full traceback for debugging purposes
        print(f"Error: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

if __name__ == "_main_":
    app.run(port=5000, debug=True, host='0.0.0.0')