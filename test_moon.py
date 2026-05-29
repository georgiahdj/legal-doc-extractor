import requests

text = """ΑΡΙΘΜΟΣ 11.924
ΜΑΡΙΑ ΜΑΣΟΥΡΟΥ-ΤΣΑΝΑΚΑ
οδό Δημοκρίτου αρ.4
Αθανάσιος Αλμπάνης, ΑΔΤ Ν 245733/1984"""

payload = {
    "model": "moondream",
    "prompt": f"Extract contract_number and notary name from this text. Return only JSON:\n\n{text}",
    "stream": False
}

r = requests.post("http://localhost:11434/api/generate", json=payload, timeout=60)
print(r.json().get("response", "No response"))