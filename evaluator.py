# evaluator.py
#
# Αυτό το αρχείο θα συγκρίνει τα 3 prompts
# θα μετραει:
# 1. Πόσα fields εχουν τιμη στο αποτελεσμα (accuracy proxy), αν ενα προμπτ βρισκει περισσοτερα fields, μαλλον καλυτερο
# 2. Πόσο χρόνο πήρε (speed)

import time
import json
from prompts import PROMPTS
from ollama_extractor import extract_from_page


def count_extracted_fields(result: dict) -> dict:
    """
    Μετράει πόσα fields έχουν τιμή (όχι null/empty).
    Το χρησιμοποιούμε ως proxy για accuracy —
    όσο περισσότερα fields εξήχθησαν, τόσο καλύτερο το prompt.
    """
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

    # Contract info
    if result.get("contract_number"):
        stats["contract_number"] = 1
        stats["total_filled"] += 1

    if result.get("contract_date"):
        stats["contract_date"] = 1
        stats["total_filled"] += 1

    # Notary
    if result.get("notary", {}).get("name"):
        stats["notary_name"] = 1
        stats["total_filled"] += 1

    if result.get("notary", {}).get("address"):
        stats["notary_address"] = 1
        stats["total_filled"] += 1

    # Parties
    sellers = result.get("sellers", [])
    stats["sellers_count"] = len([s for s in sellers if s.get("name")])
    stats["total_filled"] += stats["sellers_count"]

    buyers = result.get("buyers", [])
    stats["buyers_count"] = len([b for b in buyers if b.get("name")])
    stats["total_filled"] += stats["buyers_count"]

    reps = result.get("representatives", [])
    stats["representatives_count"] = len([r for r in reps if r.get("name")])
    stats["total_filled"] += stats["representatives_count"]

    # Properties
    props = result.get("properties", [])
    stats["properties_count"] = len([p for p in props if p.get("type")])
    stats["total_filled"] += stats["properties_count"]

    return stats


def evaluate_prompt(
    prompt_name: str,
    prompt_text: str,
    test_images: list
) -> dict:
    """
    Τρέχει ένα prompt σε λίγες σελίδες και μετράει
    χρόνο και αριθμό εξαχθέντων fields.

    Χρησιμοποιούμε μόνο τις πρώτες 3 σελίδες για speed —
    αυτές έχουν τα πιο σημαντικά δεδομένα.
    """
    print(f"\nΑξιολόγηση prompt: {prompt_name}")
    print("=" * 40)

    results_per_page = []
    times_per_page = []

    # Τρέχει μόνο στις πρώτες 3 σελίδες
    test_subset = test_images[:3]

    for i, image_bytes in enumerate(test_subset):
        print(f"  Σελίδα {i+1}/3...")

        # Μετράμε χρόνο
        start = time.time()
        result = extract_from_page(image_bytes, prompt_text)
        elapsed = time.time() - start

        times_per_page.append(elapsed)
        results_per_page.append(result)

        print(f"  Χρόνος: {elapsed:.1f}s")

    # αποτελέσματα
    from extractor import merge_results
    merged = merge_results(results_per_page)
    fields = count_extracted_fields(merged)

    avg_time = sum(times_per_page) / len(times_per_page)

    evaluation = {
        "prompt_name": prompt_name,
        "avg_time_per_page": round(avg_time, 2),
        "total_time": round(sum(times_per_page), 2),
        "fields_extracted": fields,
        "result_sample": merged
    }

    print(f"  Fields εξαχθέντα: {fields['total_filled']}")
    print(f"  Μέσος χρόνος/σελίδα: {avg_time:.1f}s")

    return evaluation


def run_full_evaluation(images: list) -> list:
    """
    Τρέχει ΌΛΑ τα prompts και επιστρέφει
    συγκριτικά αποτελέσματα.
    """
    print("\nΞεκινάει η αξιολόγηση των prompts:")
    print("Θα δοκιμαστούν 3 prompts στις πρώτες 3 σελίδες")
    print("=" * 50)

    all_results = []

    for prompt_name, prompt_text in PROMPTS.items():
        result = evaluate_prompt(prompt_name, prompt_text, images)
        all_results.append(result)

    # Βρίσκουμε το καλύτερο prompt
    best_accuracy = max(
        all_results,
        key=lambda x: x["fields_extracted"]["total_filled"]
    )
    best_speed = min(
        all_results,
        key=lambda x: x["avg_time_per_page"]
    )

    print("\n" + "=" * 50)
    print(f"Καλύτερο για accuracy: {best_accuracy['prompt_name']}")
    print(f"Καλύτερο για speed: {best_speed['prompt_name']}")

    return all_results


def format_evaluation_for_display(results: list) -> list:
    """
    Μορφοποιεί τα αποτελέσματα για εμφάνιση στο Streamlit.
    """
    display = []

    for r in results:
        display.append({
            "Prompt": r["prompt_name"],
            "Avg Time (s)": r["avg_time_per_page"],
            "Fields Found": r["fields_extracted"]["total_filled"],
            "Sellers": r["fields_extracted"]["sellers_count"],
            "Buyers": r["fields_extracted"]["buyers_count"],
            "Properties": r["fields_extracted"]["properties_count"],
        })

    return display