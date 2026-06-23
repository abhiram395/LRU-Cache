import os

from flask import Flask, request, jsonify, render_template
from lrucache import LRUCache, POLICY_DETAILS

app = Flask(__name__)

# Initialize cache
cache = LRUCache(3, "LRU")


def cache_snapshot():
    return {
        "capacity": cache.capacity,
        "size": len(cache.cache),
        "items": cache.get_items(),
        "legacy": cache.getCacheState(),
        "policy": cache.policy_info(),
        "policies": [{"code": code, **details} for code, details in POLICY_DETAILS.items()],
        "visualLabels": cache.get_visual_labels(),
        "stats": cache.get_stats(),
    }


def operation_steps(operation, key=None, value=None, found=False, evicted=None, updated=False):
    if operation == "put":
        steps = [f"PUT({key}, {value}) received."]
        if updated:
            steps.append("Key already existed, so its value was updated.")
            steps.append(cache.get_visual_labels()["movement"])
        else:
            steps.append("A new node was inserted into the cache.")
            if evicted:
                steps.append(f"Capacity was full, so key {evicted['key']} was evicted by the {cache.policy} rule.")
            else:
                steps.append("Capacity was available, so no eviction was needed.")
        return steps

    if operation == "get":
        steps = [f"GET({key}) received."]
        if found:
            steps.append("The key was found in the hash map.")
            steps.append(cache.get_visual_labels()["movement"])
        else:
            steps.append("The key was not present in the hash map.")
            steps.append("The cache order stayed the same.")
        return steps

    if operation == "capacity":
        steps = [f"Capacity changed to {value}."]
        if evicted:
            removed = ", ".join(str(item["key"]) for item in evicted)
            steps.append(f"Extra node(s) were evicted by the {cache.policy} rule: {removed}.")
        else:
            steps.append("All existing nodes still fit in the cache.")
        return steps

    if operation == "policy":
        return [
            f"Policy changed to {cache.policy}: {cache.policy_info()['name']}.",
            f"Eviction rule: remove the {cache.get_visual_labels()['evictionRule']}.",
            cache.get_visual_labels()["movement"],
        ]

    return ["Cache was reset to an empty state."]


def parse_int_field(data, field_name):
    raw_value = data.get(field_name)
    if raw_value is None or raw_value == "":
        raise ValueError(f"{field_name} is required")
    return int(raw_value)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/put', methods=['POST'])
def put():
    data = request.get_json(silent=True) or {}

    try:
        key = parse_int_field(data, "key")
        value = parse_int_field(data, "value")
    except (TypeError, ValueError):
        return jsonify({"message": "Key and value must be numbers"}), 400

    result = cache.put(key, value)
    evicted = result["evicted"]
    updated = result["updated"]

    if updated:
        message = f"Updated key {key} using {cache.policy}"
    elif evicted:
        message = f"Inserted key {key}; evicted key {evicted['key']} using {cache.policy}"
    else:
        message = f"Inserted key {key} using {cache.policy}"

    return jsonify(
        {
            "message": message,
            "operation": {
                "type": "put",
                "key": key,
                "value": value,
                "updated": updated,
                "evicted": evicted,
                "steps": operation_steps("put", key=key, value=value, evicted=evicted, updated=updated),
            },
            "snapshot": cache_snapshot(),
        }
    )


# ---------------- GET ----------------
@app.route('/get/<key>', methods=['GET'])
def get(key):
    try:
        key = int(key)
    except (TypeError, ValueError):
        return jsonify({"message": "Key must be a number"}), 400

    value = cache.get(key)

    if value == -1:
        return jsonify(
            {
                "message": f"Key {key} not found",
                "operation": {
                    "type": "get",
                    "key": key,
                    "found": False,
                    "steps": operation_steps("get", key=key, found=False),
                },
                "snapshot": cache_snapshot(),
            }
        ), 404

    return jsonify(
        {
            "key": key,
            "value": value,
            "message": f"Cache hit: key {key} has value {value}",
            "operation": {
                "type": "get",
                "key": key,
                "value": value,
                "found": True,
                "steps": operation_steps("get", key=key, found=True),
            },
            "snapshot": cache_snapshot(),
        }
    )


