import requests

API_URL = "http://127.0.0.1:8000/explain"

paper_id = "ML03"
level = "beginner"

# Stores actual messages from this session.
history = []

questions = [
    "How does positional encoding work?",
    "Why does it use sine and cosine?",
    "What advantage does that give the Transformer?",
]

for question in questions:
    print(f"\nYou: {question}")

    # Keep recent messages and limit each message's size.
    recent_history = [
        {
            "role": turn["role"],
            "content": turn["content"][:2500],
        }
        for turn in history[-6:]
    ]

    payload = {
        "paper_id": paper_id,
        "question": question,
        "level": level,
        "history": recent_history,
    }

    response = requests.post(API_URL, json=payload, timeout=300)

    if response.status_code != 200:
        print("Request failed:", response.status_code)
        print(response.text)
        break

    data = response.json()
    answer = data["answer"]

    print("\nAssistant:")
    print(answer)

    print("\nSources:")
    for source in data.get("sources", []):
        print(
            f"- Paper {source['paper_id']}, "
            f"page {source['page']}"
        )

    # Save the actual user question and assistant answer.
    history.append({
        "role": "user",
        "content": question,
    })
    history.append({
        "role": "assistant",
        "content": answer,
    })

print("\nConversation test finished.")
print("Messages stored:", len(history))
