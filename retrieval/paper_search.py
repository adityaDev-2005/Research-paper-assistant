
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAPERS_PATH = PROJECT_ROOT / "data" / "metadata" / "papers.json"
PDF_DIR = PROJECT_ROOT / "data" / "raw" / "papers"


def load_papers():
    """Load the canonical paper metadata."""
    with PAPERS_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def search_papers(query="", field="all"):
    """
    Search paper metadata.

    Supported fields:
    all, title, author, year, domain, keyword
    """
    query = str(query).strip().casefold()
    field = field.strip().casefold()

    allowed_fields = {"all", "title", "author", "year", "domain", "keyword"}
    if field not in allowed_fields:
        raise ValueError(f"Unsupported search field: {field}")

    if not query:
        return []

    papers = load_papers()
    matches = []

    for paper_id, paper in papers.items():
        metadata = paper.get("metadata", {})
        authors = metadata.get("authors", [])
        if isinstance(authors, list):
            author_text = " ".join(str(author) for author in authors)
        else:
            author_text = str(authors)

        values = {
            "title": str(paper.get("paper", "")),
            "author": author_text,
            "year": str(metadata.get("year", "")),
            "domain": str(paper.get("domain", "")),
            "keyword": " ".join([
                str(metadata.get("keywords", "")),
                str(metadata.get("abstract", "")),
            ]),
        }

        if field == "all":
            searchable = " ".join(values.values())
        else:
            searchable = values[field]

        if query in searchable.casefold():
            pdf_filename = paper.get("pdf_filename", "")
            pdf_path = PDF_DIR / pdf_filename if pdf_filename else None

            matches.append({
                "paper_id": paper_id,
                "title": paper.get("paper", "Unknown"),
                "domain": paper.get("domain", "Unknown"),
                "authors": authors,
                "year": metadata.get("year"),
                "doi": metadata.get("doi"),
                "url": metadata.get("url"),
                "pdf_filename": pdf_filename,
                "pdf_path": str(pdf_path) if pdf_path else None,
                "pdf_available": bool(pdf_path and pdf_path.is_file()),
            })

    return matches
