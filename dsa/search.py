"""
dsa/search.py
Implements and compares Linear Search vs Dictionary Lookup
for finding transactions by ID.
"""

import time
import sys
import os

# Allow importing parse_xml from parent directory
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "etl"))
from parse_xml import parse_xml


# ── Algorithm 1: Linear Search ────────────────────────────────────────────────

def linear_search(transactions, target_id):
    """
    Scan every item in the list one by one until the target ID is found.
    Time complexity: O(n) — worst case checks every record.
    """
    for transaction in transactions:
        if transaction["id"] == target_id:
            return transaction
    return None


# ── Algorithm 2: Dictionary Lookup ───────────────────────────────────────────

def build_dict(transactions):
    """
    Build a dictionary mapping id → transaction for O(1) lookups.
    Time complexity to build: O(n) — done once.
    """
    return {txn["id"]: txn for txn in transactions}


def dict_lookup(transactions_dict, target_id):
    """
    Find a transaction by key in O(1) average time.
    Time complexity: O(1) — direct key access.
    """
    return transactions_dict.get(target_id)


# ── Benchmark ─────────────────────────────────────────────────────────────────

def benchmark(transactions, num_searches=100):
    """
    Run both search methods num_searches times and compare total time.
    Uses the last transaction ID as the worst case for linear search.
    """
    if not transactions:
        print("No transactions to benchmark.")
        return

    # Use the last ID — worst case for linear search (must scan entire list)
    target_id = transactions[-1]["id"]
    txn_dict  = build_dict(transactions)

    # ── Linear Search benchmark
    start = time.perf_counter()
    for _ in range(num_searches):
        linear_search(transactions, target_id)
    linear_time = time.perf_counter() - start

    # ── Dictionary Lookup benchmark
    start = time.perf_counter()
    for _ in range(num_searches):
        dict_lookup(txn_dict, target_id)
    dict_time = time.perf_counter() - start

    # ── Results
    print("\n" + "=" * 55)
    print("       DSA SEARCH COMPARISON RESULTS")
    print("=" * 55)
    print(f"  Dataset size       : {len(transactions)} transactions")
    print(f"  Search target ID   : {target_id} (last record = worst case)")
    print(f"  Repetitions        : {num_searches}")
    print("-" * 55)
    print(f"  Linear Search time : {linear_time:.6f} seconds")
    print(f"  Dict Lookup time   : {dict_time:.6f} seconds")
    print(f"  Speedup factor     : {linear_time / dict_time:.1f}x faster")
    print("=" * 55)

    print("""
REFLECTION
----------
Linear search scans every record from index 0 until it finds
the target. For a list of n records the worst case requires n
comparisons → O(n) time complexity.

Dictionary lookup uses a hash table internally. Python computes
a hash of the key and jumps directly to the right memory slot,
giving O(1) average time regardless of how large the dataset grows.

For 20+ records the difference is already measurable. At
thousands of MoMo records it becomes critical for API response
times.

Other data structures that could further improve efficiency:
  • B-Tree index (used by relational databases like SQLite/MySQL)
    — O(log n) lookup, excellent for range queries like date filters.
  • Binary Search on a sorted list — O(log n), no extra memory
    but requires the list to stay sorted after every insert.
  • Trie — useful if searching by phone number prefix.
""")

    return {
        "dataset_size":  len(transactions),
        "target_id":     target_id,
        "repetitions":   num_searches,
        "linear_time_s": round(linear_time, 6),
        "dict_time_s":   round(dict_time, 6),
        "speedup":       round(linear_time / dict_time, 1),
    }


# ── CLI entrypoint ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    xml_path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/modified_sms_v2.xml"

    print(f"Loading transactions from: {xml_path}")
    transactions, _ = parse_xml(xml_path)

    # Ensure at least 20 records for the assignment requirement
    if len(transactions) < 20:
        print(f"Warning: only {len(transactions)} transactions found. "
              "Assignment requires at least 20.")

    benchmark(transactions, num_searches=100)
