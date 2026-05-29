import requests
import json
import time
import os

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_URL = f"{OLLAMA_HOST}/api/generate"
MODEL = "qwen2.5vl:3b"


def warmup_model():
    """
    Φορτώνει το μοντέλο στη μνήμη με ένα απλό request.
    Πρέπει να τρέχει πριν από τα extractions.
    """
    try:
        print("Φόρτωση moondream...")
        payload = {"model": MODEL, "prompt": "hi", "stream": False}
        requests.post(OLLAMA_URL, json=payload, timeout=120)
        print("Moondream έτοιμο!")
        return True
    except:
        return False


def extract_from_text(text: str, prompt: str) -> dict:
    """
    Στέλνει κείμενο στο moondream και παίρνει JSON.
    """
    full_prompt = f"{prompt}\n\nText from document:\n{text}\n\nReturn ONLY valid JSON, nothing else."

    payload = {
        "model": MODEL,
        "prompt": full_prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=600)
        raw_text = response.json()["response"].strip()

        import re
        raw_text = re.sub(r'```json\s*', '', raw_text)
        raw_text = re.sub(r'```\s*', '', raw_text)
        raw_text = raw_text.strip()


        # Try to find JSON in response
        start = raw_text.find('{')
        end = raw_text.rfind('}') + 1
        if start >= 0 and end > start:
            raw_text = raw_text[start:end]

        print("RAW:", raw_text[:300])

        return json.loads(raw_text)

    except json.JSONDecodeError:
        print("Δεν ήταν valid JSON")
        return {}
    except requests.exceptions.Timeout:
        print("Timeout — moondream δεν είναι φορτωμένο!")
        return {}
    except Exception as e:
        print(f"Error: {e}")
        return {}


def extract_from_page(image_bytes: bytes, prompt: str) -> dict:
    """
    Pipeline: εικόνα → OCR → clean → moondream → JSON
    """
    from preprocessor import preprocess_for_llm
    from extractor import merge_results

    print("  OCR + preprocessing...")
    preprocessed = preprocess_for_llm(image_bytes)
    text = preprocessed["clean_text"]
    print(f"  Κείμενο: {len(text)} chars, {preprocessed['total_chunks']} chunks")

    # Στέλνουμε όλο το κείμενο (είναι ήδη μικρό από το chunking)
    print("  Moondream extraction...")
    result = extract_from_text(text, prompt)
    return result


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