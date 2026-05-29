import requests
import base64
import json
import re
import time
import os

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_URL = f"{OLLAMA_HOST}/api/generate"
DEFAULT_MODEL = os.environ.get("VLM_MODEL", "moondream")


def extract_from_text(text: str, prompt: str, model_name: str = None) -> dict:
    """
    Στέλνει OCR κείμενο στο VLM και παίρνει JSON.
    """
    active_model = model_name if model_name else DEFAULT_MODEL
    full_prompt = f"{prompt}\n\nText extracted from document:\n{text}\n\nReturn ONLY valid JSON, no markdown, no explanation."

    payload = {
        "model": active_model,
        "prompt": full_prompt,
        "stream": False,
        "format": "json",  # Αναγκάζει το Ollama/Qwen να απαντήσει ΑΠΟΚΛΕΙΣΤΙΚΑ με έγκυρο JSON
        "options": {
            "temperature": 0.0,  # Deterministic output για μέγιστη ακρίβεια σε δομημένα δεδομένα
            "num_ctx": 8192      # Μεγάλο context window για πυκνά νομικά κείμενα
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, headers=headers, timeout=400)
        response.raise_for_status()
        raw_text = response.json()["response"].strip()

        # Καθαρισμός τυχόν markdown που μπορεί να άφησε το μοντέλο
        raw_text = re.sub(r'```json\s*', '', raw_text)
        raw_text = re.sub(r'```\s*', '', raw_text)
        raw_text = raw_text.strip()

        # Απομόνωση του καθαρού JSON block
        start = raw_text.find('{')
        end = raw_text.rfind('}') + 1
        if start >= 0 and end > start:
            raw_text = raw_text[start:end]

        return json.loads(raw_text)

    except json.JSONDecodeError:
        print(f"[ERROR] Το μοντέλο {active_model} δεν επέστρεψε valid JSON.")
        return {}
    except requests.exceptions.Timeout:
        print("[TIMEOUT] Η κλήση στο Ollama backend έληξε.")
        return {}
    except Exception as e:
        print(f"[API ERROR]: {e}")
        return {}


def extract_from_page(image_bytes: bytes, prompt: str, model_name: str = None) -> dict:
    """
    Pipeline: εικόνα → OCR preprocessing → VLM → JSON
    """
    from preprocessor import preprocess_for_llm

    print("  OCR + preprocessing...")
    preprocessed = preprocess_for_llm(image_bytes)
    text = preprocessed["clean_text"]
    print(f"  Κείμενο: {len(text)} chars, {preprocessed['total_chunks']} chunks")
    print(f"  VLM extraction με το μοντέλο: {model_name if model_name else DEFAULT_MODEL}...")
    return extract_from_text(text, prompt, model_name)


def extract_from_pdf(images: list, prompt: str, model_name: str = None) -> dict:
    from extractor import merge_results
    page_results = []
    for i, image_bytes in enumerate(images):
        print(f"Σελίδα {i+1}/{len(images)}...")
        result = extract_from_page(image_bytes, prompt, model_name)
        page_results.append(result)
        time.sleep(0.3)
    return merge_results(page_results)


def check_ollama_connection() -> bool:
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False


def warmup_model(model_name: str = None):
    """Φορτώνει το μοντέλο στη μνήμη."""
    active_model = model_name if model_name else DEFAULT_MODEL
    try:
        print(f"Φόρτωση {active_model}...")
        payload = {"model": active_model, "prompt": "hi", "stream": False}
        requests.post(OLLAMA_URL, json=payload, timeout=300)
        print("Μοντέλο έτοιμο!")
        return True
    except:
        return False


def safe_extract_from_page(image_bytes: bytes, prompt: str, model_name: str = None) -> dict:
    """
    Safe wrapper για extract_from_page με error handling χωρίς να σπάει το signature του error_handler.
    """
    from error_handler import safe_extract, fix_result
    
    # Δημιουργούμε μια εσωτερική συνάρτηση-γέφυρα που έχει ήδη ενσωματωμένο το model_name
    def extract_bridge(img_bytes, pr):
        return extract_from_page(img_bytes, pr, model_name=model_name)
        
    # Περνάμε τη γέφυρα στο safe_extract. Έτσι το 4ο όρισμα παραμένει κενό (το default int των retries)
    result = safe_extract(extract_bridge, image_bytes, prompt)
    return fix_result(result)