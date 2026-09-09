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


def _load_resume_json() -> dict:
    """Loads the full temp_organized_resume.json file once."""
    if not os.path.exists(JSON_RESUME_FILE):
        raise FileNotFoundError(f"[!] Could not find {JSON_RESUME_FILE}. Please run vlm.py first.")

    with open(JSON_RESUME_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_skills_from_json(resume_data: dict) -> str:
    """Extracts the skills section from the already-loaded resume JSON."""
    skills_data = resume_data.get("skills", {})
    return json.dumps(skills_data, indent=2)


def get_seniority_from_json(resume_data: dict) -> tuple[str, str]:
    """
    Reads the 'seniority_level' field (the last key written by vlm.py) and
    normalizes it into one of: 'Junior', 'Mid-Level', 'Senior'.

    Returns:
        (normalized_level, raw_reason_text)
    """
    raw_text = resume_data.get("seniority_level", "").strip()

    if not raw_text:
        print("[!] No 'seniority_level' field found in resume JSON. Defaulting to 'Junior'.")
        return "Junior", "Not specified in resume JSON."

    raw_lower = raw_text.lower()

    if "senior" in raw_lower or "staff" in raw_lower or "lead" in raw_lower:
        level = "Senior"
    elif "mid" in raw_lower or "intermediate" in raw_lower:
        level = "Mid-Level"
    elif "entry" in raw_lower or "junior" in raw_lower:
        level = "Junior"
    else:
        # Unrecognized phrasing -> safest default so we don't over/under-shoot
        level = "Junior"

    return level, raw_text


# Seniority-specific instructions injected into the Gemini prompt so the
# generated Boolean queries target the ACTUAL detected level, not a
# hardcoded one.
SENIORITY_PROMPT_RULES = {
    "Junior": (
        'The candidate is at a JUNIOR / ENTRY-LEVEL. You MUST explicitly include target '
        'job seniority keywords (such as "Junior", "Entry-Level", or "Associate") in the '
        'queries so that job boards filter out senior or advanced roles automatically during search.'
    ),
    "Mid-Level": (
        'The candidate is at a MID-LEVEL / INTERMEDIATE level. You MUST explicitly include '
        'target job seniority keywords (such as "Mid-Level", "Intermediate", or "II") in the '
        'queries so that job boards filter out both entry-level/junior roles and senior/staff '
        'roles automatically during search.'
    ),
    "Senior": (
        'The candidate is at a SENIOR level. You MUST explicitly include target job seniority '
        'keywords (such as "Senior", "Lead", or "Staff") in the queries so that job boards '
        'filter out junior or entry-level roles automatically during search.'
    ),
}

# Fallback query sets per seniority level, used only if Gemini's JSON response
# fails to parse.
FALLBACK_QUERIES = {
    "Junior": [
        {"query": "(\"Junior Developer\" OR \"Entry-Level\") AND (\"React\" OR \"Next.js\") AND (\"Node\")", "job_type": "Junior"},
        {"query": "(\"Junior Frontend Developer\") AND (\"React Native\" OR \"Tailwind\") AND (\"JavaScript\")", "job_type": "Junior"},
        {"query": "(\"Junior Backend Developer\" OR \"Associate\") AND (\"Node.js\" OR \"Python\") AND (\"Express\")", "job_type": "Junior"},
    ],
    "Mid-Level": [
        {"query": "(\"Mid-Level Developer\" OR \"Intermediate Engineer\") AND (\"React\" OR \"Next.js\") AND (\"Node\")", "job_type": "Mid-Level"},
        {"query": "(\"Software Engineer II\" OR \"Intermediate\") AND (\"React Native\" OR \"Tailwind\") AND (\"JavaScript\")", "job_type": "Mid-Level"},
        {"query": "(\"Mid-Level Backend Developer\") AND (\"Node.js\" OR \"Python\") AND (\"Express\")", "job_type": "Mid-Level"},
    ],
    "Senior": [
        {"query": "(\"Senior Developer\" OR \"Senior Engineer\") AND (\"React\" OR \"Next.js\") AND (\"Node\")", "job_type": "Senior"},
        {"query": "(\"Senior Frontend Developer\" OR \"Lead\") AND (\"React Native\" OR \"Tailwind\") AND (\"JavaScript\")", "job_type": "Senior"},
        {"query": "(\"Senior Backend Developer\" OR \"Staff\") AND (\"Node.js\" OR \"Python\") AND (\"Express\")", "job_type": "Senior"},
    ],
}


def generate_search_queries() -> dict:
    resume_data = _load_resume_json()

    skills_json_str = get_skills_from_json(resume_data)
    seniority_level, seniority_reason = get_seniority_from_json(resume_data)

    print(f"[*] Detected seniority level from resume JSON: {seniority_level}")
    print(f"    Reason: {seniority_reason}")

    seniority_rule = SENIORITY_PROMPT_RULES[seniority_level]

    client = genai.Client()

    prompt = f"""
You are an expert technical recruiter and Boolean search architect.
Analyze the candidate's skills JSON object provided below:

Skills JSON:
{skills_json_str}

The candidate's seniority level has already been determined by prior analysis of their resume:
"{seniority_reason}"

Your task is to generate EXACTLY 3 job search queries using Boolean operators (AND, OR) and parentheses.
{seniority_rule}

Return your response strictly as a valid JSON object with a single key "queries" containing a list of 3 objects. Each object must have:
- "query": The Boolean search string containing seniority level and skills.
- "job_type": The seniority level intended for that query (must match "{seniority_level}" or a close synonym of it, e.g. "Senior", "Lead", "Staff" if the level is Senior).

Example format:
{{
  "queries": [
    {{
      "query": "(\\"{seniority_level} Developer\\" OR \\"{seniority_level} Engineer\\") AND (\\"React\\" OR \\"Next.js\\") AND (\\"Node\\")",
      "job_type": "{seniority_level}"
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
        print("[!] Gemini response failed to parse as JSON. Using seniority-matched fallback queries.")
        data = {
            "source": f"temp_organized_resume.json -> skills (seniority-targeted: {seniority_level})",
            "queries": FALLBACK_QUERIES[seniority_level],
        }

    # Ensure structured cache format + always stamp the detected seniority
    data["source"] = f"temp_organized_resume.json -> skills (seniority-targeted: {seniority_level})"
    data["detected_seniority"] = seniority_level
    data["seniority_reason"] = seniority_reason

    # Store structured queries and job types in query_cache.json (full overwrite)
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return data


if __name__ == "__main__":
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)

    result = generate_search_queries()
    print(f"\n[*] Seniority used for this run: {result.get('detected_seniority')}")
    for i, item in enumerate(result.get("queries", [])):
        print(f"Query {i+1} [{item.get('job_type')}]: {item.get('query')}")