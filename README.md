# ScholarSpace — Research Paper Intelligence & Reading Assistant

ScholarSpace is an AI-powered research assistant that helps users explore research papers, understand technical concepts, and find relevant information through natural-language questions. It uses Retrieval-Augmented Generation (RAG) to generate answers grounded in a curated collection of research papers.

## Features

- **AI Research Assistant:** Ask questions about research papers and receive context-grounded answers with relevant references.
- **Semantic Search:** Find relevant passages using BGE-M3 embeddings and ChromaDB.
- **RAG Pipeline:** Combine retrieved research passages with an LLM to generate informative responses.
- **Paper Discovery:** Browse research papers and explore their details.
- **Personal Library and Notes:** Save papers and notes for later reference.
- **Authentication and Cloud Sync:** Use Firebase Authentication for Google sign-in and Firestore to synchronize user data.
- **Retrieval Evaluation:** Evaluate search quality using Precision@K, Recall@K, and Mean Reciprocal Rank (MRR).

## How It Works

1. A user submits a research question through the React frontend.
2. The FastAPI backend processes the question and retrieves relevant passages from ChromaDB using BGE-M3 embeddings and hybrid ranking.
3. The retrieved passages are provided as context to Phi-3, running through Ollama.
4. The model generates an answer based on the available context, which is returned to the frontend with relevant research references.

The quality of an answer depends on the retrieved passages, the available research corpus, and the language model.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, TypeScript, Vite, CSS |
| Backend | Python, FastAPI |
| Embeddings | BGE-M3 |
| Vector Database | ChromaDB |
| Language Model | Phi-3, Ollama |
| Document Processing | PyPDFLoader, RecursiveCharacterTextSplitter |
| Authentication | Firebase Authentication |
| Cloud Storage | Cloud Firestore |
| Evaluation | Precision@K, Recall@K, MRR |

## Project Structure

```text
Research-paper-assistant/
├── app/                  # Backend application and assistant entry points
├── data/                 # Research data, metadata, and local indexes
├── evaluation/            # Retrieval evaluation and inspection scripts
├── ingestion/             # Document ingestion, embeddings, and RAG pipeline
├── frontend_updated/      # React frontend
├── requirements.txt       # Python dependencies
└── README.md
```

## Getting Started

### Prerequisites

Install Python, Node.js, npm, Git, and Ollama. The AI models and vector database also require sufficient local storage and memory.

### 1. Clone the repository

```bash
git clone https://github.com/adityaDev-2005/Research-paper-assistant.git
cd Research-paper-assistant
```

### 2. Set up the backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ollama pull phi3
python -m uvicorn app.main:app --reload
```

The FastAPI server should be available at `http://127.0.0.1:8000`. Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

### 3. Set up the frontend

Open another terminal:

```bash
cd Research-paper-assistant/frontend_updated
npm install
npm run dev
```

Vite will display the local frontend URL, typically `http://localhost:5173`.

Configure the Firebase environment variables using `frontend_updated/.env.example` and ensure the frontend API configuration points to the running backend. Google sign-in also requires Firebase Authentication to be configured.

The existing ChromaDB index and research data must be available for retrieval to work. Refer to the ingestion scripts if the index needs to be created.

## Retrieval Evaluation

The project includes scripts for evaluating and inspecting retrieved passages. Its current preliminary baseline, measured on five manually labelled questions, is:

| Metric | Score |
|---|---:|
| Precision@5 | 0.240 |
| Recall@5 | 0.370 |
| MRR | 0.740 |

These results are an initial evaluation, not a comprehensive benchmark. A larger, carefully labelled test set is needed to assess retrieval quality more reliably.

## Deployment

The frontend can be built using `npm run build` inside `frontend_updated/`. It can be hosted on a static hosting platform, while the FastAPI backend requires a separate service capable of running the AI models and accessing persistent vector storage.

A frontend deployment alone is not sufficient: the backend, model inference, database, Firebase configuration, and production API URL must also be configured.

## Future Improvements

- Expand the research corpus and retrieval evaluation dataset.
- Improve citation traceability and answer grounding.
- Optimize frontend loading and performance.
- Enhance paper discovery and personalized recommendations.
- Deploy the complete application with reliable model inference and persistent storage.

## Author

**Aditya Asutosh Mishra**

- GitHub: [adityaDev-2005](https://github.com/adityaDev-2005)
- LinkedIn: [Profile](https://www.linkedin.com/in/aditya-asutosh-mishra-1654b2331/)
