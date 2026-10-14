
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.rag_pipeline import retrieve_chunks

DATASET_PATH = PROJECT_ROOT / "evaluation" / "rag_eval_dataset.json"


def main():
    with DATASET_PATH.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    for item in dataset:
        question = item["question"]
        paper_id = item["paper_id"]
        relevant_ids = set(item["relevant_chunk_ids"])

        print("\n" + "=" * 100)
        print(f"{item['question_id']}: {question}")
        print(f"Paper: {paper_id}")

        results = retrieve_chunks(question, paper_id=paper_id)

        ids = (results.get("ids") or [[]])[0] or []
        documents = (results.get("documents") or [[]])[0] or []
        metadatas = (results.get("metadatas") or [[]])[0] or []
        distances = (results.get("distances") or [[]])[0] or []

        for rank, (chunk_id, document, metadata, distance) in enumerate(
            zip(ids, documents, metadatas, distances),
            start=1,
        ):
            metadata = metadata or {}
            page = metadata.get(
                "page_label",
                metadata.get("page", "Unknown"),
            )
            label = (
                "LABELLED RELEVANT"
                if chunk_id in relevant_ids
                else "NOT YET LABELLED"
            )

            print("\n" + "-" * 80)
            print(
                f"Rank: {rank} | ID: {chunk_id} | Page: {page} "
                f"| Distance: {distance:.4f}"
            )
            print(f"Label: {label}")
            print(document[:1200].strip())


if __name__ == "__main__":
    main()
