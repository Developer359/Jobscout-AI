import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import os
import sys
import re
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Add project root to path so it can successfully import from the Data folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Data.chroma_store import store_cv_in_chroma

# 2. Raw Text Extraction (pypdf)
def extract_raw_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    raw_text = "\n\n".join([page.extract_text() or "" for page in reader.pages])
    return re.sub(r'\n+', '\n', raw_text).strip()

# 3. LangChain Chunking Layer (No LLM)
def chunk_cv_data(raw_text: str) -> list[str]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " "]
    )
    return text_splitter.split_text(raw_text)

if __name__ == "__main__":
    # FIX: Dynamically target resume.pdf inside the same 'Core' directory as this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_file_path = os.path.join(current_dir, "resume.pdf")
    
    print("[*] Extracting raw text from PDF...")
    raw_text = extract_raw_text(pdf_file_path)
    
    print("[*] Chunking text using LangChain (No LLM)...")
    chunks = chunk_cv_data(raw_text)
    
    print(f"\n--- LangChain Chunks Output ({len(chunks)} chunks generated) ---")
    for i, chunk in enumerate(chunks[:3]):  # Preview first few chunks
        print(f"\n[Chunk {i+1}]:\n{chunk[:150]}...")
    
    # Store text chunks into ChromaDB
    print("\n[*] Storing text chunks into ChromaDB...")
    store_cv_in_chroma(chunks)
