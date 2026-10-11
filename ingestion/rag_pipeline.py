import gc
import chromadb
import ollama
import torch
from FlagEmbedding import BGEM3FlagModel

DB_PATH = "data/vector_db/chroma"
COLLECTION_NAME = "research_papers_bge_m3"
LLM_NAME = "phi3:latest"
TOP_K = 5


def retrieve_chunks(question, paper_id=None):
    """Embed the question and retrieve relevant chunks."""
    model = BGEM3FlagModel(
        "BAAI/bge-m3",
        use_fp16=False,
        devices=["cpu"],
    )

    result = model.encode(
        [question],
        batch_size=1,
        max_length=512,
    )
    query_embedding = result["dense_vecs"][0].tolist()

    # Release BGE-M3 from GPU before running the LLM.
    del model
    del result
    gc.collect()
    torch.cuda.empty_cache()

    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_collection(name=COLLECTION_NAME)

    query_args = {
        "query_embeddings": [query_embedding],
        "n_results": TOP_K,
        "include": ["documents", "metadatas", "distances"],
    }

    if paper_id:
        query_args["where"] = {"paper_id": paper_id}

    results = collection.query(**query_args)
    return results


def generate_answer(question, results):
    """Generate an answer using the retrieved passages."""
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    context_parts = []
    for i, (document, metadata) in enumerate(
        zip(documents, metadatas), start=1
    ):
        paper_id = metadata.get("paper_id", "Unknown")
        page = metadata.get("page_label", metadata.get("page", "Unknown"))

        context_parts.append(
            f"[Source {i}: Paper ID {paper_id}, Page {page}]\n{document}"
        )

    context = "\n\n".join(context_parts)

    prompt = f"""You are a research paper reading assistant.

Answer the user's question using only the supplied research passages.
If the passages do not contain enough information, say so.
Do not invent facts or citations.
Cite supporting passages using [Source 1], [Source 2], etc.

Research passages:
{context}

User question:
{question}

Answer:"""

    response = ollama.chat(
        model=LLM_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        options={
            "temperature": 0.1,
            "num_ctx": 4096,
        },
    )

    return response["message"]["content"], metadatas

def generate_reading_response(
    question,
    results,
    mode="explain",
    level="intermediate",
    conversation_history=None,
):
    """Generate a grounded summary or explanation with conversation context."""

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    context_parts = []

    for i, (document, metadata) in enumerate(
        zip(documents, metadatas), start=1
    ):
        paper_id = metadata.get("paper_id", "Unknown")
        page = metadata.get(
            "page_label",
            metadata.get("page", "Unknown"),
        )

        context_parts.append(
            f"[Source {i}: Paper ID {paper_id}, Page {page}]\n"
            f"{document}"
        )

    context = "\n\n".join(context_parts)

    # Include recent conversation as context.
    history_text = ""

    if conversation_history:
        recent_history = conversation_history[-6:]

        history_text = "\n".join(
            f"{turn['role'].capitalize()}: {turn['content']}"
            for turn in recent_history
        )

    # Select the appropriate instructions.
    if mode == "summarize":
        instructions = """
Create a structured research-paper summary covering, where supported:
1. Research problem and objectives
2. Main contributions
3. Methodology or proposed approach
4. Important findings
5. Limitations, if discussed

Use only the supplied research passages. Clearly state when
information is unavailable. Do not invent results or limitations.
"""
    elif mode == "explain":
        level_instructions = {
            "beginner": (
                "Use simple language, define technical terms, "
                "and provide an intuitive example when appropriate."
            ),
            "intermediate": (
                "Explain the concept with technical detail suitable "
                "for a university student familiar with the basics."
            ),
            "expert": (
                "Provide a technically detailed explanation, including "
                "relevant mechanisms, assumptions, and equations "
                "when supported by the passages."
            ),
        }

        if level not in level_instructions:
            raise ValueError(f"Unsupported explanation level: {level}")

        instructions = level_instructions[level]
    else:
        raise ValueError(f"Unsupported response mode: {mode}")

    prompt = f"""You are a research paper reading assistant.

Instructions:
{instructions}

Use previous conversation turns only to understand the user's
current question and references to earlier topics.
The research passages below must provide the evidence for your answer.
If the passages do not contain enough evidence, say so.
Do not invent facts or citations.
Cite supporting passages using [Source 1], [Source 2], etc.

Previous conversation:
{history_text if history_text else "No previous conversation."}

Research passages:
{context}

Current user question:
{question}

Response:"""

    response = ollama.chat(
        model=LLM_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        options={
            "temperature": 0.1,
            "num_ctx": 4096,
        },
    )

    return response["message"]["content"], metadatas


def main():
    question = input("Ask a question about your research papers: ").strip()

    if not question:
        print("Please enter a question.")
        return

    # Optional filter: set a paper ID to restrict retrieval.
    # Leave as None to search across all 37 papers.
    paper_id = None

    results = retrieve_chunks(question, paper_id)

    if not results["documents"] or not results["documents"][0]:
        print("No relevant passages were found.")
        return

    answer, metadatas = generate_answer(question, results)

    print("\n========== ANSWER ==========\n")
    print(answer)

    print("\n========== RETRIEVED SOURCES ==========\n")
    seen = set()

    for metadata in metadatas:
        key = (
            metadata.get("paper_id"),
            metadata.get("page_label", metadata.get("page")),
        )

        if key not in seen:
            seen.add(key)
            print(
                f"Paper: {metadata.get('paper_title', metadata.get('paper_id'))}"
                f" | ID: {metadata.get('paper_id')}"
                f" | Page: {key[1]}"
            )


if __name__ == "__main__":
    main()
