
import json
from pathlib import Path
from collections import Counter

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

PAPERS_PATH = Path("data/metadata/papers.json")
PAPERS_DIR = Path("data/raw/papers")

# Step 1: Load metadata for all papers
with PAPERS_PATH.open("r", encoding="utf-8") as file:
    papers = json.load(file)

# Step 2: Configure the chunker (same settings as before)
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)

all_chunks = []
chunk_counts = Counter()
failed_papers = []

# Step 3: Process every paper
for paper_id, paper in papers.items():
    pdf_path = PAPERS_DIR / paper["pdf_filename"]

    try:
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Load PDF pages
        documents = PyPDFLoader(str(pdf_path)).load()

        # Split pages into chunks
        chunks = splitter.split_documents(documents)

        # Step 4: Attach the paper ID to every chunk
        for chunk in chunks:
            chunk.metadata["paper_id"] = paper_id

        # Collect chunks and record the count
        all_chunks.extend(chunks)
        chunk_counts[paper_id] = len(chunks)

        print(
            f"{paper_id}: {paper['paper']} | "
            f"Pages: {len(documents)} | Chunks: {len(chunks)}"
        )

    except Exception as error:
        failed_papers.append((paper_id, str(error)))
        print(f"FAILED: {paper_id} | {error}")

# Step 5: Summarize the results
print("\n========== INGESTION SUMMARY ==========")
print("Papers in metadata:", len(papers))
print("Papers processed:", len(chunk_counts))
print("Papers failed:", len(failed_papers))
print("Total chunks:", len(all_chunks))

if failed_papers:
    print("\nFailed papers:")
    for paper_id, error in failed_papers:
        print(f"{paper_id}: {error}")

# Step 6: Validate the collected chunks
chunk_ids = Counter(
    chunk.metadata["paper_id"] for chunk in all_chunks
)

print("\nChunk counts by paper ID:")
for paper_id in papers:
    print(f"{paper_id}: {chunk_ids[paper_id]}")

if len(chunk_counts) == len(papers) and not failed_papers:
    print("\nSUCCESS: All papers processed.")
else:
    print("\nWARNING: Some papers were not processed successfully.")

# Inspect one chunk
if all_chunks:
    print("\nFirst chunk metadata:")
    print(json.dumps(all_chunks[0].metadata, indent=2))
    print("\nFirst 300 characters:")
    print(all_chunks[0].page_content[:300])
