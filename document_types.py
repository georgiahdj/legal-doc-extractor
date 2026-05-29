# document_types.py
# Υποστήριξη διαφορετικών τύπων νομικών εγγράφων

from prompts import PROMPTS

# ============================================================
# DOCUMENT TYPE DETECTION
# ============================================================

DOCUMENT_TYPES = {
    "property_deed": {
        "name": "Αγοραπωλησία (Property Deed)",
        "keywords": ["ΑΓΟΡΑΠΩΛΗΣΙΑ", "ΠΩΛΗΤΗΡΙΟ", "ΑΓΟΡΑΠΩΛΗΤΗΡΙΟ", "πωλητ", "αγοραστ"],
        "description": "Συμβόλαιο αγοραπωλησίας ακινήτου"
    },
    "parental_provision": {
        "name": "Γονική Παροχή (Parental Provision)",
        "keywords": ["ΓΟΝΙΚΗ ΠΑΡΟΧΗ", "ΔΩΡΕΑ", "γονέων", "γονεϊκή"],
        "description": "Γονική παροχή ακινήτου — πωλητής=γονείς, αγοραστής=παιδιά"
    },
    "lease": {
        "name": "Μίσθωση (Lease)",
        "keywords": ["ΜΙΣΘΩΣΗ", "ΜΙΣΘΩΤΗΡΙΟ", "μισθωτ", "εκμισθωτ"],
        "description": "Συμβόλαιο μίσθωσης ακινήτου"
    },
    "donation": {
        "name": "Δωρεά (Donation)",
        "keywords": ["ΔΩΡΕΑ", "δωρητ", "δωρεοδόχ"],
        "description": "Συμβόλαιο δωρεάς ακινήτου"
    }
}


def detect_document_type(text: str) -> str:
    """
    Ανιχνεύει τον τύπο εγγράφου από το OCR κείμενο.
    """
    text_upper = text.upper()

    scores = {}
    for doc_type, info in DOCUMENT_TYPES.items():
        score = sum(1 for kw in info["keywords"] if kw.upper() in text_upper)
        scores[doc_type] = score

    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best
    return "property_deed"  # default


def get_prompt_for_document_type(doc_type: str, strategy: str = "chain_of_thought") -> str:
    """
    Επιστρέφει το κατάλληλο prompt για τον τύπο εγγράφου.
    """
    base_prompt = PROMPTS.get(strategy, PROMPTS["chain_of_thought"])

    if doc_type == "parental_provision":
        note = "\n\nIMPORTANT: This is a PARENTAL PROVISION deed. The SELLER is the parent(s) and the BUYER is the child(ren). Look for 'γονική παροχή', 'δωρεά', 'γονέων'.\n"
        return base_prompt + note

    if doc_type == "lease":
        note = "\n\nIMPORTANT: This is a LEASE agreement. Look for 'μισθωτής' (tenant) and 'εκμισθωτής' (landlord) instead of sellers/buyers.\n"
        return base_prompt + note

    if doc_type == "donation":
        note = "\n\nIMPORTANT: This is a DONATION deed. The 'δωρητής' is the donor (seller) and 'δωρεοδόχος' is the recipient (buyer).\n"
        return base_prompt + note

    return base_prompt


def get_document_info(doc_type: str) -> dict:
    """Επιστρέφει πληροφορίες για τον τύπο εγγράφου."""
    return DOCUMENT_TYPES.get(doc_type, DOCUMENT_TYPES["property_deed"])