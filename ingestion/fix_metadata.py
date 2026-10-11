from pathlib import Path
import pandas as pd

CSV_PATH = Path("data/metadata/openalex_verification.csv")

df = pd.read_csv(CSV_PATH)

# Verified information for the original papers
corrections = {
    "ML01": {
        "year": 2014,
        "doi": "https://doi.org/10.48550/arXiv.1406.2661",
        "url": "https://arxiv.org/abs/1406.2661",
    },
    "ML03": {
        "year": 2017,
        "doi": "https://doi.org/10.48550/arXiv.1706.03762",
        "url": "https://arxiv.org/abs/1706.03762",
    },
}

for paper_id, values in corrections.items():
    mask = df["paper_id"] == paper_id

    if mask.sum() != 1:
        raise ValueError(
            f"Expected exactly one row for {paper_id}, "
            f"found {mask.sum()}"
        )

    for column, value in values.items():
        df.loc[mask, column] = value

    # The old OpenAlex match was not reliable.
    # Remove its identifier rather than preserve a wrong link.
    if "openalex_id" in df.columns:
        df.loc[mask, "openalex_id"] = ""

    if "status" in df.columns:
        df.loc[mask, "status"] = "MANUALLY_VERIFIED"

df.to_csv(CSV_PATH, index=False)

print("Corrected metadata:")
print(
    df[df["paper_id"].isin(corrections)]
    [["paper_id", "title", "year", "doi", "url"]]
    .to_string(index=False)
)
