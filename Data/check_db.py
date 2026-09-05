import os
import chromadb

# Point directly to the Data/chroma_db folder where it is actually saved
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "chroma_db"))

# If your parser saved it in the root or Data folder instead, adjust path above.
# Let's initialize the persistent client
client = chromadb.PersistentClient(path=db_path)

try:
    collection = client.get_collection(name="candidate_cv")
    results = collection.get()
    
    print(f"[*] Total Records Stored: {len(results['ids'])}")
    print("\n--- Stored Documents & Metadatas ---")
    for i, doc in enumerate(results['documents']):
        print(f"\n[Record {i+1}]:\n{doc}")
except Exception as e:
    print(f"[!] Could not find collection: {e}")
    print("Make sure you ran Core/parser.py first so the database is populated.")