import json
from pathlib import Path

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.rag_pipeline import retrieve_chunks

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = PROJECT_ROOT / "evaluation" / "rag_eval_dataset.json"

TOP_K = 5


def evaluate_question(question_data):
    question = question_data["question"]
    paper_id = question_data["paper_id"]
    relevant_ids = set(question_data["relevant_chunk_ids"])

    # Retrieve chunks from the existing RAG pipeline
    results = retrieve_chunks(question, paper_id=paper_id)

    # Match the returned chunk IDs to the ground-truth labels
    retrieved_ids = results["ids"][0][:TOP_K]
    relevant_retrieved = [
        chunk_id for chunk_id in retrieved_ids
        if chunk_id in relevant_ids
    ]

    precision = (
        len(relevant_retrieved) / len(retrieved_ids) 
        if retrieved_ids else 0.0
    )

    recall = (
        len(relevant_retrieved) / len(relevant_ids)
        if relevant_ids else None
    )

    reciprocal_rank = 0.0
    for rank, chunk_id in enumerate(retrieved_ids, start=1):
        if chunk_id in relevant_ids:
            reciprocal_rank = 1.0 / rank
            break

    return {
        "question_id": question_data["question_id"],
        "precision_at_5": precision,
        "recall_at_5": recall,
        "reciprocal_rank": reciprocal_rank,
        "retrieved_ids": retrieved_ids,
        "relevant_retrieved": relevant_retrieved,
    }


def main():
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    results = []

    for question_data in dataset:
        if not question_data["answerable"]:
            print(
                f"Skipping {question_data['question_id']}: "
                "unanswerable question"
            )
            continue

        result = evaluate_question(question_data)
        results.append(result)

        print(f"\nQuestion: {result['question_id']}")
        print(f"Retrieved IDs: {result['retrieved_ids']}")
        print(f"Relevant retrieved: {result['relevant_retrieved']}")
        print(f"Precision@5: {result['precision_at_5']:.3f}")

        if result["recall_at_5"] is not None:
            print(f"Recall@5: {result['recall_at_5']:.3f}")

        print(f"Reciprocal Rank: {result['reciprocal_rank']:.3f}")

    if not results:
        print("No answerable questions to evaluate.")
        return

    mean_precision = sum(
        result["precision_at_5"] for result in results
    ) / len(results)

    recall_results = [
        result["recall_at_5"]
        for result in results
        if result["recall_at_5"] is not None
    ]

    mean_recall = (
        sum(recall_results) / len(recall_results)
        if recall_results else None
    )

    mrr = sum(
        result["reciprocal_rank"] for result in results
    ) / len(results)

    print("\n========== OVERALL RESULTS ==========")
    print(f"Evaluated questions: {len(results)}")
    print(f"Mean Precision@5: {mean_precision:.3f}")

    if mean_recall is not None:
        print(f"Mean Recall@5: {mean_recall:.3f}")

    print(f"MRR: {mrr:.3f}")


if __name__ == "__main__":
    main()