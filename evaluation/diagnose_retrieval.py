
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.rag_pipeline import retrieve_chunks

DATASET_PATH = PROJECT_ROOT / "evaluation" / "rag_eval_dataset.json"


def main():
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    for item in dataset:
        question = item["question"]
        paper_id = item.get("paper_id")
        relevant_ids = set(item["relevant_chunk_ids"])

        print("\n" + "=" * 75)
        print(f"{item['question_id']}: {question}")
        print(f"Paper: {paper_id}")
        print("Ground-truth relevant chunks:", sorted(relevant_ids))

        results = retrieve_chunks(question, paper_id=paper_id)

        ids = results["ids"][0]
        distances = results["distances"][0]

        print("\nRetrieved ranking:")

        for rank, (chunk_id, distance) in enumerate(
            zip(ids, distances), start=1
        ):
            status = "RELEVANT" if chunk_id in relevant_ids else "NOT LABELLED"
            print(
                f"Rank {rank} | Distance: {distance:.4f} | "
                f"{status} | {chunk_id}"
            )


if __name__ == "__main__":
    main()
