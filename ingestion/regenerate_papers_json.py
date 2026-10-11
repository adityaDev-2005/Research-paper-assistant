
import json
from pathlib import Path

import pandas as pd

CSV_PATH = Path("data/metadata/openalex_verification.csv")
JSON_PATH = Path("data/metadata/papers.json")

# These two records were manually checked against the original arXiv papers.
MANUALLY_VERIFIED = {"ML01", "ML03"}

df = pd.read_csv(CSV_PATH, dtype={"paper_id": str})
required = {"paper_id", "pdf_filename", "title", "year", "doi", "url"}

missing = required - set(df.columns)
if missing:
    raise ValueError(f"Missing required CSV columns: {sorted(missing)}")

if df["paper_id"].duplicated().any():
    duplicates = df.loc[df["paper_id"].duplicated(), "paper_id"].tolist()
    raise ValueError(f"Duplicate paper IDs: {duplicates}")


def clean(value):
    """Convert empty CSV cells to None and trim strings."""
    if pd.isna(value) or str(value).strip() == "":
        return None
    return str(value).strip()


def parse_authors(value):
    """Convert a semicolon-separated author cell into a list."""
    value = clean(value)
    if not value:
        return []

    # The current verification CSV stores authors separated by semicolons.
    return [author.strip() for author in value.split(";") if author.strip()]


papers = {}

for _, row in df.iterrows():
    paper_id = clean(row["paper_id"])
    if not paper_id:
        continue

    year_value = clean(row["year"])
    year = int(float(year_value)) if year_value else None

    # Use the domain in this CSV when available; otherwise infer from ID prefix.
    domain = clean(row["domain"]) if "domain" in df.columns else None
    if not domain:
        prefix_domains = {
            "ML": "Machine Learning",
            "CV": "Computer Vision",
            "RS": "Remote Sensing",
        }
        domain = prefix_domains.get(paper_id[:2], "Unknown")

    source = (
        "Manual verification (arXiv)"
        if paper_id in MANUALLY_VERIFIED
        else "OpenAlex"
    )

    metadata = {
        "authors": parse_authors(row["authors"]) if "authors" in df.columns else [],
        "year": year,
        "doi": clean(row["doi"]),
        "url": clean(row["url"]),
        "openalex_id": (
            None if paper_id in MANUALLY_VERIFIED
            else clean(row["openalex_id"]) if "openalex_id" in df.columns
            else None
        ),
        "source": source,
    }

    papers[paper_id] = {
        "paper": clean(row["title"]),
        "pdf_filename": clean(row["pdf_filename"]),
        "domain": domain,
        "metadata": metadata,
    }

JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
with JSON_PATH.open("w", encoding="utf-8") as file:
    json.dump(papers, file, indent=2, ensure_ascii=False)

print(f"Created {JSON_PATH}")
print(f"Total papers: {len(papers)}")
print("\nManually verified records:")
for paper_id in sorted(MANUALLY_VERIFIED):
    if paper_id in papers:
        print(json.dumps({paper_id: papers[paper_id]}, indent=2))
    else:
        print(f"WARNING: {paper_id} was not found in the CSV.")
