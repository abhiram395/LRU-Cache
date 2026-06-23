# LRU Cache Visualizer

An interactive Flask web app for learning how cache eviction policies work. The app visualizes cache state, shows operation steps, tracks hits/misses/evictions, recommends a policy for a workload, and exports the operation history as JSON.

## Features

- Capacity-first setup flow so users choose cache size before running operations.
- Interactive `GET` and `PUT` operations.
- Four cache policies:
  - `LRU` - Least Recently Used
  - `FIFO` - First In First Out
  - `LFU` - Least Frequently Used
  - `MRU` - Most Recently Used
- Local AI-style policy advisor that recommends a policy from workload hints.
- Step mode for revealing operation steps one by one.
- Hash map panel, cache lane visualization, stats, and operation history.
- JSON export for operation history.
- REST endpoints for cache state, policy changes, recommendations, and operations.

## Why This Project Exists

Caching is a common systems and interview topic. A cache needs fast lookup and a clear eviction rule when capacity is full.

For classic LRU, the common design is:

- Hash map for `O(1)` key lookup.
- Doubly linked list or ordered state for keeping usage order.
- Evict from the least-recent side when capacity is full.

This project extends that idea to multiple cache policies so users can see how different workloads need different strategies.

## Supported Policies

| Policy | Evicts | Best For |
| --- | --- | --- |
| LRU | Least recently used key | General-purpose app/session/API caches |
| FIFO | Oldest inserted key | Simple queues, streams, insertion-order workloads |
| LFU | Least frequently used key | Hot-key workloads where the same items repeat often |
| MRU | Most recently used key | Sequential scans where the newest item is unlikely to be reused |

## Local AI Advisor

The advisor is intentionally local and deterministic. It does not call an external AI API or send user data anywhere.

It scores the workload text and priority against common cache-policy patterns:

- repeated/popular/hot keys -> `LFU`
- recent/session/API/general usage -> `LRU`
- queue/stream/insertion order -> `FIFO`
- scan/batch/sequential usage -> `MRU`

This keeps the project easy to run while still giving users intelligent guidance.

## Run Locally

```bash
pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Run Checks

```bash
python - <<'PY'
import ast
from pathlib import Path

for path in [Path("app.py"), Path("lrucache.py"), *Path("tests").glob("*.py")]:
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

print("Python syntax OK")
PY
python -m unittest discover -s tests -v
```

The GitHub Actions workflow in `.github/workflows/ci.yml` runs these checks automatically on every push and pull request. It also verifies that the JavaScript inside `templates/index.html` parses successfully.

## API Routes

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/` | Render the visualizer |
| `POST` | `/reset` | Reset cache with capacity and policy |
| `POST` | `/put` | Insert or update a key/value pair |
| `GET` | `/get/<key>` | Read a key and update policy state |
| `GET` | `/state` | Return full visualization state |
| `GET` | `/cache` | Return legacy cache state |
| `POST` | `/capacity` | Change capacity |
| `GET` | `/policies` | List supported policies |
| `POST` | `/policy` | Change active policy |
| `POST` | `/recommend-policy` | Recommend a policy from workload hints |

## Example Flow

1. Set capacity to `3`.
2. Choose policy `LRU`.
3. Run `PUT(1, 100)`, `PUT(2, 200)`, `PUT(3, 300)`.
4. Run `GET(1)`.
5. Run `PUT(4, 400)`.

For LRU, key `2` is evicted because it became the least recently used key.

## Tech Stack

- Python
- Flask
- HTML
- CSS
- Vanilla JavaScript

## Project Ideas To Extend Later

- Add pytest test coverage for every policy.
- Add OpenAPI/Swagger documentation for the REST API.
- Add GitHub Actions CI for automated syntax checks and tests.
- Add Docker for one-command deployment.
- Add optional external LLM integration for richer natural-language policy recommendations.
