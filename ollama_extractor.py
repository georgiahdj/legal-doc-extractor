import requests
import base64
import json
import re
import time
import os

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_URL = f"{OLLAMA_HOST}/api/generate"
MODEL = "qwen2.5vl:3b"


def extract_from_text(text: str, prompt: str) -> dict:
    """
    Στέλνει OCR κείμενο στο VLM και παίρνει JSON.
    """
    full_prompt = f"{prompt}\n\nText extracted from document:\n{text}\n\nReturn ONLY valid JSON, no markdown, no explanation."

    payload = {
        "model": MODEL,
        "prompt": full_prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        raw_text = response.json()["response"].strip()

        # Καθαρισμός markdown
        raw_text = re.sub(r'```json\s*', '', raw_text)
        raw_text = re.sub(r'```\s*', '', raw_text)
        raw_text = raw_text.strip()

        # Βρες το JSON μέσα στο text
        start = raw_text.find('{')
        end = raw_text.rfind('}') + 1
        if start >= 0 and end > start:
            raw_text = raw_text[start:end]

        return json.loads(raw_text)

    except json.JSONDecodeError:
        print("Δεν ήταν valid JSON")
        return {}
    except requests.exceptions.Timeout:
        print("Timeout")
        return {}
    except Exception as e:
        print(f"Error: {e}")
        return {}


def extract_from_page(image_bytes: bytes, prompt: str) -> dict:
    """
    Pipeline: εικόνα → OCR preprocessing → VLM → JSON
    """
    from preprocessor import preprocess_for_llm

    print("  OCR + preprocessing...")
    preprocessed = preprocess_for_llm(image_bytes)
    text = preprocessed["clean_text"]
    print(f"  Κείμενο: {len(text)} chars, {preprocessed['total_chunks']} chunks")
    print("  VLM extraction...")
    return extract_from_text(text, prompt)


def extract_from_pdf(images: list, prompt: str) -> dict:
    from extractor import merge_results
    page_results = []
    for i, image_bytes in enumerate(images):
        print(f"Σελίδα {i+1}/{len(images)}...")
        result = extract_from_page(image_bytes, prompt)
        page_results.append(result)
        time.sleep(0.3)
    return merge_results(page_results)


def check_ollama_connection() -> bool:
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        return response.status_code == 200
    except:
        return False


def warmup_model():
    """Φορτώνει το μοντέλο στη μνήμη."""
    try:
        print(f"Φόρτωση {MODEL}...")
        payload = {"model": MODEL, "prompt": "hi", "stream": False}
        requests.post(OLLAMA_URL, json=payload, timeout=300)
        print("Μοντέλο έτοιμο!")
        return True
    except:
        return False