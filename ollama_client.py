import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

def consultar_ollama(prompt, modelo="llama3"):
    payload = {
        "model": modelo,
        "prompt": prompt,
        "stream": False
    }

    r = requests.post(OLLAMA_URL, json=payload, timeout=300)
    r.raise_for_status()
    return r.json()["response"]