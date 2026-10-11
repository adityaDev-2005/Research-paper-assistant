
from FlagEmbedding import BGEM3FlagModel
import chromadb

DB_PATH = "data/vector_db/chroma"
COLLECTION_NAME = "research_papers_bge_m3"

# Load the existing embedding model
model = BGEM3FlagModel(
    "BAAI/bge-m3",
    use_fp16=True,
    devices=["cuda:0"],
)

# Connect to the existing database
client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_collection(name=COLLECTION_NAME)

print("Stored chunks:", collection.count())

# Ask a question
question = "What architecture does Attention Is All You Need introduce?"

# Convert the question into an embedding
query_result = model.encode(
    [question],
    batch_size=1,
    max_length=512,
)

query_embedding = query_result["dense_vecs"][0].tolist()

# Retrieve the 5 most relevant chunks from ML03
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5,
    where={"paper_id": "ML03"},
    include=["documents", "metadatas", "distances"],
)

# Display retrieved passages and their sources
print("\nQuestion:", question)

for i, (document, metadata, distance) in enumerate(
    zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ),
    start=1,
):
    print(f"\n--- Result {i} ---")
    print("Paper ID:", metadata.get("paper_id"))
    print("Page:", metadata.get("page_label", metadata.get("page")))
    print("Distance:", round(distance, 4))
    print("Text:", document[:800])
