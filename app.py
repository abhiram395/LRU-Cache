import os

from flask import Flask, request, jsonify, render_template
from lrucache import LRUCache

app = Flask(__name__)

# Initialize cache
cache = LRUCache(3)


# ---------------- PUT ----------------
# from flask import render_template

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/put', methods=['POST'])
def put():
    data = request.json
    key = data.get("key")
    value = data.get("value")

    cache.put(key, value)

    return jsonify({"message": "Inserted/Updated"})


# ---------------- GET ----------------
@app.route('/get/<int:key>', methods=['GET'])
def get(key):
    value = cache.get(key)

    if value == -1:
        return jsonify({"message": "Key not found"}), 404

    return jsonify({"key": key, "value": value})


# ---------------- VIEW CACHE ----------------
@app.route('/cache', methods=['GET'])
def view_cache():
    return jsonify(cache.getCacheState())

@app.route('/reset')
def reset():
    global cache
    cache = LRUCache(3)
    return "reset done"

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
