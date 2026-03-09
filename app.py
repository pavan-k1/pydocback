from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt
import os, shutil, secrets, datetime
import os
from dotenv import load_dotenv

load_dotenv()

from doc_report import docstring_coverage
from parsor import extract_nodes
from main import analyze_and_generate
from validator import validate_pep257

import mysql.connector


app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
GENERATED_FOLDER = os.path.join(BASE_DIR, "generated")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)


db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "pydoc_generator")
}

def get_db_connection():
    return mysql.connector.connect(**db_config)


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"msg": "Username and password required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
    if cursor.fetchone():
        cursor.close(); conn.close()
        return jsonify({"msg": "Username already exists"}), 400

    hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_pw))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"msg": "User registered successfully"}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"msg": "Username and password required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user or not bcrypt.check_password_hash(user["password"], password):
        return jsonify({"msg": "Invalid credentials"}), 401

    token = secrets.token_hex(16)
    return jsonify({"token": token, "username": username})


@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")
    username = request.args.get("username")
    if not file or not username:
        return jsonify({"error": "File or username missing"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_files (username, filename, file_type) VALUES (%s, %s, %s)",
        (username, filename, "uploaded")
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"filename": filename})


@app.route("/user_files/<username>", methods=["GET"])
def get_user_files(username):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT filename, file_type FROM user_files WHERE username=%s", (username,))
    files = cursor.fetchall()
    cursor.close()
    conn.close()

    uploaded = [f["filename"] for f in files if f["file_type"] == "uploaded"]
    generated = [f["filename"] for f in files if f["file_type"] == "generated"]

    return jsonify({"uploaded": uploaded, "generated": generated})



@app.route("/analyze", methods=["POST"])
def analyze_code():
    data = request.get_json()
    filename = data["filename"]
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    _, nod, _, _ = extract_nodes(filepath)
    total_coverage = docstring_coverage(filepath)

    result = [{"name": n["name"], "type": n["type"], "hasDocstring": n["hasDocstring"], "coverage": 100 if n["hasDocstring"] else 0} for n in nod]

    return jsonify({"nodes": result, "tree": nod, "coverage": total_coverage})


@app.route("/upanalyze", methods=["POST"])
def upanalyze_code():
    data = request.get_json()
    filename = data["filename"]
    filepath = os.path.join(GENERATED_FOLDER, filename)

    _, nod, _, _ = extract_nodes(filepath)
    total_coverage = docstring_coverage(filepath)

    result = [{"name": n["name"], "type": n["type"], "hasDocstring": n["hasDocstring"], "coverage": 100 if n["hasDocstring"] else 0} for n in nod]

    return jsonify({"nodes": result, "tree": nod, "coverage": total_coverage})



@app.route("/generate", methods=["POST"])
def generate_docstrings():
    data = request.get_json()
    filename = data["filename"]
    style = data.get("style", "google")
    username = data.get("username")  # <- get username from request

    original_path = os.path.join(UPLOAD_FOLDER, filename)
   
    generated_filename = f"generated_{filename}"
    generated_path = os.path.join(GENERATED_FOLDER, generated_filename)

    shutil.copy(original_path, generated_path)

   
    analyze_and_generate(generated_path, style)

    with open(original_path, "r", encoding="utf-8") as f:
        original_code = f.read()
    with open(generated_path, "r", encoding="utf-8") as f:
        updated_code = f.read()


    if username:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_files (username, filename, file_type) VALUES (%s, %s, %s)",
            (username, generated_filename, "generated")
        )
        conn.commit()
        cursor.close()
        conn.close()

    return jsonify({
        "original": original_code,
        "updated": updated_code,
        "generatedFile": generated_filename
    })




@app.route("/validate", methods=["POST"])
def validate_docstrings():
    data = request.get_json()
    filename = data["filename"]
    filetype = data.get("type", "generated")

    folder = UPLOAD_FOLDER if filetype == "original" else GENERATED_FOLDER
    filepath = os.path.join(folder, filename)

    result = validate_pep257(filepath)

    return jsonify({
        "passed": result.get("passed", False),
        "errors": result.get("errors", []),
        "message": result.get("message", "PEP 257 validation completed")
    })



@app.route("/download/<filename>")
def download_file(filename):
    gen_path = os.path.join(GENERATED_FOLDER, filename)
    upload_path = os.path.join(UPLOAD_FOLDER, filename)

    if os.path.exists(gen_path):
        return send_file(gen_path, as_attachment=True)

    elif os.path.exists(upload_path):
        return send_file(upload_path, as_attachment=True)

    else:
        return jsonify({"error": "File not found"}), 404

@app.route("/save_edit", methods=["POST"])
def save_edit():
    data = request.get_json()
    filename = data.get("filename")
    content = data.get("content")

    if not filename or not content:
        return jsonify({"success": False, "error": "Missing data"}), 400

    filepath = os.path.join(GENERATED_FOLDER, filename)

    if not os.path.exists(filepath):
        return jsonify({"success": False, "error": "File not found"}), 404

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return jsonify({"success": True})

import json



@app.route("/load_file_content/<username>/<filename>")
def load_file_content(username, filename):

    upload_path = os.path.join(UPLOAD_FOLDER, filename)
    generated_path = os.path.join(GENERATED_FOLDER, filename)

    original_content = ""
    generated_content = ""

    # If file exists in uploads folder
    if os.path.exists(upload_path):
        with open(upload_path, "r", encoding="utf-8") as f:
            original_content = f.read()

    # If file exists in generated folder
    if os.path.exists(generated_path):
        with open(generated_path, "r", encoding="utf-8") as f:
            generated_content = f.read()

    return jsonify({
        "original": original_content,
        "updated": generated_content,
        "generatedFile": filename
    })

@app.route("/paste_code", methods=["POST"])
def paste_code():
    try:
        data = request.get_json()
        code = data.get("code")
        username = data.get("username")

        if not code or not username:
            return jsonify({"error": "Code or username missing"}), 400

        filename = f"{username}_pasted_code.py"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_files (username, filename, file_type) VALUES (%s, %s, %s)",
            (username, filename, "uploaded")
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"filename": filename})

    except Exception as e:
        print("Paste error:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True,use_reloader=False  )
