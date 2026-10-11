
import json
import re
import sys
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.rag_pipeline import retrieve_chunks, generate_answer

DATASET_PATH = PROJECT_ROOT / "evaluation" / "rag_eval_dataset.json"
OUTPUT_PATH = PROJECT_ROOT / "evaluation" / "answer_evaluation_results.json"


def get_retrieved_context(results):
    """Extract retrieved passages and their metadata from ChromaDB results."""
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    ids = results.get("ids", [[]])[0]

    chunks = []

    for chunk_id, document, metadata in zip(ids, documents, metadatas):
        chunks.append({
            "chunk_id": chunk_id,
            "text": document,
            "metadata": metadata or {}
        })

    return chunks


def calculate_answer_metrics(answer, context):
    """Calculate simple, transparent answer-quality indicators."""
    answer = answer or ""
    answer_lower = answer.lower()

    # Check whether the answer contains source citation markers.
    citations = re.findall(
    r"\[Source\s+\d+(?:[^\]]*)\]",
    answer,
    flags=re.IGNORECASE
)

    # Check how many unique context words also occur in the answer.
    # This is only a lexical-overlap indicator, not a faithfulness score.
    stopwords = {
        "the", "a", "an", "and", "or", "but", "is", "are", "was",
        "were", "to", "of", "in", "on", "for", "with", "by", "as",
        "it", "this", "that", "these", "those", "from", "be", "can",
        "which", "what", "how", "their", "its", "they", "we", "our"
    }

    context_words = set(
        re.findall(r"\b[a-zA-Z]{3,}\b", " ".join(context).lower())
    ) - stopwords

    answer_words = set(
        re.findall(r"\b[a-zA-Z]{3,}\b", answer_lower)
    ) - stopwords

    overlap = (
        len(context_words & answer_words) / len(answer_words)
        if answer_words else 0.0
    )

    return {
        "answer_length_words": len(answer.split()),
        "has_citation": bool(citations),
        "citation_count": len(citations),
        "context_word_overlap": round(overlap, 4)
    }


def evaluate_question(item):
    question_id = item["question_id"]
    question = item["question"]
    paper_id = item.get("paper_id")
    answerable = item.get("answerable", True)

    print(f"\nEvaluating {question_id}: {question}")

    # Retrieve evidence from the selected paper.
    results = retrieve_chunks(question, paper_id=paper_id)
    chunks = get_retrieved_context(results)
    context = [chunk["text"] for chunk in chunks]

    # Generate an answer using the existing RAG generation function.
    answer, generated_metadatas = generate_answer(question, results)

    metrics = calculate_answer_metrics(answer, context)

    print(f"Answer: {answer}")
    print(f"Citation present: {metrics['has_citation']}")
    print(f"Context-word overlap: {metrics['context_word_overlap']}")

    # Human review fields are deliberately left for manual assessment.
    return {
        "question_id": question_id,
        "question": question,
        "paper_id": paper_id,
        "expected_answerable": answerable,
        "answer": answer,
        "retrieved_chunks": [
            chunk["chunk_id"] for chunk in chunks
        ],
        "metrics": metrics,
        "manual_review": {
            "factually_correct": None,
            "faithful_to_context": None,
            "answers_question": None,
            "handles_answerability_correctly": None,
            "notes": ""
        }
    }


def main():
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    results = []

    for item in dataset:
        try:
            results.append(evaluate_question(item))
        except Exception as error:
            print(f"Error evaluating {item.get('question_id')}: {error}")
            results.append({
                "question_id": item.get("question_id"),
                "question": item.get("question"),
                "error": str(error)
            })

    successful = [
        result for result in results
        if "error" not in result
    ]

    if successful:
        citation_rate = sum(
            result["metrics"]["has_citation"]
            for result in successful
        ) / len(successful)

        mean_overlap = sum(
            result["metrics"]["context_word_overlap"]
            for result in successful
        ) / len(successful)
    else:
        citation_rate = 0.0
        mean_overlap = 0.0

    report = {
        "total_questions": len(dataset),
        "successful_evaluations": len(successful),
        "failed_evaluations": len(dataset) - len(successful),
        "summary": {
            "citation_presence_rate": round(citation_rate, 4),
            "mean_context_word_overlap": round(mean_overlap, 4)
        },
        "results": results
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("\n========== ANSWER EVALUATION SUMMARY ==========")
    print(f"Questions: {len(dataset)}")
    print(f"Successful evaluations: {len(successful)}")
    print(f"Failed evaluations: {len(dataset) - len(successful)}")
    print(f"Citation presence rate: {citation_rate:.2%}")
    print(f"Mean context-word overlap: {mean_overlap:.4f}")
    print(f"Saved results to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
