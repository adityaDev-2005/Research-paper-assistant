
import re
import time
from functools import lru_cache

import chromadb
import ollama
from FlagEmbedding import BGEM3FlagModel

# --------------------------------------------------
# Configuration
# --------------------------------------------------

DB_PATH = "data/vector_db/chroma"
COLLECTION_NAME = "research_papers_bge_m3_clean"
LLM_NAME = "phi3:latest"

TOP_K = 5
RETRIEVAL_CANDIDATES = 30

NUM_CTX = 4096

ANSWER_MAX_TOKENS = 320
EXPLAIN_MAX_TOKENS = 384
SUMMARY_MAX_TOKENS = 512


# --------------------------------------------------
# Cached resources
# --------------------------------------------------

@lru_cache(maxsize=1)
def get_embedding_model():
    """Load BGE-M3 once and reuse it across requests."""
    print("[RAG] Loading BGE-M3 embedding model...")
    start = time.perf_counter()

    model = BGEM3FlagModel(
        "BAAI/bge-m3",
        use_fp16=False,
        devices=["cpu"],
    )

    print(
        f"[TIMING] BGE-M3 initialization: "
        f"{time.perf_counter() - start:.2f}s"
    )
    return model


@lru_cache(maxsize=1)
def get_collection():
    """Reuse the persistent ChromaDB collection."""
    print("[RAG] Opening ChromaDB collection...")
    start = time.perf_counter()

    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_collection(name=COLLECTION_NAME)

    print(
        f"[TIMING] ChromaDB initialization: "
        f"{time.perf_counter() - start:.2f}s"
    )
    return collection


# --------------------------------------------------
# Retrieval
# --------------------------------------------------

def retrieve_chunks(question, paper_id=None):
    """Retrieve candidates and rerank them for relevance."""
    total_start = time.perf_counter()

    question = question.strip()
    if not question:
        raise ValueError("The question cannot be empty.")

    stage_start = time.perf_counter()
    model = get_embedding_model()

    print(
        f"[TIMING] Get embedding model: "
        f"{time.perf_counter() - stage_start:.2f}s"
    )

    stage_start = time.perf_counter()
    result = model.encode(
        [question],
        batch_size=1,
        max_length=512,
    )
    query_embedding = result["dense_vecs"][0].tolist()

    print(
        f"[TIMING] Query embedding: "
        f"{time.perf_counter() - stage_start:.2f}s"
    )

    stage_start = time.perf_counter()
    collection = get_collection()

    query_args = {
        "query_embeddings": [query_embedding],
        "n_results": RETRIEVAL_CANDIDATES,
        "include": ["documents", "metadatas", "distances"],
    }

    if paper_id:
        query_args["where"] = {"paper_id": paper_id}

    results = collection.query(**query_args)

    ids = (results.get("ids") or [[]])[0] or []
    documents = (results.get("documents") or [[]])[0] or []
    metadatas = (results.get("metadatas") or [[]])[0] or []
    distances = (results.get("distances") or [[]])[0] or []

    # Keep each candidate's ID, document, metadata, and distance together.
    candidates = []

    for i, chunk_id in enumerate(ids):
        if i >= len(documents) or i >= len(metadatas):
            continue

        document = documents[i]
        if not document or not document.strip():
            continue

        metadata = metadatas[i] or {}
        distance = distances[i] if i < len(distances) else 1.0

        candidates.append({
            "id": chunk_id,
            "document": document,
            "metadata": metadata,
            "distance": distance,
        })

    # Lightweight lexical reranking alongside dense similarity.
    stop_words = {
        "a", "an", "and", "are", "as", "at", "be", "by", "for",
        "from", "how", "in", "is", "it", "of", "on", "or", "the",
        "their", "this", "to", "what", "when", "which", "with",
    }

    def normalize_token(token):
        """Normalize common plural forms."""
        if len(token) > 4 and token.endswith("ies"):
            return token[:-3] + "y"

        if (
            len(token) > 4
            and token.endswith("s")
            and not token.endswith("ss")
        ):
            return token[:-1]

        return token

    query_terms = {
        normalize_token(token)
        for token in re.findall(r"[a-zA-Z0-9]+", question.lower())
        if len(token) > 2 and token not in stop_words
    }

    question_lower = question.lower()

    broad_intent = any(
        phrase in question_lower
        for phrase in (
            "main goal",
            "main objective",
            "primary objective",
            "main contribution",
            "purpose of",
            "what is the goal",
        )
    )

    for candidate in candidates:
        distance = float(candidate["distance"])
        dense_score = 1.0 - distance

        document_terms = {
            normalize_token(token)
            for token in re.findall(
                r"[a-zA-Z0-9]+",
                candidate["document"].lower(),
            )
        }

        lexical_score = (
            len(query_terms & document_terms) / len(query_terms)
            if query_terms
            else 0.0
        )

        # Dense similarity remains the primary signal.
        score = 0.70 * dense_score + 0.30 * lexical_score

        # Slightly favor the abstract/introduction for broad goal questions.
        if broad_intent:
            page_value = candidate["metadata"].get(
                "page_label",
                candidate["metadata"].get("page"),
            )

            try:
                page_number = int(page_value)
            except (TypeError, ValueError):
                page_number = None

            if page_number is not None and page_number <= 2:
                score += 0.04

        candidate["score"] = score

    candidates.sort(
        key=lambda candidate: candidate["score"],
        reverse=True,
    )

    # Select the true top-ranked chunks without page diversification.
    selected = candidates[:TOP_K]

    # Keep IDs, documents, metadata, and distances in the same order.
    results["ids"] = [
        [candidate["id"] for candidate in selected]
    ]
    results["documents"] = [
        [candidate["document"] for candidate in selected]
    ]
    results["metadatas"] = [
        [candidate["metadata"] for candidate in selected]
    ]
    results["distances"] = [
        [candidate["distance"] for candidate in selected]
    ]

    print(
        f"[TIMING] ChromaDB retrieval and reranking: "
        f"{time.perf_counter() - stage_start:.2f}s"
    )
    print(
        f"[RAG] Retrieved {len(selected)} passages from "
        f"{len(candidates)} candidates with final hybrid ranking."
    )
    print(
        f"[TIMING] Total retrieval: "
        f"{time.perf_counter() - total_start:.2f}s"
    )

    return results


