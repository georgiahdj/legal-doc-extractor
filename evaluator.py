# evaluator.py
# Αξιολόγηση των 3 prompt strategies
# Μετρικές: speed, accuracy, completeness, format correctness, consistency, error rate

import time
import json
import re
from prompts import PROMPTS
from ollama_extractor import extract_from_page

# ============================================================
# GROUND TRUTH — γνωστές τιμές από το συμβόλαιο
# ============================================================
GROUND_TRUTH = {
    "contract_number": "11.924",
    "contract_date": "29-12-1999",
    "notary_name": "ΜΑΡΙΑ ΜΑΣΟΥΡΟΥ-ΤΣΑΝΑΚΑ",
    "seller_name": "ΑΘΑΝΑΣΙΟΣ ΑΛΜΠΑΝΗΣ",
    "seller_afm": "94325270",
    "property_type": "οικόπεδο"
}


# ============================================================
# ΜΕΤΡΙΚΕΣ
# ============================================================

def count_extracted_fields(result: dict) -> dict:
    """Μετράει πόσα fields έχουν τιμή."""
    stats = {
        "contract_number": 0,
        "contract_date": 0,
        "notary_name": 0,
        "notary_address": 0,
        "sellers_count": 0,
        "buyers_count": 0,
        "representatives_count": 0,
        "properties_count": 0,
        "total_filled": 0
    }

    if result.get("contract_number"):
        stats["contract_number"] = 1
        stats["total_filled"] += 1
    if result.get("contract_date"):
        stats["contract_date"] = 1
        stats["total_filled"] += 1
    if result.get("notary", {}).get("name"):
        stats["notary_name"] = 1
        stats["total_filled"] += 1
    if result.get("notary", {}).get("address"):
        stats["notary_address"] = 1
        stats["total_filled"] += 1

    sellers = [s for s in result.get("sellers", []) if s.get("name")]
    stats["sellers_count"] = len(sellers)
    stats["total_filled"] += len(sellers)

    buyers = [b for b in result.get("buyers", []) if b.get("name")]
    stats["buyers_count"] = len(buyers)
    stats["total_filled"] += len(buyers)

    reps = [r for r in result.get("representatives", []) if r.get("name")]
    stats["representatives_count"] = len(reps)
    stats["total_filled"] += len(reps)

    props = [p for p in result.get("properties", []) if p.get("type")]
    stats["properties_count"] = len(props)
    stats["total_filled"] += len(props)

    return stats


def check_format_correctness(result: dict) -> dict:
    """Ελέγχει αν τα fields έχουν σωστό format."""
    checks = {
        "afm_format": False,
        "date_format": False,
        "contract_number_format": False
    }

    # AFM: 9 ψηφία
    for seller in result.get("sellers", []):
        afm = seller.get("afm", "")
        if afm and re.match(r'^\d{9}$', str(afm).replace(" ", "")):
            checks["afm_format"] = True

    # Date format
    date = result.get("contract_date", "")
    if date and re.search(r'\d{4}', str(date)):
        checks["date_format"] = True

    # Contract number
    cn = result.get("contract_number", "")
    if cn and re.search(r'\d+', str(cn)):
        checks["contract_number_format"] = True

    return checks


def check_ground_truth_accuracy(result: dict) -> dict:
    """Συγκρίνει με γνωστές τιμές ground truth."""
    accuracy = {
        "contract_number_correct": False,
        "notary_correct": False,
        "seller_correct": False,
        "seller_afm_correct": False,
        "property_type_correct": False,
        "score": 0
    }

    # Contract number
    cn = str(result.get("contract_number", "")).strip()
    if "11.924" in cn or "11924" in cn:
        accuracy["contract_number_correct"] = True
        accuracy["score"] += 1

    # Notary
    notary = str(result.get("notary", {}).get("name", "")).upper()
    if "ΜΑΣΟΥΡΟΥ" in notary or "ΤΣΑΝΑΚΑ" in notary or "MASOUROU" in notary:
        accuracy["notary_correct"] = True
        accuracy["score"] += 1

    # Seller name
    for seller in result.get("sellers", []):
        name = str(seller.get("name", "")).upper()
        if "ΑΛΜΠΑΝΗΣ" in name or "ALBANIS" in name or "ALBAINIS" in name:
            accuracy["seller_correct"] = True
            accuracy["score"] += 1
            break

    # Seller AFM
    for seller in result.get("sellers", []):
        afm = str(seller.get("afm", "")).replace(" ", "")
        if "94325270" in afm:
            accuracy["seller_afm_correct"] = True
            accuracy["score"] += 1
            break

    # Property type
    for prop in result.get("properties", []):
        ptype = str(prop.get("type", "")).lower()
        if "οικόπεδο" in ptype or "oikopedo" in ptype:
            accuracy["property_type_correct"] = True
            accuracy["score"] += 1
            break

    return accuracy


