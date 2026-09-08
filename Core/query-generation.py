import os
import sys
import json
import warnings
import logging

warnings.filterwarnings("ignore")
logging.getLogger().setLevel(logging.ERROR)
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"

from dotenv import load_dotenv
from google import genai

load_dotenv()

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.abspath(os.path.join(CURRENT_DIR, "../query_cache.json"))
JSON_RESUME_FILE = os.path.abspath(os.path.join(CURRENT_DIR, "temp_organized_resume.json"))

def get_skills_from_json() -> str:
    """Reads the skills section directly from temp_organized_resume.json."""
    if not os.path.exists(JSON_RESUME_FILE):
        raise FileNotFoundError(f"[!] Could not find {JSON_RESUME_FILE}. Please run vlm.py first.")
    
    with open(JSON_RESUME_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    skills_data = data.get("skills", {})
    return json.dumps(skills_data, indent=2)

def generate_search_queries() -> list[str]:
    skills_json_str = get_skills_from_json()
    client = genai.Client()
    
    prompt = f"""
You are an expert technical recruiter and Boolean search architect. 
Analyze the candidate's skills JSON object provided below:

Skills JSON:
{skills_json_str}

Your task is to generate EXACTLY 3 short, punchy, and highly popular job search queries using Boolean operators (AND, OR) and parentheses. 
Keep them concise—use only the top 3-4 most popular industry keywords per query:

- Query 1: Short **Full Stack** query (e.g., combining Full Stack with React/Next.js and Node).
- Query 2: Short **Frontend / Mobile** query (e.g., React, Next.js, or React Native).
- Query 3: Short **Backend / API / DB** query (e.g., Node, Express, Python, or Database).

STRICT FORMATTING RULES:
1. Return ONLY the 3 search queries separated by newlines.
2. No extra text, bullet points, numbers, explanations, or markdown code blocks.
3. Keep each query short, concise, and focused strictly on top market keywords.
"""

    print("[*] Generating short, market-optimized search queries with Gemini 3.5 Flash-Lite...")
    response = client.models.generate_content(
        model='gemini-3.5-flash-lite',
        contents=prompt
    )
    
    queries = [q.strip() for q in response.text.split("\n") if q.strip()][:3]
    
    # Store queries in structured JSON format inside temporary storage
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    structured_cache = {
        "source": "temp_organized_resume.json -> skills (short & popular)",
        "queries": queries
    }
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(structured_cache, f, indent=4, ensure_ascii=False)
        
    return queries

if __name__ == "__main__":
    # Clear out old cache so it immediately recalculates with the shorter format
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
        
    queries = generate_search_queries()
    for i, q in enumerate(queries):
        print(f"Query {i+1}: {q}")