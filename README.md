# ScholarSpace — Research Paper Intelligence & Reading Assistant

ScholarSpace is a research-paper assistant that combines semantic retrieval,
retrieval-augmented generation (RAG), and adaptive explanations to help users
understand technical research papers.

## Features

- Search research papers using available metadata.
- Retrieve relevant passages from indexed papers.
- Ask questions about research papers using RAG.
- Generate summaries and explanations at different difficulty levels.
- Maintain conversation context for follow-up questions.
- Evaluate retrieval and answer-generation behavior.

## Technology Stack

- Python
- FastAPI
- ChromaDB
- BGE-M3 embeddings
- Ollama with Phi-3
- PyPDF-based document ingestion

## Project Structure

- `app/` — API and command-line assistant
- `ingestion/` — PDF ingestion, chunking, embeddings, and RAG pipeline
- `retrieval/` — Paper metadata search
- `recommendation/` — Paper recommendation code
- `evaluation/` — Retrieval and answer evaluation
- `tests/` — Automated tests
- `data/metadata/` — Curated paper metadata and evaluation records

## Setup

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install the dependencies from `requirements.txt`.
4. Configure Ollama and download the required generation model.
5. Download or restore the research papers and build the local ChromaDB
   collection using the ingestion scripts.
6. Configure any required environment variables locally.
7. Start the FastAPI application using the instructions below.

Create a local `.env` file only if required by the application. Never commit
secrets or credentials.

## Run the API

From the project root, activate your virtual environment and run:

```bash
uvicorn app.main:app --reload
Open http://127.0.0.1:8000/docs to inspect the API.
The API requires the relevant local dependencies, paper index, and Ollama
service to be configured and available.
Local Data
Downloaded PDFs, extracted full-text files, virtual environments, local
vector databases, and model weights are excluded from Git. The original
research-paper files and generated index must be available locally for
retrieval to work.
Evaluation
Evaluation scripts and the current evaluation dataset are located in
evaluation/. Reported evaluation results are preliminary and depend on
the quality of the ground-truth labels and evaluation methodology.
