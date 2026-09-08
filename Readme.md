<div align="center">

# 🤖 JobScout-AI

**An Agentic AI-Powered Resume Parser, Vector Store, and Automated Job Scraping Pipeline**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Vector Store-ChromaDB-orange](https://img.shields.io/badge/Vector_Store-ChromaDB-orange.svg)](https://www.trychroma.com/)
[![Scraper-JobSpy-green](https://img.shields.io/badge/Scraper-JobSpy-green.svg)](https://github.com/BullsEyePundit/JobSpy)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent, multi-stage pipeline that parses candidate resumes, organizes skills using vision/language capabilities, indexes semantic embeddings in ChromaDB, generates targeted search queries, and scrapes fresh remote tech job opportunities across major platforms.

</div>

---

## 📌 Overview

**JobScout-AI** bridges the gap between candidate resumes and active job board listings. Rather than relying on generic keyword searches, JobScout-AI analyzes candidate credentials, extracts structured skills, stores vector representations for semantic matching, and dynamically formulates search queries filtered by seniority target levels (e.g., *Junior*, *Mid*, *Senior*).

It systematically queries live job aggregators (LinkedIn, Indeed, Google Jobs) using **JobSpy**, enforcing strict age and seniority rules to deliver high-intent, recent opportunities directly into structured local caches.

---

## ✨ Key Features

- 📄 **Smart Resume Parsing**: Extracts structured technical credentials from PDF resumes (`parser.py`).
- 👁️ **Visual & Semantic Structuring**: Leverages VLM/LLM capabilities to categorize candidate skills into structured domains (`vlm.py`).
- ⚡ **Vector DB Indexing**: Embeds and indexes resume context into **ChromaDB** for efficient semantic retrieval (`chroma_store.py`).
- 🎯 **Targeted Query Generation**: Dynamically constructs Boolean search queries mapped to candidate seniority targets (`query-generation.py`).
- 🔍 **Multi-Platform Web Scraping**: Scrapes active listings across **LinkedIn**, **Indeed**, and **Google Jobs** with real-time freshness filters (`job-search.py`).
- 🛡️ **Seniority Rules Engine**: Deterministically evaluates candidate seniority and query parameters to filter out mismatched positions.
- 🔄 **Orchestrated Execution**: Single-command execution via `main.py` with non-destructive, auto-updating cache management.

---


📊 job_results_cache.json

| Step | Module | Function / Responsibility |
| :--- | :--- | :--- |
| **1** | `Core/parser.py` | Extracts raw text and structure from input PDF resumes. |
| **2** | `Core/vlm.py` | Processes resume content to extract domain skills into `temp_organized_resume.json`. |
| **3** | `Data/chroma_store.py` | Generates vector embeddings and stores chunks inside local ChromaDB storage. |
| **4** | `Core/query-generation.py` | Formulates optimized Boolean search queries linked with target job levels in `query_cache.json`. |
| **5** | `Core/job-search.py` | Executes multi-site scraping via JobSpy, filtering results by location, age ($\le$ 2 days), and target match. |

---

## 🏗 System Architecture & Pipeline

<img width="1174" height="514" alt="image" src="https://github.com/user-attachments/assets/653821e0-224e-4024-90ec-50dff1d73de9" /> <img width="1196" height="526" alt="image" src="https://github.com/user-attachments/assets/c5f6b3b3-0bba-4821-ac93-5c406995bafc" /> <img width="1093" height="485" alt="image" src="https://github.com/user-attachments/assets/d2fa9a94-d0e5-4373-aa92-89bbdc704f75" />




## 📂 Project Hierarchy

```text
JobScout-AI/
├── Core/
│   ├── job-search.py           # Multi-platform job scraper & seniority filter
│   ├── parser.py               # Resume text extraction utility
│   ├── query-generation.py    # LLM-driven query builder
│   ├── resume.pdf              # Input resume file
│   └── vlm.py                  # Vision-Language model skill structurer
├── Data/
│   ├── chroma_store.py         # Vector DB embedding pipeline
│   └── check_db.py             # ChromaDB inspection/debug tool
├── utils/                      # Helper scripts and prompt templates
├── .env                        # Environment configurations (API keys)
├── .gitignore                  # Git exclusions (Caches, DBs, pycache)
├── main.py                     # Master execution orchestration entry point
└── Readme.md                   # Project documentation
