jobscout-ai/
│
├── core/                   # The brains of your application
│   ├── __init__.py         # Makes 'core' a Python module
│   ├── parser.py           # Extracts text from PDFs (pypdf)
│   ├── vector_store.py     # Handles LangChain chunking and Chroma DB
│   ├── generator.py        # Prompts the LLM for agentic job search queries
│   ├── search.py           # Executes real-time searches via Tavily API
│   └── evaluator.py        # Calculates the match score and reasons the output
│
├── data/                   # Local file storage (Keep this out of Git!)
│   ├── inputs/             # Drop candidate CVs (.pdf, .docx) here
│   ├── outputs/            # Generated CLI reports/Markdown files save here
│   └── chroma_db/          # Local persistent storage for your vector database
│
├── utils/                  # Helper functions to keep core logic clean
│   ├── __init__.py
│   ├── config.py           # Loads and validates .env API keys securely
│   └── logger.py           # Formats your beautiful CLI/Markdown terminal output
│
├── .env                    # Your private API keys (Groq/Gemini, Tavily)
├── .gitignore              # Ignores 'data/', '.env', and '__pycache__/'
├── requirements.txt        # pip dependencies (pypdf, langchain, chromadb, etc.)
├── README.md               # Hackathon documentation and HLD diagram
└── main.py                 # The orchestrator script that runs the whole pipeline