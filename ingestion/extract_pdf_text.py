import json
import os
import pymupdf


# Project root directory
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

# Input files
JSON_PATH = os.path.join(
    BASE_DIR,
    "data",
    "metadata",
    "papers.json"
)

PDF_DIR = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "papers"
)

# Output directory
TEXT_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "text"
)


def load_papers():
    """Load paper metadata from papers.json."""

    with open(JSON_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def extract_text(pdf_path):
    """Extract text from PDF while preserving page boundaries."""

    document = pymupdf.open(pdf_path)

    pages = []

    for page_number, page in enumerate(document, start=1):

        text = page.get_text()

        page_text = (
            f"\n\n===== PAGE {page_number} =====\n\n"
            f"{text}"
        )

        pages.append(page_text)

    document.close()

    return "".join(pages)


def main():

    papers = load_papers()

    os.makedirs(TEXT_DIR, exist_ok=True)

    successful = 0
    failed = 0

    for paper_id, paper in papers.items():

        pdf_filename = paper["pdf_filename"]

        pdf_path = os.path.join(
            PDF_DIR,
            pdf_filename
        )

        output_path = os.path.join(
            TEXT_DIR,
            f"{paper_id}.txt"
        )

        print(
            f"Processing {paper_id}: "
            f"{pdf_filename}"
        )

        if not os.path.exists(pdf_path):
            print("  ERROR: PDF not found")
            failed += 1
            continue

        try:

            text = extract_text(pdf_path)

            with open(
                output_path,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(text)

            print(f"  Saved: {output_path}")

            successful += 1

        except Exception as error:

            print(f"  ERROR: {error}")
            failed += 1

    print("\n" + "=" * 50)
    print("PDF TEXT EXTRACTION COMPLETE")
    print("=" * 50)

    print(f"Successful : {successful}")
    print(f"Failed     : {failed}")
    print(f"Total      : {len(papers)}")


if __name__ == "__main__":
    main()