import os
import json
import warnings
import logging

warnings.filterwarnings("ignore")
logging.getLogger().setLevel(logging.ERROR)
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
from google import genai

load_dotenv()

# Updated path to save query_cache.json directly in the project root directory
CACHE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../query_cache.json"))

def format_candidate_data(raw_texts: list[str]) -> str:
    cleaned_chunks = [chunk.strip() for chunk in raw_texts if chunk.strip()]
    formatted_profile = "\n\n".join(cleaned_chunks)
    return formatted_profile

def get_relevant_cv_data():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    persist_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "../Data/chroma_db"))
    
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
        collection_name="candidate_cv"
    )
    
    query = "skills work experience MERN Python AI fullstack developer projects"
    docs = vectorstore.similarity_search(query, k=4)
    
    seen = set()
    unique_texts = []
    for doc in docs:
        if doc.page_content not in seen:
            seen.add(doc.page_content)
            unique_texts.append(doc.page_content)
            
    candidate_profile = format_candidate_data(unique_texts)
    return candidate_profile

def generate_search_queries(candidate_profile: str) -> list[str]:
    # Check temporary cache first
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)
            cached_queries = data.get("queries", [])
            if cached_queries:
                return cached_queries

    client = genai.Client()
    
    prompt = f"""
    Based on the following candidate profile extracted from their CV, generate exactly 3 professional job search queries using Boolean operators (AND, OR) and parentheses, exactly matching this structure style:
    ("Full-Stack" OR MERN) (Remote OR Freelance)
    (LangChain OR "Python AI" OR "Generative AI") (Developer OR Engineer) (Freelance OR Contract)
    
    Candidate Profile:
    {candidate_profile}
    
    Return ONLY the 3 search queries separated by newlines, with no extra text, explanations, or numbering.
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    
    queries = [q.strip() for q in response.text.split("\n") if q.strip()][:3]
    
    # Save generated queries to temporary cache file in the root folder
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump({"queries": queries}, f, indent=4)
        
    return queries

if __name__ == "__main__":
    profile = get_relevant_cv_data()
    queries = generate_search_queries(profile)
    for i, q in enumerate(queries):
        print(f"Query {i+1}: {q}")