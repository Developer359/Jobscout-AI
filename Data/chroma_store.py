import os
import hashlib
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

def store_cv_in_chroma(chunks: list[str]):
    print("[*] Initializing HuggingFace Embeddings...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    persist_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "chroma_db"))
    
    # 1. Connect to the existing vector store (preserves old data)
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
        collection_name="candidate_cv"
    )
    
    # 2. Fetch existing documents from ChromaDB to check for duplicates
    existing_data = vectorstore.get()
    existing_documents = set(existing_data["documents"]) if existing_data and "documents" in existing_data else set()
    
    # 3. Filter out chunks that already exist in the database
    new_chunks = []
    new_ids = []
    
    for chunk in chunks:
        # Generate a unique hash ID for the chunk
        chunk_id = hashlib.md5(chunk.encode('utf-8')).hexdigest()
        
        # Check if this exact text content is already stored
        if chunk not in existing_documents:
            new_chunks.append(chunk)
            new_ids.append(chunk_id)
            # Add to set locally to catch duplicates within the current run batch too
            existing_documents.add(chunk)

    # 4. Add only the brand-new, unique chunks if any exist
    if new_chunks:
        print(f"[*] Adding {len(new_chunks)} new unique chunks (skipped duplicates)...")
        vectorstore.add_texts(texts=new_chunks, ids=new_ids)
        print(f"[✓] Successfully updated ChromaDB with new data!")
    else:
        print("[!] No new unique data found. All chunks already exist in ChromaDB.")
        
    return vectorstore