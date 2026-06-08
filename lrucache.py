class Node:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}

        self.head = Node(0, 0)
        self.tail = Node(0, 0)

        self.head.next = self.tail
        self.tail.prev = self.head

    # ---------------- DLL OPERATIONS ----------------
    def addNode(self, node):
        node.next = self.head.next
        node.prev = self.head

        self.head.next.prev = node
        self.head.next = node

    def deleteNode(self, node):
        prev = node.prev
        nxt = node.next

        prev.next = nxt
        nxt.prev = prev

    # ---------------- CORE OPERATIONS ----------------
    def get(self, key):
        if key not in self.cache:
            return -1

        node = self.cache[key]

        self.deleteNode(node)
        self.addNode(node)

        return node.value

    def put(self, key, value):
        if key in self.cache:
            node = self.cache[key]

            self.deleteNode(node)
            node.value = value
            self.addNode(node)

        else:
            if len(self.cache) == self.capacity:
                lru = self.tail.prev
                self.deleteNode(lru)
                del self.cache[lru.key]

            newNode = Node(key, value)
            self.cache[key] = newNode
            self.addNode(newNode)

    # ---------------- DEBUG ----------------
    def getCacheState(self):
        res = []
        curr = self.head.next
        while curr != self.tail:
            res.append({curr.key: curr.value})
            curr = curr.next
        return res