from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader


PDF_PATH = Path("/home/aditya/Research_Assistant/data/raw/papers/attention_is_all_you_need.pdf")

loader = PyPDFLoader(str(PDF_PATH))

documents = loader.load()

print("Number of pages:",len(documents))


for i,doc in enumerate(documents): # returns the index and the document at that index
    print(f"\n---PAGE {i+1}---")
    print("Characters:",len(doc.page_content))
    print("Metadata:",doc.metadata)
    print("Preview")
    print(doc.page_content[:300].replace("\n", " "))

# print("\n---FIRST PAGE---")
# print(documents[0].page_content[:2000])

# print("\n---METADATA---")
# print(documents[0].metadata)