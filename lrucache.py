POLICY_DETAILS = {
    "LRU": {
        "name": "Least Recently Used",
        "display": "Most recent -> least recent",
        "evicts": "least recently used key",
        "best_for": "General-purpose caches where recently used data is likely to be used again.",
    },
    "FIFO": {
        "name": "First In First Out",
        "display": "Newest -> oldest",
        "evicts": "oldest inserted key",
        "best_for": "Simple queues or streams where insertion age matters more than access frequency.",
    },
    "LFU": {
        "name": "Least Frequently Used",
        "display": "Most frequent -> least frequent",
        "evicts": "least frequently used key, then oldest among ties",
        "best_for": "Workloads where a small group of hot keys is repeatedly requested.",
    },
    "MRU": {
        "name": "Most Recently Used",
        "display": "Least recent -> most recent",
        "evicts": "most recently used key",
        "best_for": "Scan-heavy workloads where the newest item is least likely to be reused soon.",
    },
}


class LRUCache:
    def __init__(self, capacity, policy="LRU"):
        self.capacity = max(1, int(capacity))
        self.policy = self.normalize_policy(policy)
        self.cache = {}
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.operations = 0
        self.clock = 0

    @staticmethod
    def normalize_policy(policy):
        normalized = str(policy or "LRU").upper()
        return normalized if normalized in POLICY_DETAILS else "LRU"

    def policy_info(self):
        info = POLICY_DETAILS[self.policy].copy()
        info["code"] = self.policy
        return info

    def _touch(self, entry):
        self.clock += 1
        entry["last_access"] = self.clock
        entry["frequency"] += 1

    def _new_entry(self, key, value):
        self.clock += 1
        return {
            "key": key,
            "value": value,
            "frequency": 1,
            "inserted_at": self.clock,
            "last_access": self.clock,
        }

    def _eviction_key(self):
        if self.policy == "LRU":
            return min(self.cache, key=lambda item_key: self.cache[item_key]["last_access"])

        if self.policy == "MRU":
            return max(self.cache, key=lambda item_key: self.cache[item_key]["last_access"])

        if self.policy == "FIFO":
            return min(self.cache, key=lambda item_key: self.cache[item_key]["inserted_at"])

        return min(
            self.cache,
            key=lambda item_key: (
                self.cache[item_key]["frequency"],
                self.cache[item_key]["inserted_at"],
            ),
        )

    def _evict_one(self):
        evict_key = self._eviction_key()
        evicted_entry = self.cache.pop(evict_key)
        self.evictions += 1
        return {"key": evicted_entry["key"], "value": evicted_entry["value"]}

    def _display_keys(self):
        if self.policy == "LRU":
            return sorted(self.cache, key=lambda item_key: self.cache[item_key]["last_access"], reverse=True)

        if self.policy == "MRU":
            return sorted(self.cache, key=lambda item_key: self.cache[item_key]["last_access"])

        if self.policy == "FIFO":
            return sorted(self.cache, key=lambda item_key: self.cache[item_key]["inserted_at"], reverse=True)

        return sorted(
            self.cache,
            key=lambda item_key: (
                self.cache[item_key]["frequency"],
                self.cache[item_key]["last_access"],
            ),
            reverse=True,
        )

    def _movement_text(self):
        if self.policy == "LRU":
            return "Accessed keys move to the most-recent side."
        if self.policy == "MRU":
            return "Accessed keys move to the most-recent eviction side."
        if self.policy == "FIFO":
            return "Accesses do not change insertion order."
        return "Accessed keys gain frequency and move toward the protected side."

    # ---------------- CORE OPERATIONS ----------------
    def get(self, key):
        self.operations += 1

        if key not in self.cache:
            self.misses += 1
            return -1

        self.hits += 1
        entry = self.cache[key]
        self._touch(entry)
        return entry["value"]

    def put(self, key, value):
        self.operations += 1
        evicted = None

        if key in self.cache:
            entry = self.cache[key]
            entry["value"] = value
            self._touch(entry)
            return {"updated": True, "evicted": None}

        if len(self.cache) == self.capacity:
            evicted = self._evict_one()

        self.cache[key] = self._new_entry(key, value)
        return {"updated": False, "evicted": evicted}

    def set_capacity(self, capacity):
        self.capacity = max(1, int(capacity))
        evicted = []

        while len(self.cache) > self.capacity:
            evicted.append(self._evict_one())

        return evicted

    def set_policy(self, policy):
        self.policy = self.normalize_policy(policy)

    # ---------------- DEBUG / VISUALIZATION ----------------
    def getCacheState(self):
        return [{entry["key"]: entry["value"]} for entry in self.get_items()]

    def get_items(self):
        items = []
        keys = self._display_keys()
        eviction_key = self._eviction_key() if self.cache else None

        for index, key in enumerate(keys, start=1):
            entry = self.cache[key]
            items.append(
                {
                    "key": entry["key"],
                    "value": entry["value"],
                    "frequency": entry["frequency"],
                    "position": index,
                    "insertedAt": entry["inserted_at"],
                    "lastAccess": entry["last_access"],
                    "isMostRecent": self.policy == "LRU" and index == 1,
                    "isLeastRecent": self.policy == "LRU" and key == eviction_key,
                    "isEvictionCandidate": key == eviction_key,
                    "isProtected": index == 1,
                }
            )

        return items

    def get_stats(self):
        total_reads = self.hits + self.misses
        hit_rate = round((self.hits / total_reads) * 100, 1) if total_reads else 0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "operations": self.operations,
            "hitRate": hit_rate,
        }

    def get_visual_labels(self):
        return {
            "left": "Protected",
            "right": "Evicted first",
            "order": POLICY_DETAILS[self.policy]["display"],
            "movement": self._movement_text(),
            "evictionRule": POLICY_DETAILS[self.policy]["evicts"],
        }
