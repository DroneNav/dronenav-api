from flask import Flask, jsonify
from app.config.database import check_database

app = Flask(__name__)

@app.route("/health")
def health():
    return jsonify({
        "status": "ok"
    })

@app.route("/api/system/database")
def database_status():
    return jsonify(check_database())
