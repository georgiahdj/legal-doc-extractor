import requests

OLLAMA_HOST = "https://audacity-exploring-nervous.ngrok-free.dev"

payload = {
    "model": "llava",
    "prompt": "Extract contract number from: ΑΡΙΘΜΟΣ 11.924. Return JSON only.",
    "stream": False
}

r = requests.post(
    f"{OLLAMA_HOST}/api/generate",
    json=payload,
    timeout=120,
    headers={"ngrok-skip-browser-warning": "true"}
)

print(r.status_code)
print(r.text[:500])