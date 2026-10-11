import csv
from pathlib import Path


# ============================================================
# FILES
# ============================================================

INPUT_FILE = "data/metadata/openalex_verification.csv"
OUTPUT_FILE = "data/metadata/openalex_verification.csv"


# ============================================================
# CORRECT ML08 METADATA
# ============================================================

ML08_DATA = {
    "openalex_id": "",
    "openalex_title": "",
    "authors": (
        "John Schulman; Filip Wolski; "
        "Prafulla Dhariwal; Alec Radford; Oleg Klimov"
    ),
    "year": "2017",
    "doi": "https://doi.org/10.48550/arXiv.1707.06347",
    "url": "https://arxiv.org/abs/1707.06347",
    "match_score": "1.000",
    "status": "VERIFIED_EXTERNAL",
}


# ============================================================
# MAIN
# ============================================================

def main():

    input_path = Path(INPUT_FILE)
    output_path = Path(OUTPUT_FILE)

    if not input_path.exists():
        raise FileNotFoundError(
            f"File not found: {input_path}"
        )

    # --------------------------------------------------------
    # READ EXISTING CSV
    # --------------------------------------------------------

    with open(
        input_path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)
        rows = list(reader)
        fieldnames = reader.fieldnames


    # --------------------------------------------------------
    # FIND ML08
    # --------------------------------------------------------

    found = False

    for row in rows:

        if row["paper_id"] == "ML08":

            found = True

            print("Found ML08.")
            print(
                "Old OpenAlex title:",
                row["openalex_title"]
            )

            # Keep the original project-controlled
            # information unchanged.

            row["openalex_id"] = ML08_DATA[
                "openalex_id"
            ]

            row["openalex_title"] = ML08_DATA[
                "openalex_title"
            ]

            row["authors"] = ML08_DATA[
                "authors"
            ]

            row["year"] = ML08_DATA[
                "year"
            ]

            row["doi"] = ML08_DATA[
                "doi"
            ]

            row["url"] = ML08_DATA[
                "url"
            ]

            row["match_score"] = ML08_DATA[
                "match_score"
            ]

            row["status"] = ML08_DATA[
                "status"
            ]

            break


    if not found:

        raise ValueError(
            "ML08 was not found in the verification CSV."
        )


    # --------------------------------------------------------
    # WRITE UPDATED CSV
    # --------------------------------------------------------

    with open(
        output_path,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)


    print()
    print("=" * 60)
    print("ML08 UPDATED")
    print("=" * 60)

    print(
        "Title: Proximal Policy Optimization Algorithms"
    )

    print(
        "Source: arXiv"
    )

    print(
        "DOI: 10.48550/arXiv.1707.06347"
    )

    print(
        "Other 36 rows: unchanged"
    )

    print()
    print(
        f"Updated file: {output_path}"
    )


if __name__ == "__main__":
    main()