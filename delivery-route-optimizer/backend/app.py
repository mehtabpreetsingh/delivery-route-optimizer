"""
app.py
------
Small Flask API that exposes the route optimizer over HTTP so the
frontend (or Postman / curl) can send delivery stops and get back
an optimized route.

Run:
    pip install -r requirements.txt
    python app.py

Then open http://localhost:5000 in your browser.
"""

from flask import Flask, request, jsonify, send_from_directory
from optimizer import optimize_route
import os

app = Flask(__name__, static_folder="../frontend", static_url_path="")


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/optimize", methods=["POST"])
def optimize():
    """
    Expects JSON body:
    {
      "points": [
        {"lat": 30.90, "lng": 75.85, "label": "Warehouse"},
        {"lat": 30.91, "lng": 75.82, "label": "Customer A"},
        ...
      ]
    }
    First point is treated as the depot.
    """
    data = request.get_json(force=True, silent=True) or {}
    points = data.get("points", [])

    if len(points) < 2:
        return jsonify({"error": "Provide at least 2 points (1 depot + 1 stop)."}), 400

    for p in points:
        if "lat" not in p or "lng" not in p:
            return jsonify({"error": "Each point needs 'lat' and 'lng'."}), 400

    result = optimize_route(points)
    return jsonify(result)


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
