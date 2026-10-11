from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


PDF_PATH = Path("data/raw/papers/attention_is_all_you_need.pdf")


# 1. Load the PDF
loader = PyPDFLoader(str(PDF_PATH))
documents = loader.load()

print("Number of pages:", len(documents))


# 2. Create the text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)


# 3. Split the documents into chunks
chunks = text_splitter.split_documents(documents)

print("Number of chunks:", len(chunks))


# 4. Inspect the first few chunks
for i, chunk in enumerate(chunks[:5]):

    print(f"\n--- CHUNK {i + 1} ---")

    print("Characters:", len(chunk.page_content))

    print("Metadata:", chunk.metadata)

    print("Text:")
    print(chunk.page_content)