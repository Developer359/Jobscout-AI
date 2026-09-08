import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import os
import sys
import re
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Add project root to path so it can successfully import from the Data folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Data.chroma_store import store_cv_in_chroma

# 2. Raw Text Extraction (PyMuPDF)
def extract_raw_text(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    raw_text = ""
    for page in doc:
        # get_text("text") extracts text preserving logical reading order
        raw_text += page.get_text("text") + "\n\n"
    doc.close()
    
    # Clean up excess newlines
    return re.sub(r'\n{3,}', '\n\n', raw_text).strip()

# 3. Extract Only the Skills Section
def extract_skills_chunk(raw_text: str) -> str:
    pattern = r"(?i)(?:technical skills|skills|core competencies|expertise)[:\s]*\n(.*?)(?=\n[A-Z][A-Z\s]{3,}\n|\Z)"
    match = re.search(pattern, raw_text, re.DOTALL)
    
    if match:
        skills_text = match.group(0).strip()
        return f"[Dedicated Skills Section]\n{skills_text}"
    return ""

# 4. LangChain Chunking Layer (No LLM)
def chunk_cv_data(raw_text: str) -> list[str]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " "]
    )
    
    general_chunks = text_splitter.split_text(raw_text)
    skills_chunk = extract_skills_chunk(raw_text)
    
    final_chunks = []
    if skills_chunk:
        final_chunks.append(skills_chunk)
        
    final_chunks.extend(general_chunks)
    return final_chunks

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_file_path = os.path.join(current_dir, "resume.pdf")
    
    print("[*] Extracting raw text from PDF using PyMuPDF...")
    raw_text = extract_raw_text(pdf_file_path)
    
    print("[*] Chunking text and isolating Skills section...")
    chunks = chunk_cv_data(raw_text)
    
    print(f"\n--- Output ({len(chunks)} total chunks generated) ---")
    if chunks:
        print(f"[First Chunk Preview]:\n{chunks[0][:150]}...\n")
    
    # Store text chunks into ChromaDB
    print("[*] Storing text chunks into ChromaDB...")
    store_cv_in_chroma(chunks)