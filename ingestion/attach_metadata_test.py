
import json
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

PAPERS_PATH = Path("data/metadata/papers.json")
PAPERS_DIR = Path("data/raw/papers")
PAPER_ID = "ML03"

# Step 1: Load paper metadata
with PAPERS_PATH.open("r", encoding="utf-8") as file:
    papers = json.load(file)

if PAPER_ID not in papers:
    raise KeyError(f"{PAPER_ID} not found in papers.json")

paper = papers[PAPER_ID]
pdf_path = PAPERS_DIR / paper["pdf_filename"]

if not pdf_path.exists():
    raise FileNotFoundError(f"PDF not found: {pdf_path}")

# Step 2: Load the PDF (one Document per page)
documents = PyPDFLoader(str(pdf_path)).load()

# Step 3: Split the pages into smaller chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
chunks = splitter.split_documents(documents)

# Step 4: ADD PAPER METADATA TO EACH CHUNK
for chunk in chunks:
    chunk.metadata["paper_id"] = PAPER_ID

# Step 5: Display results for verification
print("Paper ID:", PAPER_ID)
print("Paper title:", paper["paper"])
print("Pages:", len(documents))
print("Chunks:", len(chunks))

print("\nFirst chunk metadata:")
print(json.dumps(chunks[0].metadata, indent=2, ensure_ascii=False))

print("\nFirst 300 characters of the first chunk:")
print(chunks[0].page_content[:300])
