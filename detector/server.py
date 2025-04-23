from flask import Flask, request, jsonify
from flask_cors import CORS
from app import analyze_repo
import traceback
import os

app = Flask(__name__)
CORS(app, resources={r"/analyze": {"origins": "*"}})

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

if __name__ == "__main__":
    app.run(port=5000, debug=True, host='0.0.0.0')