import sys
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from fastapi import Query

# Make the project root importable.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from retrieval.paper_search import search_papers, load_papers
# from ingestion.rag_pipeline import retrieve_chunks, generate_answer
from ingestion.rag_pipeline import (
    retrieve_chunks,
    generate_answer,
    generate_reading_response,
)
from recommendation.recommender import recommend_papers


app = FastAPI(
    title="Research Paper Intelligence API",
    description="Search research papers and ask questions using RAG.",
    version="1.0.0",
)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    paper_id: str = Field(min_length=1)


class SummarizeRequest(BaseModel):
    paper_id: str = Field(min_length=1)
    focus: str = Field(
        default="main contributions and methodology",
        min_length=1,
        max_length=300,
    )

class ConversationTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=12000)


class ExplainRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    paper_id: str = Field(min_length=1)
    level: Literal[
        "beginner", "intermediate", "expert"
    ] = "intermediate"
    history: list[ConversationTurn] = Field(
        default_factory=list,
        max_length=10,
    )



@app.get("/")
def home():
    return {
        "message": "Research Paper Intelligence API is running",
        "docs": "/docs",
    }


@app.get("/papers")
def get_papers(
    query: str = Query(default="", max_length=200),
    field: Literal[
        "all", "title", "author", "year", "domain", "keyword"
    ] = "all",
):
    try:
        papers = search_papers(query=query, field=field)
        return {
            "query": query,
            "field": field,
            "count": len(papers),
            "papers": papers,
        }
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Paper search failed: {error}",
        )


@app.post("/ask")
def ask_question(request: AskRequest):
    question = request.question.strip()
    paper_id = request.paper_id.strip()

    if not question or not paper_id:
        raise HTTPException(
            status_code=400,
            detail="Question and paper ID cannot be empty.",
        )

    # Validate that the paper exists in the metadata.
    try:
        papers = load_papers()
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not load paper metadata: {error}",
        )

    if paper_id not in papers:
        raise HTTPException(
            status_code=404,
            detail=f"Paper ID '{paper_id}' was not found.",
        )

    try:
        results = retrieve_chunks(
            question,
            paper_id=paper_id,
        )

        documents = results.get("documents", [[]])[0]

        if not documents:
            raise HTTPException(
                status_code=404,
                detail="No relevant passages were retrieved.",
            )

        answer, metadatas = generate_answer(question, results)

        sources = []

        for index, metadata in enumerate(metadatas, start=1):
            sources.append({
                "source": index,
                "paper_id": metadata.get("paper_id", "Unknown"),
                "page": metadata.get(
                    "page_label",
                    metadata.get("page", "Unknown"),
                ),
            })

        return {
            "question": question,
            "paper_id": paper_id,
            "answer": answer,
            "sources": sources,
        }

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Question answering failed: {error}",
        )


@app.post("/summarize")
def summarize_paper(request: SummarizeRequest):
    paper_id = request.paper_id.strip()

    papers = load_papers()
    if paper_id not in papers:
        raise HTTPException(
            status_code=404,
            detail=f"Paper ID '{paper_id}' was not found.",
        )

    question = (
        f"Summarize the paper, focusing on {request.focus}. "
        "Cover the research problem, methodology, contributions, "
        "findings, and limitations where supported."
    )

    try:
        results = retrieve_chunks(question, paper_id=paper_id)

        if not results.get("documents", [[]])[0]:
            raise HTTPException(
                status_code=404,
                detail="No relevant passages were retrieved.",
            )

        summary, metadatas = generate_reading_response(
            question,
            results,
            mode="summarize",
        )

        return {
            "paper_id": paper_id,
            "focus": request.focus,
            "summary": summary,
            "sources": [
                {
                    "source": i,
                    "paper_id": m.get("paper_id", "Unknown"),
                    "page": m.get(
                        "page_label", m.get("page", "Unknown")
                    ),
                }
                for i, m in enumerate(metadatas, start=1)
            ],
        }

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Summarization failed: {error}",
        )


@app.post("/explain")
def explain_concept(request: ExplainRequest):
    question = request.question.strip()
    paper_id = request.paper_id.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    # Validate the paper ID.
    try:
        papers = load_papers()
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not load paper metadata: {error}",
        )

    if paper_id not in papers:
        raise HTTPException(
            status_code=404,
            detail=f"Paper ID '{paper_id}' was not found.",
        )

    # Convert validated Pydantic objects into dictionaries.
    history = [
        turn.model_dump()
        for turn in request.history
    ]

    try:
        # Include recent conversation when retrieving evidence.
        retrieval_query = question

        if history:
            recent_history = history[-6:]

            history_text = "\n".join(
                f"{turn['role']}: {turn['content']}"
                for turn in recent_history
            )

            retrieval_query = (
                f"Conversation context:\n{history_text}\n\n"
                f"Current question: {question}"
            )

        results = retrieve_chunks(
            retrieval_query,
            paper_id=paper_id,
        )

        documents = results.get("documents", [[]])[0]

        if not documents:
            raise HTTPException(
                status_code=404,
                detail="No relevant passages were retrieved.",
            )

        answer, metadatas = generate_reading_response(
            question,
            results,
            mode="explain",
            level=request.level,
            conversation_history=history,
        )

        sources = [
            {
                "source": index,
                "paper_id": metadata.get("paper_id", "Unknown"),
                "page": metadata.get(
                    "page_label",
                    metadata.get("page", "Unknown"),
                ),
            }
            for index, metadata in enumerate(metadatas, start=1)
        ]

        return {
            "paper_id": paper_id,
            "question": question,
            "level": request.level,
            "answer": answer,
            "sources": sources,
        }

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Explanation failed: {error}",
        )

@app.get("/recommend")
def get_recommendations(
    domain: Optional[str] = Query(default=None),
    year_from: Optional[int] = Query(default=None, ge=1900, le=2100),
    year_to: Optional[int] = Query(default=None, ge=1900, le=2100),
    limit: int = Query(default=5, ge=1, le=20),
):
    if year_from is not None and year_to is not None:
        if year_from > year_to:
            return {
                "recommendations": [],
                "count": 0,
                "message": "year_from must not exceed year_to",
            }

    papers = recommend_papers(
        domain=domain,
        year_from=year_from,
        year_to=year_to,
        limit=limit,
    )

    return {
        "recommendations": papers,
        "count": len(papers),
    }
