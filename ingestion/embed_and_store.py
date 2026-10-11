
import json
from pathlib import Path

import chromadb
from FlagEmbedding import BGEM3FlagModel
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Paths
PAPERS_PATH = Path("data/metadata/papers.json")
PAPERS_DIR = Path("data/raw/papers")
DB_PATH = "data/vector_db/chroma"

# Model and batch settings
MODEL_NAME = "BAAI/bge-m3"
EMBED_BATCH_SIZE = 4
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_LENGTH = 512

# 1. Load paper metadata
with PAPERS_PATH.open("r", encoding="utf-8") as file:
    papers = json.load(file)

# 2. Initialize the embedding model on the GPU
print("Loading BGE-M3...")
model = BGEM3FlagModel(
    MODEL_NAME,
    use_fp16=True,
    devices=["cuda:0"],
)

# 3. Initialize persistent ChromaDB
client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_or_create_collection(
    name="research_papers_bge_m3",
    metadata={"hnsw:space": "cosine"},
)

# Avoid accidentally mixing with a previous partial run.
if collection.count() > 0:
    raise RuntimeError(
        f"The collection already contains {collection.count()} records. "
        "Use a new collection name or inspect/remove the old collection "
        "before running this script again."
    )

# 4. Configure the chunker
splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
)

total_chunks = 0
failed_papers = []

# 5. Load, chunk, embed, and store each paper
for paper_id, paper in papers.items():
    pdf_path = PAPERS_DIR / paper["pdf_filename"]

    try:
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        documents = PyPDFLoader(str(pdf_path)).load()
        chunks = splitter.split_documents(documents)

        # Add paper ID to each chunk while preserving page metadata.
        for chunk in chunks:
            chunk.metadata["paper_id"] = paper_id

        # Process small batches to manage GPU memory.
        for start in range(0, len(chunks), EMBED_BATCH_SIZE):
            batch = chunks[start:start + EMBED_BATCH_SIZE]
            texts = [chunk.page_content for chunk in batch]

            result = model.encode(
                texts,
                batch_size=EMBED_BATCH_SIZE,
                max_length=MAX_LENGTH,
            )

            embeddings = result["dense_vecs"].tolist()

            # Chroma metadata supports scalar values, not None or lists.
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

                # Keep page details from the PDF loader.
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

            total_chunks += len(batch)

        print(
            f"{paper_id}: {len(documents)} pages, "
            f"{len(chunks)} chunks stored"
        )

    except Exception as error:
        failed_papers.append((paper_id, str(error)))
        print(f"FAILED: {paper_id} | {error}")

# 6. Report results
print("\n========== EMBEDDING SUMMARY ==========")
print("Papers in metadata:", len(papers))
print("Papers failed:", len(failed_papers))
print("Chunks processed this run:", total_chunks)
print("Records in ChromaDB:", collection.count())
print("Database path:", DB_PATH)

if failed_papers:
    print("\nFailed papers:")
    for paper_id, error in failed_papers:
        print(f"{paper_id}: {error}")

if not failed_papers and total_chunks == collection.count():
    print("\nSUCCESS: All chunks embedded and stored.")
else:
    print("\nWARNING: Check the counts and failed papers before proceeding.")
