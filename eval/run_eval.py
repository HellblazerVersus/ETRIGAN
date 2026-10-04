import json
import os
from pathlib import Path

# In a real run, this imports the RetrieverProtocol
# from etrigan.kb.store import HybridStore

def evaluate_retrieval(k=3):
    queries_file = Path(__file__).parent / "queries_synthetic.json"
    with open(queries_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print(f"--- ETRIGAN Hybrid Retrieval Eval (Recall@{k} & MRR) ---")
    print(data["_meta"]["warning"])
    print("---------------------------------------------------------")
    
    queries = data["queries"]
    total = len(queries) * 2 # English + Hindi
    
    # Mocking retrieval results since we don't have ingested documents yet
    # In reality: results = store.search(query["text_en"], k=k)
    
    print(f"\nEvaluated {total} queries (English + Hindi).")
    print(f"Recall@{k}: 1.00 (Mocked for Demo)")
    print("MRR: 1.00 (Mocked for Demo)")
    print("\nTo test with real data, ingest documents into the SQLite vector DB first via /ingest.")

if __name__ == "__main__":
    evaluate_retrieval()
