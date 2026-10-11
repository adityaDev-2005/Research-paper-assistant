
import json
from pathlib import Path

PAPERS_PATH = Path("data/metadata/papers.json")
PDF_DIR = Path("data/raw/papers")


def load_papers():
    with PAPERS_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def search_papers(query, papers):
    """Search paper metadata by title, author, year, domain, or keyword."""
    query = query.strip().lower()
    matches = []

    if not query:
        return matches

    for paper_id, paper in papers.items():
        metadata = paper.get("metadata", {})
        authors = metadata.get("authors", [])

        # Support authors represented as either a list or a string.
        if isinstance(authors, list):
            author_text = " ".join(str(author) for author in authors)
        else:
            author_text = str(authors)

        searchable_text = " ".join([
            str(paper.get("paper", "")),
            str(paper.get("pdf_filename", "")),
            str(paper.get("domain", "")),
            author_text,
            str(metadata.get("year", "")),
            str(metadata.get("doi", "")),
            str(metadata.get("url", "")),
            str(metadata.get("abstract", "")),
            str(metadata.get("keywords", "")),
        ]).lower()

        if query in searchable_text:
            matches.append((paper_id, paper))

    return matches


def display_results(matches):
    if not matches:
        print("\nNo matching papers found.")
        return

    print(f"\nFound {len(matches)} matching paper(s):")

    for paper_id, paper in matches:
        metadata = paper.get("metadata", {})
        pdf_path = PDF_DIR / paper.get("pdf_filename", "")

        print("\n" + "=" * 60)
        print("Paper ID:", paper_id)
        print("Title:", paper.get("paper", "Unknown"))
        print("Domain:", paper.get("domain", "Unknown"))
        print("Authors:", metadata.get("authors", "Not available"))
        print("Year:", metadata.get("year", "Not available"))
        print("PDF available:", pdf_path.is_file())
        print("PDF path:", pdf_path if pdf_path.is_file() else "Not found")
        print("URL:", metadata.get("url") or "Not available")


def main():
    papers = load_papers()

    print("Research Paper Discovery")
    print("Search by title, author, year, domain, or keyword.")
    print("Enter 'exit' to quit.")

    while True:
        query = input("\nSearch: ").strip()

        if query.lower() == "exit":
            break

        display_results(search_papers(query, papers))


if __name__ == "__main__":
    main()
