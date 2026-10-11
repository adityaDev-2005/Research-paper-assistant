
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAPERS_PATH = PROJECT_ROOT / "data" / "metadata" / "papers.json"


def load_papers():
    """Load the existing paper metadata."""
    with PAPERS_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    # Your current papers.json stores papers in a dictionary.
    if isinstance(data, dict):
        return list(data.values())

    if isinstance(data, list):
        return data

    raise ValueError("Unsupported papers.json structure")


def recommend_papers(domain=None, year_from=None, year_to=None, limit=5):
    """
    Recommend papers using available metadata.

    Domain and publication year are filters, not measures of
    paper quality or reading difficulty.
    """
    papers = load_papers()
    results = []

    for item in papers:
        metadata = item.get("metadata", {})
        paper_domain = item.get("domain", "Unknown")
        year = metadata.get("year")

        if domain and domain.lower() not in paper_domain.lower():
            continue

        if year_from is not None and (
            not isinstance(year, int) or year < year_from
        ):
            continue

        if year_to is not None and (
            not isinstance(year, int) or year > year_to
        ):
            continue

        results.append({
            "title": item.get("paper", "Untitled"),
            "domain": paper_domain,
            "year": year,
            "authors": metadata.get("authors", []),
            "url": metadata.get("url"),
            "doi": metadata.get("doi"),
            "pdf_filename": item.get("pdf_filename"),
        })

    return results[:max(1, min(limit, 20))]
