import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from retrieval.paper_search import search_papers

tests = [
    ("attention is all you need", "title"),
    ("vaswani", "author"),
    ("2017", "year"),
    ("remote sensing", "domain"),
    ("transformer", "all"),
]

for query, field in tests:
    results = search_papers(query, field)

    print(f"\nQuery: {query!r} | Field: {field}")
    print(f"Matches: {len(results)}")

    for paper in results[:3]:
        print(
            f"- [{paper['paper_id']}] {paper['title']} "
            f"({paper['year'] or 'Year unknown'})"
        )
        print(f"  PDF available: {paper['pdf_available']}")
