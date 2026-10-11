import csv
import re
from pathlib import Path

from pypdf import PdfReader


# --------------------------------------------------
# Paths
# --------------------------------------------------

PDF_DIR = Path("data/raw/papers")
OUTPUT_FILE = Path("data/metadata/paper_list.csv")


# --------------------------------------------------
# Domain mapping
# --------------------------------------------------

DOMAIN_MAP = {
    "ML": "Machine Learning",
    "CV": "Computer Vision",
    "ROB": "Robotics",
    "RS": "Remote Sensing",
}


# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def extract_first_page_text(pdf_path):
    """Extract text from the first page of a PDF."""
    reader = PdfReader(str(pdf_path))

    if not reader.pages:
        return ""

    return reader.pages[0].extract_text() or ""


def clean_line(line):
    """Clean unnecessary whitespace."""
    return re.sub(r"\s+", " ", line).strip()


def extract_title(text):
    """
    Try to identify the paper title from the first page.

    This is a simple heuristic, not the final PDF
    processing system.
    """

    lines = [clean_line(line) for line in text.splitlines()]
    lines = [line for line in lines if line]

    if not lines:
        return ""

    # Remove obvious non-title lines
    ignored_patterns = [
        r"^arxiv:",
        r"^doi:",
        r"^abstract$",
        r"^keywords?:",
    ]

    candidates = []

    for line in lines[:30]:
        if len(line) < 5:
            continue

        if any(re.search(pattern, line, re.IGNORECASE)
               for pattern in ignored_patterns):
            continue

        # Avoid lines that look like author/email information
        if "@" in line:
            continue

        candidates.append(line)

    if not candidates:
        return ""

    # Usually the title is one of the first substantial lines.
    return candidates[0]


def determine_domain(filename):
    """
    Determine domain from our paper naming convention.

    If the filename does not contain a recognizable prefix,
    the domain is left blank for manual verification.
    """

    name = filename.upper()

    if name.startswith("ML"):
        return DOMAIN_MAP["ML"]

    if name.startswith("CV"):
        return DOMAIN_MAP["CV"]

    if name.startswith("ROB"):
        return DOMAIN_MAP["ROB"]

    if name.startswith("RS"):
        return DOMAIN_MAP["RS"]

    return ""


def generate_paper_id(filename, index):
    """
    Generate a temporary ID.

    Later we can replace this with the exact
    ML01, CV01, ROB01, RS01 mapping.
    """

    domain = filename.upper()

    if domain.startswith("ML"):
        prefix = "ML"
    elif domain.startswith("CV"):
        prefix = "CV"
    elif domain.startswith("ROB"):
        prefix = "ROB"
    elif domain.startswith("RS"):
        prefix = "RS"
    else:
        prefix = "PAPER"

    return f"{prefix}{index:02d}"


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    if not PDF_DIR.exists():
        print(f"PDF directory not found: {PDF_DIR}")
        return

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(PDF_DIR.glob("*.pdf"))

    print(f"Found {len(pdf_files)} PDF files.\n")

    rows = []

    for index, pdf_path in enumerate(pdf_files, start=1):

        print(f"Processing: {pdf_path.name}")

        try:
            text = extract_first_page_text(pdf_path)
            title = extract_title(text)

            row = {
                "paper_id": generate_paper_id(
                    pdf_path.name,
                    index
                ),
                "pdf_filename": pdf_path.name,
                "title": title,
                "domain": determine_domain(
                    pdf_path.name
                ),
            }

            rows.append(row)

            print(f"  Title: {title}")

        except Exception as e:
            print(f"  ERROR: {e}")

            rows.append({
                "paper_id": generate_paper_id(
                    pdf_path.name,
                    index
                ),
                "pdf_filename": pdf_path.name,
                "title": "",
                "domain": determine_domain(
                    pdf_path.name
                ),
            })

    # --------------------------------------------------
    # Write CSV
    # --------------------------------------------------

    fieldnames = [
        "paper_id",
        "pdf_filename",
        "title",
        "domain",
    ]

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)

    print("\n--------------------------------")
    print("Done!")
    print(f"Created: {OUTPUT_FILE}")
    print(f"Papers processed: {len(rows)}")
    print("--------------------------------")


if __name__ == "__main__":
    main()