def _get_passages(results):
    """Extract valid passages and their metadata."""
    documents = (results.get("documents") or [[]])[0] or []
    metadatas = (results.get("metadatas") or [[]])[0] or []

    passages = []

    for document, metadata in zip(documents, metadatas):
        if not document or not document.strip():
            continue

        metadata = metadata or {}
        paper_id = metadata.get("paper_id", "Unknown")
        page = metadata.get(
            "page_label",
            metadata.get("page", "Unknown"),
        )

        passages.append({
            "document": document.strip(),
            "metadata": metadata,
            "source_label": (
                f"Source {len(passages) + 1}: "
                f"Paper ID {paper_id}, Page {page}"
            ),
        })

    return passages


def _build_context(passages):
    """Build numbered passages for the LLM."""
    return "\n\n".join(
        f"[{passage['source_label']}]\n{passage['document']}"
        for passage in passages
    )


def _log_ollama_stats(response):
    """Log Ollama timing and token statistics when available."""
    keys = (
        "load_duration",
        "prompt_eval_count",
        "prompt_eval_duration",
        "eval_count",
        "eval_duration",
        "total_duration",
    )

    stats = {key: response.get(key) for key in keys}
    print(f"[OLLAMA STATS] {stats}")

    prompt_tokens = response.get("prompt_eval_count")
    prompt_ns = response.get("prompt_eval_duration")
    output_tokens = response.get("eval_count")
    output_ns = response.get("eval_duration")

    if prompt_tokens is not None and prompt_ns:
        print(
            f"[OLLAMA] Prompt processing: "
            f"{prompt_tokens / (prompt_ns / 1e9):.2f} tokens/s"
        )

    if output_tokens is not None and output_ns:
        print(
            f"[OLLAMA] Generation speed: "
            f"{output_tokens / (output_ns / 1e9):.2f} tokens/s"
        )


def _generate(prompt, max_tokens):
    """Run Ollama generation and report its performance."""
    start = time.perf_counter()

    try:
        response = ollama.chat(
            model=LLM_NAME,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.1,
                "num_ctx": NUM_CTX,
                "num_predict": max_tokens,
            },
        )
    except Exception:
        print(
            f"[ERROR] Ollama generation failed after "
            f"{time.perf_counter() - start:.2f}s."
        )
        raise

    print(
        f"[TIMING] Ollama generation: "
        f"{time.perf_counter() - start:.2f}s"
    )

    _log_ollama_stats(response)

    answer = response.get("message", {}).get("content", "").strip()
    if not answer:
        raise RuntimeError("Ollama returned an empty answer.")

    return answer


# --------------------------------------------------
# General question answering
# --------------------------------------------------

