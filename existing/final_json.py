import pandas as pd
import json

# Load OpenAlex verification CSV
df = pd.read_csv("/home/aditya/Research_Assistant/data/metadata/openalex_verification.csv")

# Remove verification-only columns
df = df.drop(
    columns=[
        "openalex_title",
        "match_score",
        "status"
    ]
)

# Rename column
df = df.rename(columns={
    "title": "paper"
})

# Create JSON structure
papers = {}

for _, row in df.iterrows():

    papers[row["paper_id"]] = {
        "paper": row["paper"],
        "pdf_filename": row["pdf_filename"],
        "domain": row["domain"],
        "metadata": {
            "year": row["year"],
            "doi": row["doi"],
            "openalex_id": row["openalex_id"],
            "source": "OpenAlex"
        }
    }

# Save JSON
with open("/home/aditya/Research_Assistant/data/metadata/papers.json", "w", encoding="utf-8") as f:
    json.dump(papers, f, indent=4, ensure_ascii=False)

print(f"Created papers.json with {len(papers)} papers.")