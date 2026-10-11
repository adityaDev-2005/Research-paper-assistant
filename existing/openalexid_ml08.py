import requests

doi = "https://doi.org/10.48550/arXiv.1707.06347"

url = f"https://api.openalex.org/works/{doi}"

response = requests.get(
    url,
    headers={
        "Authorization": f"Bearer YOUR_OPENALEX_API_KEY"
    }
)

data = response.json()

print("Title:", data.get("title"))
print("OpenAlex ID:", data.get("id"))