def generate_answer(question, results):
    """Answer a question using retrieved research passages."""
    passages = _get_passages(results)

    if not passages:
        return (
            "No relevant passages were retrieved. "
            "Try rephrasing your question.",
            [],
        )

    context = _build_context(passages)

    prompt = f"""You are ScholarSpace, a research-paper assistant.

Answer the question using only the research passages below.

Rules:

- Base factual claims on the supplied passages.
- Do not invent methods, results, limitations, or citations.
- Distinguish facts stated in the passages from reasonable inferences.
- If evidence is insufficient, explicitly say what is missing.
- Cite claims using the supplied labels, such as [Source 1].
- Never cite a source that does not support the claim.
- Be concise and directly answer the question.

Research passages:

{context}

Question:

{question}

Answer:"""

    answer = _generate(prompt, ANSWER_MAX_TOKENS)
    return answer, [p["metadata"] for p in passages]


# --------------------------------------------------
# Summarization and explanations
# --------------------------------------------------

def generate_reading_response(
    question,
    results,
    mode="explain",
    level="intermediate",
    conversation_history=None,
):
    """Generate a grounded summary or explanation."""
    passages = _get_passages(results)

    if not passages:
        return (
            "No relevant passages were retrieved. "
            "Try rephrasing your question.",
            [],
        )

    if mode not in {"explain", "summarize"}:
        raise ValueError(f"Unsupported response mode: {mode}")

    context = _build_context(passages)

    # Include only recognized roles and recent conversational turns.
    history_lines = []

    for turn in (conversation_history or [])[-4:]:
        if not isinstance(turn, dict):
            continue

        role = turn.get("role")
        content = turn.get("content")

        if role not in {"user", "assistant"}:
            continue

        if not isinstance(content, str) or not content.strip():
            continue

        history_lines.append(
            f"{role.capitalize()}: {content.strip()[:1200]}"
        )

    history_text = "\n".join(history_lines) or "No previous conversation."

    if mode == "summarize":
        instructions = """
Create a concise, structured summary using only supported information.

Use these headings when the passages provide relevant evidence:

1. Research problem and objectives
2. Main contributions
3. Methodology
4. Findings
5. Limitations

Do not invent missing sections or claim that a limitation exists unless
the passages support it. State when important information is unavailable.

Prefer clear paragraphs and concise bullet points.
"""
        max_tokens = SUMMARY_MAX_TOKENS

    else:
        level_instructions = {
            "beginner": """
Explain in plain language. Define technical terms and use a short,
intuitive example only when it helps explain the supplied evidence.
Avoid unnecessary jargon.
""",
            "intermediate": """
Explain the concept for a university student familiar with the basics.
Include relevant technical details and methodology, but avoid repetition.
""",
            "expert": """
Give a concise technical explanation. Discuss mechanisms, assumptions,
equations, and limitations only when supported by the passages.
""",
        }

        if level not in level_instructions:
            raise ValueError(f"Unsupported explanation level: {level}")

        instructions = level_instructions[level]
        max_tokens = EXPLAIN_MAX_TOKENS

    prompt = f"""You are ScholarSpace, a research-paper reading assistant.

Task:

{instructions}

Evidence rules:

- Use the supplied research passages as the factual evidence.
- The selected paper's identity must not be treated as evidence by itself.
- Do not merge claims from different papers into one paper's contributions.
- Use previous conversation only to resolve the current question's context.
- Do not treat previous assistant answers as verified evidence.
- If the passages do not establish an answer, say so clearly.
- Cite supporting claims using labels such as [Source 1].
- Do not invent citations, results, limitations, or technical details.

Previous conversation:

{history_text}

Research passages:

{context}

Current question or summary request:

{question}

Response:"""

    answer = _generate(prompt, max_tokens)
    return answer, [p["metadata"] for p in passages]


# --------------------------------------------------
# Command-line testing
# --------------------------------------------------

def main():
    question = input(
        "Ask a question about your research papers: "
    ).strip()

    if not question:
        print("Please enter a question.")
        return

    # Set a paper ID here to restrict retrieval to one paper.
    paper_id = None

    results = retrieve_chunks(question, paper_id)

    if not _get_passages(results):
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

        if key in seen:
            continue

        seen.add(key)

        print(
            f"Paper: {metadata.get('paper_title', metadata.get('paper_id'))}"
            f" | ID: {metadata.get('paper_id')}"
            f" | Page: {key[1]}"
        )


if __name__ == "__main__":
    main()
