
import csv
import time
from pathlib import Path

from ingestion.rag_pipeline import retrieve_chunks


# Evaluation configuration
PAPER_ID = "ML03"  # Attention Is All You Need
TOPIC = "Transformer architecture and methodology"

QUESTIONS = [
    {
        "id": "ML03-Q01",
        "question": "What is the main contribution of this paper?",
        "expected_topics": [
            "transformer",
            "attention",
            "sequence",
        ],
        "expected_pages": [],
    },
    {
        "id": "ML03-Q02",
        "question": "What architecture does the paper propose?",
        "expected_topics": [
            "encoder",
            "decoder",
            "attention",
        ],
        "expected_pages": [],
    },
    {
        "id": "ML03-Q03",
        "question": "How does multi-head attention work?",
        "expected_topics": [
            "attention",
            "heads",
            "queries",
            "keys",
            "values",
        ],
        "expected_pages": [],
    },
    {
        "id": "ML03-Q04",
        "question": "Why does the Transformer use positional encoding?",
        "expected_topics": [
            "position",
            "positional",
            "sequence",
        ],
        "expected_pages": [],
    },
    {
        "id": "ML03-Q05",
        "question": "How does the Transformer differ from recurrent neural networks?",
        "expected_topics": [
            "recurrent",
            "parallel",
            "sequence",
        ],
        "expected_pages": [],
    },
    {
        "id": "ML03-Q06",
        "question": "What is the purpose of residual connections and layer normalization?",
        "expected_topics": [
            "residual",
            "normalization",
            "layer",
        ],
        "expected_pages": [],
    },
    {
        "id": "ML03-Q07",
        "question": "What are the limitations of self-attention?",
        "expected_topics": [
            "attention",
            "complexity",
            "sequence",
        ],
        "expected_pages": [],
    },
    {
        "id": "ML03-Q08",
        "question": "What training objective does the original Transformer use?",
        "expected_topics": [
            "training",
            "translation",
            "optimization",
        ],
        "expected_pages": [],
    },
    {
        "id": "ML03-Q09",
        "question": "How is attention scaled in scaled dot-product attention?",
        "expected_topics": [
            "dot",
            "product",
            "dimension",
            "square",
        ],
        "expected_pages": [],
    },
    {
        "id": "ML03-Q10",
        "question": "What are the main experimental findings of the paper?",
        "expected_topics": [
            "results",
            "translation",
            "BLEU",
        ],
        "expected_pages": [],
    },
]


OUTPUT_DIR = Path("evaluation/results")
OUTPUT_FILE = OUTPUT_DIR / "retrieval_baseline.csv"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []

    print("=" * 80)
    print("SCHOLARSPACE RETRIEVAL BASELINE")
    print("Paper:", PAPER_ID, "-", TOPIC)
    print("=" * 80)

    for item in QUESTIONS:
        question = item["question"]

        print(f"\n[{item['id']}] {question}")

        start = time.perf_counter()

        results = retrieve_chunks(
            question,
            paper_id=PAPER_ID,
        )

        elapsed = time.perf_counter() - start

        documents = (results.get("documents") or [[]])[0] or []
        metadatas = (results.get("metadatas") or [[]])[0] or []
        distances = (results.get("distances") or [[]])[0] or []

        for rank, (document, metadata, distance) in enumerate(
            zip(documents, metadatas, distances),
            start=1,
        ):
            metadata = metadata or {}

            page = metadata.get(
                "page_label",
                metadata.get("page", "Unknown"),
            )

            topics = [
                term
                for term in item["expected_topics"]
                if term.lower() in document.lower()
            ]

            print(
                f"  Rank {rank} | Page {page} "
                f"| Distance {distance:.4f}"
            )
            print(" ", document[:220].replace("\n", " "))

            rows.append(
                {
                    "question_id": item["id"],
                    "question": question,
                    "paper_id": PAPER_ID,
                    "rank": rank,
                    "page": page,
                    "distance": distance,
                    "matched_terms": "; ".join(topics),
                    "matched_term_count": len(topics),
                    "expected_pages": "; ".join(
                        map(str, item["expected_pages"])
                    ),
                    "passage": document,
                    "retrieval_seconds": round(elapsed, 3),
                }
            )

        if not documents:
            print("  WARNING: No passages retrieved.")

        print(f"  Retrieved: {len(documents)} passages")
        print(f"  Retrieval time: {elapsed:.3f}s")

    fieldnames = [
        "question_id",
        "question",
        "paper_id",
        "rank",
        "page",
        "distance",
        "matched_terms",
        "matched_term_count",
        "expected_pages",
        "passage",
        "retrieval_seconds",
    ]

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("\n" + "=" * 80)
    print("EVALUATION COMPLETE")
    print("Questions:", len(QUESTIONS))
    print("Passages recorded:", len(rows))
    print("CSV:", OUTPUT_FILE.resolve())
    print("=" * 80)


if __name__ == "__main__":
    main()
