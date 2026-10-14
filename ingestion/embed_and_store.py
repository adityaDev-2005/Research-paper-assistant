import json
import re
from pathlib import Path

import chromadb
from FlagEmbedding import BGEM3FlagModel
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ============================================================
# CONFIGURATION
# ============================================================

PAPERS_PATH = Path("data/metadata/papers.json")
PAPERS_DIR = Path("data/raw/papers")
DB_PATH = "data/vector_db/chroma"

MODEL_NAME = "BAAI/bge-m3"
COLLECTION_NAME = "research_papers_bge_m3_clean"

EMBED_BATCH_SIZE = 4
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_LENGTH = 512

# First run with True to inspect filtering.
# Change to False only after reviewing the dry-run output.
DRY_RUN = False

# Print examples of chunks that will be excluded.
SHOW_FILTERED_EXAMPLES = True


# ============================================================
# BIBLIOGRAPHY FILTERING
# ============================================================

def is_reference_heading(line):
    """
    Identify likely bibliography section headings.
    """
    text = re.sub(r"\s+", " ", line.strip()).lower()
    text = re.sub(r"^[\d.]+\s*", "", text)
    text = text.strip(" :.-")

    return text in {
        "references",
        "bibliography",
        "works cited",
        "literature cited",
        "references and notes",
        "references cited",
    }


def find_reference_start(documents):
    """
    Find the first page that appears to begin a bibliography.

    PyPDFLoader's 'page' metadata is zero-based.
    Returns None when no reliable heading is found.

    This deliberately uses a conservative heading check instead
    of assuming that every paper's references start on the same page.
    """
    for document in documents:
        lines = document.page_content.splitlines()
        page = document.metadata.get("page")

        for index, line in enumerate(lines):
            if is_reference_heading(line):
                # Avoid treating an isolated mention of "References"
                # in the main text as a section heading.
                nearby_text = "\n".join(lines[index + 1:index + 5]).strip()

                if len(nearby_text) >= 40:
                    return page

    return None


def filter_reference_pages(documents):
    """
    Remove pages starting at a detected References/Bibliography
    heading, including all subsequent pages.

    Returns:
        filtered_documents, reference_start_page
    """
    reference_start_page = find_reference_start(documents)

    if reference_start_page is None:
        return documents, None

    filtered_documents = [
        document
        for document in documents
        if document.metadata.get("page", -1) < reference_start_page
    ]

    return filtered_documents, reference_start_page


# ============================================================
# 1. LOAD PAPER METADATA
# ============================================================

with PAPERS_PATH.open("r", encoding="utf-8") as file:
    papers = json.load(file)

print("Papers listed in metadata:", len(papers))
print("Target collection:", COLLECTION_NAME)
print("Dry-run mode:", DRY_RUN)


# ============================================================
# 2. CONFIGURE THE CHUNKER
# ============================================================

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
)

total_chunks = 0
total_filtered_pages = 0
failed_papers = []
paper_chunks = {}
filtered_examples = []


# ============================================================
# 3. LOAD, FILTER, AND CHUNK PAPERS
# ============================================================

print("\nLoading PDFs and filtering bibliography pages...\n")

for paper_id, paper in papers.items():
    pdf_path = PAPERS_DIR / paper["pdf_filename"]

    try:
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        documents = PyPDFLoader(str(pdf_path)).load()

        filtered_documents, reference_start_page = (
            filter_reference_pages(documents)
        )

        removed_pages = len(documents) - len(filtered_documents)
        total_filtered_pages += removed_pages

        if reference_start_page is None:
            print(
                f"WARNING: {paper_id}: no bibliography heading detected. "
                "All pages retained."
            )
        else:
            print(
                f"{paper_id}: bibliography begins at PDF page "
                f"{reference_start_page + 1}; "
                f"excluded {removed_pages} page(s)."
            )

        chunks = splitter.split_documents(filtered_documents)

        for chunk in chunks:
            chunk.metadata["paper_id"] = paper_id

        paper_chunks[paper_id] = {
            "paper": paper,
            "pdf_path": pdf_path,
            "documents": documents,
            "chunks": chunks,
        }

        total_chunks += len(chunks)

        print(
            f"  Pages: {len(documents)} -> {len(filtered_documents)}; "
            f"chunks retained: {len(chunks)}"
        )

    except Exception as error:
        failed_papers.append((paper_id, str(error)))
        print(f"FAILED: {paper_id} | {error}")


