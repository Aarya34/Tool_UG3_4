from flask import Flask, request, jsonify
from flask_cors import CORS
from app import analyze_repo
import traceback  # Add this import
import os

app = Flask(__name__)
CORS(app, resources={r"/analyze": {"origins": "*"}})  # Explicit CORS for /analyze

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json()
        repo_url = data.get("repo_url")
        results = analyze_repo(repo_url)
        
        # Transform results to include relative paths
        transformed = {
            "python": {
                os.path.basename(path): details 
                for path, details in results["python"].items()
            },
            "javascript": {
                os.path.basename(path): details 
                for path, details in results["javascript"].items()
            }
        }
        return jsonify(transformed)
    except Exception as e:
        print(f"[SERVER ERROR] {traceback.format_exc()}")  # Full error logging
        return jsonify({"error": f"Backend error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True, host='0.0.0.0')  # Allow external connections