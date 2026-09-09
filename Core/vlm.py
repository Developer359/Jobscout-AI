import os
import sys
import json
import re
import time
import warnings
warnings.filterwarnings("ignore")

# Load variables from the .env file in the root directory
from dotenv import load_dotenv
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))

from google import genai
from google.genai.errors import ServerError

# 1. Import extraction and chunking directly from parser.py
from parser import extract_raw_text, chunk_cv_data

# 2. Add project root for Chroma DB store
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Data.chroma_store import store_cv_in_chroma


def organize_with_gemini(chunks: list[str]) -> dict:
    """Uses Google Gemini to read chunks, evaluate seniority level, and structure data into clean multi-line JSON with auto-retry."""
    combined_text = "\n\n".join(chunks)

    print("[*] Initializing Google GenAI client...")
    client = genai.Client()

    prompt = f"""You are an expert data extractor, resume parser, and technical recruiter. Read the resume text below carefully and extract the real applicant data into a strict JSON object.
You must categorize the information into these EXACT keys: 
"personal_info", "skills", "projects", "about_me", "internships_and_experience", and "seniority_level".

SPECIAL EVALUATION INSTRUCTION FOR "seniority_level":
- Deeply scan the full resume text for total years of experience, depth of technical implementation, architectural ownership, and leadership responsibilities.
- Accurately categorize the candidate's career level as one of: "Junior", "Intermediate", or "Senior" (you may also specify a precise leaning if applicable, e.g., "Junior-Intermediate" or "Mid-Senior"). 
- Provide a brief 1-2 sentence justification or key indicator inside this field alongside the level.

STRICT RULES:
1. Extract ONLY information explicitly present in the text below. 
2. Do NOT invent, assume, or add any data, skills, or experiences that are not written in the text.
3. If a section or data point is missing from the resume, leave its value as an empty string ("") or empty list ([]). Do not use placeholder terms.
4. Return ONLY valid JSON. Do not include markdown code block formatting like ```json or any extra conversational text.

Resume Text:
{combined_text}"""

    max_retries = 3
    delay = 3  # seconds

    for attempt in range(1, max_retries + 1):
        try:
            print(f"[*] Sending text to Gemini (Attempt {attempt}/{max_retries})...")
            response = client.models.generate_content(
                model='gemini-2.5-flash',  # Adjust model identifier if needed
                contents=prompt,
            )
            raw_response = response.text.strip()
            break
        except ServerError as e:
            if attempt == max_retries:
                print(f"[!] Server error persists after {max_retries} attempts.")
                raise e
            print(f"[!] Model experiencing high demand (503). Retrying in {delay} seconds...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff

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

    # Structure data and evaluate seniority using Gemini
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