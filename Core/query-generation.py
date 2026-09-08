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

def generate_search_queries() -> dict:
    skills_json_str = get_skills_from_json()
    client = genai.Client()
    
    prompt = f"""
You are an expert technical recruiter and Boolean search architect. 
Analyze the candidate's skills JSON object provided below:

Skills JSON:
{skills_json_str}

Your task is to generate EXACTLY 3 job search queries using Boolean operators (AND, OR) and parentheses. 
Because the candidate is at a junior/entry level, you MUST explicitly include target job seniority keywords (such as "Junior", "Entry-Level", or "Associate") in the queries so that job boards filter out senior or advanced roles automatically during search.

Return your response strictly as a valid JSON object with a single key "queries" containing a list of 3 objects. Each object must have:
- "query": The Boolean search string containing seniority level and skills.
- "job_type": The seniority level intended for that query (e.g., "Junior", "Entry-Level", "Intermediate").

Example format:
{{
  "queries": [
    {{
      "query": "(\"Junior Developer\" OR \"Junior Engineer\") AND (\"React\" OR \"Next.js\") AND (\"Node\")",
      "job_type": "Junior"
    }}
  ]
}}

Return ONLY valid JSON. No markdown code blocks, no extra conversational text.
"""

    print("[*] Generating seniority-filtered search queries with Gemini 3.5 Flash-Lite...")
    response = client.models.generate_content(
        model='gemini-3.5-flash-lite',
        contents=prompt
    )
    
    raw_response = response.text.strip()
    # Clean markdown code blocks if Gemini adds them
    clean_json_str = raw_response.replace("```json", "").replace("```", "").strip()
    
    try:
        data = json.loads(clean_json_str)
    except json.JSONDecodeError:
        # Fallback dictionary if formatting fails slightly
        data = {
            "source": "temp_organized_resume.json -> skills (seniority-targeted)",
            "queries": [
                {"query": "(\"Junior Developer\" OR \"Entry-Level\") AND (\"React\" OR \"Next.js\") AND (\"Node\")", "job_type": "Junior"},
                {"query": "(\"Junior Frontend Developer\") AND (\"React Native\" OR \"Tailwind\") AND (\"JavaScript\")", "job_type": "Junior"},
                {"query": "(\"Junior Backend Developer\" OR \"Associate\") AND (\"Node.js\" OR \"Python\") AND (\"Express\")", "job_type": "Junior"}
            ]
        }

    # Ensure structured cache format
    if "source" not in data:
        data["source"] = "temp_organized_resume.json -> skills (seniority-targeted)"

    # Store structured queries and job types in query_cache.json
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    return data

if __name__ == "__main__":
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
        
    result = generate_search_queries()
    for i, item in enumerate(result.get("queries", [])):
        print(f"Query {i+1} [{item.get('job_type')}]: {item.get('query')}")