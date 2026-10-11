import csv
from pathlib import Path
from pypdf import PdfReader


INPUT_FILE = "data/metadata/paper_list_final_37.csv"
PDF_DIR = Path("data/raw/papers")


def main():

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        papers = list(csv.DictReader(file))


    print(f"Found {len(papers)} papers.")


    for index, paper in enumerate(
        papers,
        start=1
    ):

        pdf_path = PDF_DIR / paper["pdf_filename"]

        print()
        print("=" * 70)
        print(
            f"[{index}/{len(papers)}] "
            f"{paper['paper_id']}"
        )

        print(
            f"File: {paper['pdf_filename']}"
        )

        print(
            f"Expected title: {paper['title']}"
        )


        # ----------------------------------------------------
        # CHECK FILE
        # ----------------------------------------------------

        if not pdf_path.exists():

            print("PDF STATUS: FILE NOT FOUND")
            continue


        try:

            reader = PdfReader(
                str(pdf_path)
            )

            print(
                f"Pages: {len(reader.pages)}"
            )


            # ------------------------------------------------
            # PDF DOCUMENT METADATA
            # ------------------------------------------------

            metadata = reader.metadata

            if metadata:

                print("\nPDF metadata:")

                print(
                    "Title:",
                    metadata.title
                )

                print(
                    "Author:",
                    metadata.author
                )

                print(
                    "Subject:",
                    metadata.subject
                )


            # ------------------------------------------------
            # FIRST PAGE TEXT
            # ------------------------------------------------

            if len(reader.pages) > 0:

                text = reader.pages[0].extract_text()

                if text:

                    print(
                        "\nFirst-page text "
                        "(first 1500 characters):"
                    )

                    print(
                        text[:1500]
                    )

                else:

                    print(
                        "\nNo text extracted "
                        "from first page."
                    )


        except Exception as error:

            print(
                "PDF ERROR:",
                error
            )


if __name__ == "__main__":
    main()