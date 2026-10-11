import json
import os


# Path to papers.json
JSON_PATH = "/home/aditya/Research_Assistant/data/metadata/papers.json"


def load_papers():
    """Load all papers from papers.json."""
    
    with open(JSON_PATH, "r", encoding="utf-8") as file:
        papers = json.load(file)

    return papers


# def search_paper(query, papers):
#     """Search for papers matching the user's query."""

#     query = query.lower().strip()

#     results = []

#     for paper_id, paper in papers.items():

#         title = paper["paper"].lower()
#         domain = paper["domain"].lower()

#         # Check whether query appears in title or domain
#         if query in title or query in domain:
#             results.append((paper_id, paper))

#     return results


# def search_paper(query, papers):
#     """Search for papers matching the user's query."""

#     # Convert user query to lowercase
#     query = query.lower().strip()

#     results = []

#     for paper_id, paper in papers.items():

#         # Convert paper metadata to lowercase
#         title = paper["paper"].lower()
#         domain = paper["domain"].lower()

#         # Compare lowercase query with lowercase metadata
#         if query in title or query in domain:
#             results.append((paper_id, paper))

#     return results


def search_paper(query, papers):
    """Search for papers matching the user's query."""

    query = query.lower().strip()

    results = []

    for paper_id, paper in papers.items():

        title = paper["paper"].lower()
        domain = paper["domain"].lower()
        pdf_filename = paper["pdf_filename"].lower()

        if (
            query in title
            or query in domain
            or query in pdf_filename
        ):
            results.append((paper_id, paper))

    return results


def display_results(results):
    """Display the retrieved papers."""

    if not results:
        print("\nNo matching paper found.")
        return

    print(f"\nFound {len(results)} paper(s):\n")

    for paper_id, paper in results:

        print(f"Paper ID : {paper_id}")
        print(f"Title    : {paper['paper']}")
        print(f"Domain   : {paper['domain']}")
        print(f"Year     : {paper['metadata']['year']}")
        print(f"DOI      : {paper['metadata']['doi']}")
        print(f"PDF      : {paper['pdf_filename']}")
        print("-" * 60)


def main():

    papers = load_papers()

    print("Research Paper Metadata Search")
    print("=" * 40)

    query = input("\nEnter paper name or keyword: ")

    results = search_paper(query, papers)

    display_results(results)


if __name__ == "__main__":
    main()