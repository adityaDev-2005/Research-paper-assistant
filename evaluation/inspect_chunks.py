
import chromadb

client = chromadb.PersistentClient(path="data/vector_db/chroma")
collection = client.get_collection(name="research_papers_bge_m3")

# chunk_ids = [
#     "CV01_chunk_0000",
#     "CV01_chunk_0089",
#     "CV01_chunk_0134",
#     "ML03_chunk_0006",
#     "ML03_chunk_0010",
#     "ML03_chunk_0017",
# ]

chunk_ids = [
    "CV01_chunk_0002",
    "CV01_chunk_0010",
    "ML03_chunk_0021",
    "ML03_chunk_0030",
]

results = collection.get(
    ids=chunk_ids,
    include=["documents", "metadatas"],
)

for chunk_id, document, metadata in zip(
    results["ids"],
    results["documents"],
    results["metadatas"],
):
    print("\n" + "=" * 75)
    print("CHUNK:", chunk_id)
    print("PAPER:", metadata.get("paper_id"))
    print("PAGE:", metadata.get("page_label", metadata.get("page")))
    print("TEXT:\n", document)
