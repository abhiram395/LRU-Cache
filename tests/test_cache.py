import unittest

import app as app_module
from lrucache import LRUCache


class CachePolicyTests(unittest.TestCase):
    def put_many(self, cache, keys):
        for key in keys:
            cache.put(key, key * 100)

    def test_lru_evicts_least_recently_used_key(self):
        cache = LRUCache(3, "LRU")
        self.put_many(cache, [1, 2, 3])

        cache.get(1)
        result = cache.put(4, 400)

        self.assertEqual(result["evicted"]["key"], 2)
        self.assertEqual([item["key"] for item in cache.get_items()], [4, 1, 3])

    def test_fifo_evicts_oldest_inserted_key(self):
        cache = LRUCache(3, "FIFO")
        self.put_many(cache, [1, 2, 3])

        cache.get(1)
        result = cache.put(4, 400)

        self.assertEqual(result["evicted"]["key"], 1)
        self.assertEqual([item["key"] for item in cache.get_items()], [4, 3, 2])

    def test_lfu_evicts_least_frequently_used_key(self):
        cache = LRUCache(3, "LFU")
        self.put_many(cache, [1, 2, 3])

        cache.get(1)
        cache.get(1)
        cache.get(2)
        result = cache.put(4, 400)

        self.assertEqual(result["evicted"]["key"], 3)
        self.assertEqual([item["key"] for item in cache.get_items()], [1, 2, 4])

    def test_mru_evicts_most_recently_used_key(self):
        cache = LRUCache(3, "MRU")
        self.put_many(cache, [1, 2, 3])

        cache.get(1)
        result = cache.put(4, 400)

        self.assertEqual(result["evicted"]["key"], 1)
        self.assertEqual([item["key"] for item in cache.get_items()], [2, 3, 4])

    def test_capacity_resize_uses_active_policy(self):
        cache = LRUCache(4, "FIFO")
        self.put_many(cache, [1, 2, 3, 4])

        evicted = cache.set_capacity(2)

        self.assertEqual([item["key"] for item in evicted], [1, 2])
        self.assertEqual(cache.capacity, 2)
        self.assertEqual([item["key"] for item in cache.get_items()], [4, 3])


class FlaskRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()
        self.client.post("/reset", json={"capacity": 3, "policy": "LRU"})

    def test_put_get_and_state_routes(self):
        put_response = self.client.post("/put", json={"key": 1, "value": 100})
        get_response = self.client.get("/get/1")
        state_response = self.client.get("/state")

        self.assertEqual(put_response.status_code, 200)
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json["value"], 100)
        self.assertEqual(state_response.json["size"], 1)
        self.assertEqual(state_response.json["policy"]["code"], "LRU")

    def test_policy_route_changes_active_policy(self):
        response = self.client.post("/policy", json={"policy": "LFU"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["snapshot"]["policy"]["code"], "LFU")

    def test_recommend_policy_route(self):
        response = self.client.post(
            "/recommend-policy",
            json={
                "workload": "batch sequential scan newest not reused",
                "priority": "scan-heavy",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["recommended"]["code"], "MRU")


if __name__ == "__main__":
    unittest.main()
