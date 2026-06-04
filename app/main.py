from flask import Flask, jsonify

from app.config.database import check_database
from app.routes.authorities import authorities_bp
from app.routes.sites import sites_bp
from app.routes.zones import zones_bp
from app.routes.droneports import droneports_bp

app = Flask(__name__)

app.register_blueprint(authorities_bp)
app.register_blueprint(sites_bp)
app.register_blueprint(zones_bp)
app.register_blueprint(droneports_bp)

@app.route("/health")
def health():
    return jsonify({
        "status": "ok"
    })


@app.route("/api/system/database")
def database_status():
    return jsonify(check_database())

