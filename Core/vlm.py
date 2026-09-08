import os
import sys
import json
import re
import warnings
warnings.filterwarnings("ignore")

# Load variables from the .env file in the root directory
from dotenv import load_dotenv
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))

from google import genai

# 1. Import extraction and chunking directly from parser.py
from parser import extract_raw_text, chunk_cv_data

# 2. Add project root for Chroma DB store
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Data.chroma_store import store_cv_in_chroma


def organize_with_gemini(chunks: list[str]) -> dict:
    """Uses Google Gemini Flash to read chunks and structure them into clean multi-line JSON."""
    combined_text = "\n\n".join(chunks)

    print("[*] Initializing Google GenAI client...")
    client = genai.Client() # Now automatically finds GEMINI_API_KEY from the loaded .env file

    prompt = f"""
    You are an expert data extractor and resume parser. Read the resume text below carefully and extract the real applicant data into a strict JSON object.
    You must categorize the information into these EXACT keys: 
    "personal_info", "skills", "projects", "about_me", and "internships_and_experience".
    
    Do not use placeholder terms. Extract the actual real details present in the text.
    Return ONLY valid JSON. Do not include markdown code block formatting like ```json or any extra conversational text.

    Resume Text:
    {combined_text}
    """

    print("[*] Sending text to Gemini Flash for clean organization...")
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )

    raw_response = response.text.strip()

    # Clean markdown code blocks if Gemini includes them
    clean_json_str = re.sub(r'```(?:json)?\s*([\s\S]*?)\s*```', r'\1', raw_response).strip()

    try:
        return json.loads(clean_json_str)
    except json.JSONDecodeError:
        print("[!] Warning: Response was not clean JSON. Trying fallback extraction.")
        match = re.search(r'\{.*\}', clean_json_str, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
        return {"raw_extraction": clean_json_str}


def convert_json_to_chroma_chunks(json_data: dict) -> list[str]:
    """Converts structured JSON into readable, sectioned text chunks for ChromaDB."""
    chroma_chunks = []
    for section, content in json_data.items():
        chunk_str = f"--- SECTION: {section.upper().replace('_', ' ')} ---\n"
        if isinstance(content, (dict, list)):
            chunk_str += json.dumps(content, indent=2)
        else:
            chunk_str += str(content)
        chroma_chunks.append(chunk_str)

    return chroma_chunks


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_file_path = os.path.join(current_dir, "resume.pdf")
    temp_json_path = os.path.join(current_dir, "temp_organized_resume.json")

    print("[*] Running parser.py logic...")
    raw_text = extract_raw_text(pdf_file_path)
    raw_chunks = chunk_cv_data(raw_text)

    # Structure data using Gemini Flash
    structured_json = organize_with_gemini(raw_chunks)

    print(f"[*] Saving structured data to temporary JSON: {temp_json_path}")
    with open(temp_json_path, "w", encoding="utf-8") as f:
        json.dump(structured_json, f, indent=4, ensure_ascii=False)

    # Convert structured sections for vector search
    chroma_ready_chunks = convert_json_to_chroma_chunks(structured_json)

    print("\n--- Organized Chroma Chunk Preview ---")
    if chroma_ready_chunks:
        print(chroma_ready_chunks[0][:200] + "...\n")

    print("[*] Storing organized chunks into ChromaDB...")
    store_cv_in_chroma(chroma_ready_chunks)
    print("[✓] Process complete!")