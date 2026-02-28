import requests

OLLAMA_URL = "http://localhost:11434/api/chat"

def ask_phi(messages):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "phi3:mini",
            "messages": messages,
            "stream": False
        }
    )

    return response.json()["message"]["content"]