def check_json_validity(result: dict) -> bool:
    """Ελέγχει αν το result είναι valid (όχι κενό)."""
    return bool(result) and len(result) > 0


# ============================================================
# EVALUATION RUNNER
# ============================================================

def evaluate_prompt(prompt_name: str, prompt_text: str, test_images: list) -> dict:
    """Αξιολογεί ένα prompt σε λίγες σελίδες."""
    print(f"\nΑξιολόγηση: {prompt_name}")
    print("=" * 40)

    results_per_page = []
    times_per_page = []
    json_valid_count = 0
    all_accuracy = []
    all_format = []

    test_subset = test_images[:3]

    for i, image_bytes in enumerate(test_subset):
        print(f"  Σελίδα {i+1}/3...")
        start = time.time()
        result = extract_from_page(image_bytes, prompt_text)
        elapsed = time.time() - start

        times_per_page.append(elapsed)
        results_per_page.append(result)

        if check_json_validity(result):
            json_valid_count += 1

        accuracy = check_ground_truth_accuracy(result)
        all_accuracy.append(accuracy["score"])

        format_check = check_format_correctness(result)
        all_format.append(format_check)

        print(f"    Time: {elapsed:.1f}s | Fields: {count_extracted_fields(result)['total_filled']} | GT score: {accuracy['score']}/5")

    # Merge results
    from extractor import merge_results
    merged = merge_results(results_per_page)
    fields = count_extracted_fields(merged)
    final_accuracy = check_ground_truth_accuracy(merged)

    avg_time = sum(times_per_page) / len(times_per_page)
    error_rate = 1 - (json_valid_count / len(test_subset))

    evaluation = {
        "prompt_name": prompt_name,
        "avg_time_per_page": round(avg_time, 2),
        "total_time": round(sum(times_per_page), 2),
        "fields_extracted": fields,
        "json_validity_rate": round(json_valid_count / len(test_subset), 2),
        "error_rate": round(error_rate, 2),
        "ground_truth_score": final_accuracy["score"],
        "ground_truth_details": final_accuracy,
        "format_checks": all_format,
        "result_sample": merged
    }

    print(f"\n  Avg time: {avg_time:.1f}s/page")
    print(f"  Fields: {fields['total_filled']}")
    print(f"  JSON valid: {json_valid_count}/3")
    print(f"  GT score: {final_accuracy['score']}/5")

    return evaluation


def run_full_evaluation(images: list) -> list:
    """Τρέχει ΌΛΑ τα prompts και επιστρέφει σύγκριση."""
    print("\nΞεκινάει η αξιολόγηση:")
    print("3 prompts × 3 σελίδες")
    print("=" * 50)

    all_results = []
    for prompt_name, prompt_text in PROMPTS.items():
        result = evaluate_prompt(prompt_name, prompt_text, images)
        all_results.append(result)

    best_accuracy = max(all_results, key=lambda x: x["ground_truth_score"])
    best_speed = min(all_results, key=lambda x: x["avg_time_per_page"])
    best_fields = max(all_results, key=lambda x: x["fields_extracted"]["total_filled"])

    print("\n" + "=" * 50)
    print(f"Best accuracy: {best_accuracy['prompt_name']} (GT score: {best_accuracy['ground_truth_score']}/5)")
    print(f"Fastest: {best_speed['prompt_name']} ({best_speed['avg_time_per_page']}s/page)")
    print(f"Most fields: {best_fields['prompt_name']} ({best_fields['fields_extracted']['total_filled']} fields)")

    return all_results


def format_evaluation_for_display(results: list) -> list:
    """Μορφοποιεί για εμφάνιση στο Streamlit."""
    display = []
    for r in results:
        display.append({
            "Prompt": r["prompt_name"],
            "Avg Time (s)": r["avg_time_per_page"],
            "Fields Found": r["fields_extracted"]["total_filled"],
            "GT Score (0-5)": r["ground_truth_score"],
            "JSON Valid Rate": r["json_validity_rate"],
            "Error Rate": r["error_rate"],
            "Sellers": r["fields_extracted"]["sellers_count"],
            "Buyers": r["fields_extracted"]["buyers_count"],
            "Properties": r["fields_extracted"]["properties_count"],
        })
    return display