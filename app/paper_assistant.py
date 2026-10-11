import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from retrieval.paper_search import search_papers
from ingestion.rag_pipeline import retrieve_chunks, generate_answer


def main():
    print("\n=== Research Paper Assistant ===")

    # Step 1: Search for a paper.
    query = input("\nSearch for a paper: ").strip()

    if not query:
        print("Please enter a search query.")
        return

    papers = search_papers(query, field="all")

    if not papers:
        print("No matching papers found.")
        return

    available_papers = [
        paper for paper in papers if paper["pdf_available"]
    ]

    if not available_papers:
        print("No matching papers have a local PDF.")
        return

    # Step 2: Select a paper.
    print(f"\nFound {len(available_papers)} paper(s):\n")

    for index, paper in enumerate(available_papers, start=1):
        print(
            f"{index}. [{paper['paper_id']}] "
            f"{paper['title']} "
            f"({paper['year'] or 'Year unknown'})"
        )

    try:
        choice = int(input("\nSelect a paper by number: "))
    except ValueError:
        print("Please enter a valid number.")
        return

    if not 1 <= choice <= len(available_papers):
        print("Invalid selection.")
        return

    selected_paper = available_papers[choice - 1]
    paper_id = selected_paper["paper_id"]

    print(f"\nSelected: {selected_paper['title']}")
    print(f"Paper ID: {paper_id}")
    print("\nYou can now ask multiple questions about this paper.")
    print("Type 'exit' or 'quit' to end the session.")

    # Step 3: Keep accepting questions.
    while True:
        question = input("\nYour question: ").strip()

        if question.casefold() in {"exit", "quit"}:
            print("\nResearch session ended.")
            break

        if not question:
            print("Please enter a question.")
            continue

        # Step 4: Retrieve relevant passages.
        try:
            print("\nRetrieving relevant passages...")
            results = retrieve_chunks(
                question,
                paper_id=paper_id,
            )

            documents = results.get("documents", [[]])[0]

            if not documents:
                print("No relevant passages were retrieved.")
                continue

            # Step 5: Generate the answer.
            print("Generating answer...")
            answer, metadatas = generate_answer(
                question,
                results,
            )

            print("\n=== Answer ===\n")
            print(answer)

            print("\n=== Retrieved Sources ===")

            for index, metadata in enumerate(metadatas, start=1):
                page = metadata.get(
                    "page_label",
                    metadata.get("page", "Unknown"),
                )
                print(
                    f"[Source {index}] "
                    f"Paper: {metadata.get('paper_id', 'Unknown')} | "
                    f"Page: {page}"
                )

        except Exception as error:
            print(f"\nAn error occurred: {error}")
            print("You can try asking another question.")


if __name__ == "__main__":
    main()
