# error_handler.py
# Robust error handling για cases που το OCR/VLM αποτυγχάνει

import json
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def empty_result() -> dict:
    """Επιστρέφει κενό αποτέλεσμα με σωστή δομή."""
    return {
        "contract_number": None,
        "contract_date": None,
        "notary": {"name": None, "address": None},
        "sellers": [],
        "buyers": [],
        "representatives": [],
        "properties": []
    }


def validate_result(result: dict) -> tuple[bool, list]:
    """
    Ελέγχει αν το result έχει σωστή δομή.
    Επιστρέφει (is_valid, list_of_warnings).
    """
    warnings = []

    if not isinstance(result, dict):
        return False, ["Result is not a dict"]

    required_keys = ["contract_number", "contract_date", "notary", "sellers", "buyers", "properties"]
    for key in required_keys:
        if key not in result:
            warnings.append(f"Missing key: {key}")

    # Έλεγχος notary
    if "notary" in result and not isinstance(result["notary"], dict):
        warnings.append("notary should be a dict")

    # Έλεγχος lists
    for list_key in ["sellers", "buyers", "representatives", "properties"]:
        if list_key in result and not isinstance(result[list_key], list):
            warnings.append(f"{list_key} should be a list")
            result[list_key] = []

    return len(warnings) == 0, warnings


def fix_result(result: dict) -> dict:
    """
    Διορθώνει common errors στο result:
    - Προσθέτει missing keys
    - Διορθώνει λάθος types
    - Καθαρίζει noise values
    """
    if not isinstance(result, dict):
        return empty_result()

    fixed = empty_result()

    # Contract number
    cn = result.get("contract_number")
    if cn and str(cn).strip() and str(cn).strip() != "null":
        fixed["contract_number"] = str(cn).strip()

    # Contract date
    date = result.get("contract_date")
    if date and str(date).strip() and str(date).strip() != "null":
        fixed["contract_date"] = str(date).strip()

    # Notary
    notary = result.get("notary", {})
    if isinstance(notary, dict):
        fixed["notary"]["name"] = notary.get("name") or None
        fixed["notary"]["address"] = notary.get("address") or None

    # Sellers
    sellers = result.get("sellers", [])
    if isinstance(sellers, list):
        for s in sellers:
            if isinstance(s, dict) and s.get("name") and len(str(s.get("name", ""))) > 2:
                fixed["sellers"].append({
                    "name": s.get("name"),
                    "afm": s.get("afm"),
                    "address": s.get("address"),
                    "id_document": s.get("id_document")
                })

    # Buyers
    buyers = result.get("buyers", [])
    if isinstance(buyers, list):
        for b in buyers:
            if isinstance(b, dict) and b.get("name") and len(str(b.get("name", ""))) > 2:
                fixed["buyers"].append({
                    "name": b.get("name"),
                    "afm": b.get("afm"),
                    "address": b.get("address"),
                    "id_document": b.get("id_document")
                })

    # Representatives
    reps = result.get("representatives", [])
    if isinstance(reps, list):
        for r in reps:
            if isinstance(r, dict) and r.get("name") and len(str(r.get("name", ""))) > 2:
                fixed["representatives"].append({
                    "name": r.get("name"),
                    "represents": r.get("represents"),
                    "id_document": r.get("id_document")
                })

    # Properties
    props = result.get("properties", [])
    if isinstance(props, list):
        for p in props:
            if isinstance(p, dict) and (p.get("type") or p.get("location")):
                fixed["properties"].append({
                    "type": p.get("type"),
                    "location": p.get("location"),
                    "municipality": p.get("municipality"),
                    "block": p.get("block"),
                    "area_sqm": p.get("area_sqm"),
                    "floor": p.get("floor"),
                    "kaek": p.get("kaek"),
                    "building_permit": p.get("building_permit")
                })

    return fixed


def safe_extract(extract_func, image_bytes: bytes, prompt: str, retries: int = 2) -> dict:
    """
    Wrapper για safe extraction με retries.
    Αν αποτύχει, επιστρέφει κενό αποτέλεσμα.
    """
    for attempt in range(retries):
        try:
            result = extract_func(image_bytes, prompt)

            if not result:
                logger.warning(f"Empty result on attempt {attempt + 1}")
                continue

            is_valid, warnings = validate_result(result)
            if warnings:
                logger.warning(f"Validation warnings: {warnings}")

            fixed = fix_result(result)
            return fixed

        except Exception as e:
            logger.error(f"Extraction error on attempt {attempt + 1}: {e}")
            if attempt == retries - 1:
                return empty_result()

    return empty_result()


def detect_document_type(text: str) -> str:
    """
    Ανιχνεύει τον τύπο του εγγράφου από το κείμενο.
    Επιστρέφει: 'property_deed', 'parental_provision', 'unknown'
    """
    text_upper = text.upper()

    if any(word in text_upper for word in ["ΑΓΟΡΑΠΩΛΗΣΙΑ", "ΠΩΛΗΤΗΡΙΟ", "ΑΓΟΡΑΠΩΛΗΤΗΡΙΟ"]):
        return "property_deed"

    if any(word in text_upper for word in ["ΓΟΝΙΚΗ ΠΑΡΟΧΗ", "ΔΩΡΕΑ", "ΓΟΝΕΩΝ"]):
        return "parental_provision"

    if any(word in text_upper for word in ["ΜΙΣΘΩΣΗ", "ΜΙΣΘΩΤΗΡΙΟ"]):
        return "lease"

    return "unknown"