# ============================================================
# 4. DRY-RUN REPORT
# ============================================================

print("\n========== FILTERING SUMMARY ==========")
print("Papers in metadata:", len(papers))
print("Papers loaded successfully:", len(paper_chunks))
print("Papers failed:", len(failed_papers))
print("Bibliography pages excluded:", total_filtered_pages)
print("Chunks remaining after filtering:", total_chunks)

if SHOW_FILTERED_EXAMPLES:
    print(
        "\nNote: inspect a few known bibliography pages manually "
        "before disabling dry-run."
    )

if failed_papers:
    print("\nFailed papers:")
    for paper_id, error in failed_papers:
        print(f"  {paper_id}: {error}")


if DRY_RUN:
    print("\nDRY RUN COMPLETE.")
    print("No embedding model was loaded.")
    print("No ChromaDB collection was created or modified.")
    print("Review the filtering logic before enabling ingestion.")
    raise SystemExit(0)


# ============================================================
# 5. INITIALIZE THE EMBEDDING MODEL
# ============================================================

print("\nLoading BGE-M3 on GPU...")

model = BGEM3FlagModel(
    MODEL_NAME,
    use_fp16=True,
    devices=["cuda:0"],
)


# ============================================================
# 6. INITIALIZE THE CLEAN CHROMADB COLLECTION
# ============================================================

client = chromadb.PersistentClient(path=DB_PATH)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)

# Never overwrite or mix with an existing collection.
if collection.count() > 0:
    raise RuntimeError(
        f"The target collection '{COLLECTION_NAME}' already contains "
        f"{collection.count()} records. Nothing was added. "
        "Inspect the collection before proceeding."
    )


# ============================================================
# 7. EMBED AND STORE CHUNKS
# ============================================================

failed_papers = []
stored_chunks = 0

for paper_id, data in paper_chunks.items():
    paper = data["paper"]
    pdf_path = data["pdf_path"]
    chunks = data["chunks"]

    try:
        for start in range(0, len(chunks), EMBED_BATCH_SIZE):
            batch = chunks[start:start + EMBED_BATCH_SIZE]
            texts = [chunk.page_content for chunk in batch]

            result = model.encode(
                texts,
                batch_size=len(texts),
                max_length=MAX_LENGTH,
            )

            embeddings = result["dense_vecs"].tolist()

            metadatas = []
            ids = []

            for index, chunk in enumerate(batch, start=start):
                meta = chunk.metadata

                item = {
                    "paper_id": paper_id,
                    "paper_title": paper["paper"],
                    "domain": paper["domain"],
                    "source": str(pdf_path),
                    "chunk_index": index,
                }

                for key in ("page", "page_label", "total_pages"):
                    value = meta.get(key)

                    if isinstance(value, (str, int, float, bool)):
                        item[key] = value

                year = paper.get("metadata", {}).get("year")

                if isinstance(year, (int, float)):
                    item["year"] = int(year)

                metadatas.append(item)
                ids.append(f"{paper_id}_chunk_{index:04d}")

            collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
            )

            stored_chunks += len(batch)

        print(f"STORED: {paper_id} | {len(chunks)} chunks")

    except Exception as error:
        failed_papers.append((paper_id, str(error)))
        print(f"FAILED DURING STORAGE: {paper_id} | {error}")


# ============================================================
# 8. FINAL REPORT
# ============================================================

print("\n========== EMBEDDING SUMMARY ==========")
print("Target collection:", COLLECTION_NAME)
print("Papers in metadata:", len(papers))
print("Papers prepared:", len(paper_chunks))
print("Papers failed:", len(failed_papers))
print("Chunks attempted:", stored_chunks)
print("Records currently in ChromaDB:", collection.count())
print("Database path:", DB_PATH)

if failed_papers:
    print("\nFailed papers:")
    for paper_id, error in failed_papers:
        print(f"  {paper_id}: {error}")

if not failed_papers and stored_chunks == collection.count():
    print("\nSUCCESS: All prepared chunks are stored.")
else:
    print(
        "\nWARNING: Some papers may have failed. "
        "Review the report before using this collection."
    )