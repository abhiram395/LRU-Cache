#include <bits/stdc++.h>
using namespace std;
class Node
{
public:
    int key, value;
    Node *prev;
    Node *next;
};
class LRUCache
{
private:
    int capacity;

    unordered_map<int, Node *> cache;
public:
    // key → node

    // DLL
    Node *head;
    Node *tail;
    LRUCache(int cap)
    {
        capacity = cap;

        head = new Node();
        tail = new Node();
        head->prev = NULL;
        tail->next = NULL;
        head->next = tail;
        tail->prev = head;
    }
    void addNode(Node *node)
    {
        node->next = head->next;
        node->prev = head;

        head->next->prev = node;
        head->next = node;

    } // add right after head
    void deleteNode(Node *node)
    {
        Node *pre = node->prev;
        Node *nex = node->next;
        pre->next = nex;
        nex->prev = pre;
        // delete node;
    } // remove node

public:
    int get(int key)
    {
        if (cache.find(key) == cache.end())
            return -1;

        Node *node = cache[key];

        deleteNode(node); // remove from old position
        addNode(node);    // move to front

        return node->value;
    }
    void put(int key, int value)
    {   if (capacity == 0) return;
        if (cache.find(key) != cache.end())
        {
            Node *node = cache[key];
            deleteNode(node);
            node->value = value;
            addNode(node);
        }
        else
        {
            if (cache.size() == capacity)
            {
                Node *lru = tail->prev;

                deleteNode(lru);
                cache.erase(lru->key);
                delete lru;
            }

            Node *node = new Node();
            node->key = key;
            node->value = value;

            cache[key] = node;
            addNode(node);
        }
    }
};