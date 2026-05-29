import fitz  # PyMuPDF
import base64
import json
import os
from pathlib import Path


def pdf_to_images(pdf_path: str) -> list[bytes]:
    """
    μετατρεπει καθε σελιδα του pdf σε εικονα (bytes).
    """
    doc = fitz.open(pdf_path)
    images = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        # DPI 200 — καλή ποιότητα για OCR
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")
        images.append(img_bytes)

    doc.close()
    print(f"PDF έχει {len(images)} σελίδες")
    return images


def image_to_base64(image_bytes: bytes) -> str:
    """
    μετατρεπω εικόνα σε base64 string.
    """
    return base64.standard_b64encode(image_bytes).decode("utf-8")


def merge_results(page_results: list[dict]) -> dict:
    """
    Συγχωνευει τα αποτελέσματα από όλες τις σελίδες.
    """
    merged = {
        "contract_number": None,
        "contract_date": None,
        "notary": {
            "name": None,
            "address": None
        },
        "sellers": [],
        "buyers": [],
        "representatives": [],
        "properties": []
    }

    for result in page_results:
        if not result:
            continue

        # Contract info
        if result.get("contract_number") and not merged["contract_number"]:
            merged["contract_number"] = result["contract_number"]

        if result.get("contract_date") and not merged["contract_date"]:
            merged["contract_date"] = result["contract_date"]

        # Notary
        if result.get("notary"):
            if result["notary"].get("name") and not merged["notary"]["name"]:
                merged["notary"]["name"] = result["notary"]["name"]
            if result["notary"].get("address") and not merged["notary"]["address"]:
                merged["notary"]["address"] = result["notary"]["address"]

        # Sellers
        if result.get("sellers"):
            for seller in result["sellers"]:
                if seller.get("name"):
                    # Αποφυγή duplicates
                    existing = [s["name"] for s in merged["sellers"]]
                    if seller["name"] not in existing:
                        merged["sellers"].append(seller)

        # Buyers
        if result.get("buyers"):
            for buyer in result["buyers"]:
                if buyer.get("name"):
                    existing = [b["name"] for b in merged["buyers"]]
                    if buyer["name"] not in existing:
                        merged["buyers"].append(buyer)

        # Representatives
        if result.get("representatives"):
            for rep in result["representatives"]:
                if rep.get("name"):
                    existing = [r["name"] for r in merged["representatives"]]
                    if rep["name"] not in existing:
                        merged["representatives"].append(rep)

        # Properties
        if result.get("properties"):
            for prop in result["properties"]:
                if prop.get("type") or prop.get("location"):
                    merged["properties"].append(prop)

    return merged


def save_results(results: dict, output_path: str = "results.json"):
    """
    Αποθηκευω τα αποτελέσματα σε JSON.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Αποτελέσματα αποθηκεύτηκαν στο {output_path}")