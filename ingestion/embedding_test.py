
from FlagEmbedding import BGEM3FlagModel

# Load BGE-M3 on the GPU
model = BGEM3FlagModel(
    "BAAI/bge-m3",
    use_fp16=True,
    devices=["cuda:0"],
)

text = [
    "Attention Is All You Need introduced the Transformer architecture."
]

# Generate dense embeddings
result = model.encode(
    text,
    batch_size=1,
    max_length=512,
)

embedding = result["dense_vecs"][0]

print("Embedding shape:", embedding.shape)
print("Embedding dimensions:", len(embedding))
print("First 10 values:", embedding[:10])
