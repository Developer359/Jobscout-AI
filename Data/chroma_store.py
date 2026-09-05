import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

def store_cv_in_chroma(chunks: list[str]):
    print("[*] Initializing HuggingFace Embeddings...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    persist_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "chroma_db"))
    
    print("[*] Storing text chunks into ChromaDB...")
    # Create or update the vector store directly from the text chunks
    vectorstore = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        persist_directory=persist_directory,
        collection_name="candidate_cv"
    )
    
    print(f"[✓] Successfully stored {len(chunks)} text chunks into ChromaDB!")
    return vectorstore