# ---------------- VIEW CACHE ----------------
@app.route('/cache', methods=['GET'])
def view_cache():
    return jsonify(cache.getCacheState())


@app.route('/state', methods=['GET'])
def state():
    return jsonify(cache_snapshot())


@app.route('/policies', methods=['GET'])
def policies():
    return jsonify({"policies": [{"code": code, **details} for code, details in POLICY_DETAILS.items()]})


@app.route('/policy', methods=['POST'])
def policy():
    data = request.get_json(silent=True) or {}
    selected_policy = data.get("policy", "LRU")
    cache.set_policy(selected_policy)

    return jsonify(
        {
            "message": f"Policy set to {cache.policy}",
            "operation": {
                "type": "policy",
                "policy": cache.policy_info(),
                "steps": operation_steps("policy"),
            },
            "snapshot": cache_snapshot(),
        }
    )


@app.route('/capacity', methods=['POST'])
def capacity():
    data = request.get_json(silent=True) or {}

    try:
        new_capacity = parse_int_field(data, "capacity")
    except (TypeError, ValueError):
        return jsonify({"message": "Capacity must be a number"}), 400

    evicted = cache.set_capacity(new_capacity)

    return jsonify(
        {
            "message": f"Capacity set to {cache.capacity}",
            "operation": {
                "type": "capacity",
                "capacity": cache.capacity,
                "evicted": evicted,
                "steps": operation_steps("capacity", value=cache.capacity, evicted=evicted),
            },
            "snapshot": cache_snapshot(),
        }
    )


@app.route('/reset', methods=['GET', 'POST'])
def reset():
    global cache
    data = request.get_json(silent=True) or {}
    capacity = data.get("capacity", cache.capacity)
    policy = data.get("policy", cache.policy)

    try:
        capacity = int(capacity)
    except (TypeError, ValueError):
        capacity = 3

    cache = LRUCache(capacity, policy)

    return jsonify(
        {
            "message": "Cache reset",
            "operation": {
                "type": "reset",
                "steps": operation_steps("reset"),
            },
            "snapshot": cache_snapshot(),
        }
    )


@app.route('/recommend-policy', methods=['POST'])
def recommend_policy():
    data = request.get_json(silent=True) or {}
    workload = str(data.get("workload", "")).lower()
    priority = str(data.get("priority", "")).lower()
    pattern = str(data.get("pattern", "")).lower()

    scores = {"LRU": 0, "FIFO": 0, "LFU": 0, "MRU": 0}
    reasons = []

    text = " ".join([workload, priority, pattern])

    if any(word in text for word in ["repeat", "frequent", "popular", "hot", "same"]):
        scores["LFU"] += 5
        reasons.append("Repeated or popular keys benefit from LFU because frequency matters.")

    if any(word in text for word in ["recent", "session", "page", "profile", "api", "general"]):
        scores["LRU"] += 3
        reasons.append("Recently used data is likely to be reused, which is the classic LRU fit.")

    if any(word in text for word in ["queue", "stream", "arrival", "simple", "order"]):
        scores["FIFO"] += 4
        reasons.append("Insertion order matters, so FIFO is simple and predictable.")

    if any(word in text for word in ["scan", "one-time", "batch", "sequential", "latest not reused"]):
        scores["MRU"] += 4
        reasons.append("Scan-heavy workloads may prefer MRU because the newest item may not be reused soon.")

    if "simplicity" in priority or "easy" in priority:
        scores["FIFO"] += 2
        reasons.append("FIFO has the simplest mental model.")

    if "hit" in priority or "performance" in priority:
        scores["LRU"] += 1
        scores["LFU"] += 1
        reasons.append("Hit-rate-focused workloads usually need recency or frequency awareness.")

    if not any(scores.values()):
        scores["LRU"] = 1
        reasons.append("When the workload is unclear, LRU is the safest general-purpose default.")

    recommended = max(scores, key=scores.get)

    return jsonify(
        {
            "recommended": {"code": recommended, **POLICY_DETAILS[recommended]},
            "scores": scores,
            "reasons": reasons,
            "note": "This is a local heuristic advisor, so it works without sending data to an external AI service.",
        }
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
