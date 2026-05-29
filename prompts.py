# prompts.py
# 3 prompt strategies: zero_shot, few_shot, chain_of_thought
# All in English for better VLM understanding

# ============================================================
# PROMPT 1 — Zero-shot
# Direct extraction without examples
# ============================================================
ZERO_SHOT_PROMPT = """You are a legal document extraction system for Greek property deeds.

Extract the following fields from the text below. Return ONLY a JSON object, no explanation.

JSON structure:
{
  "contract_number": null,
  "contract_date": null,
  "notary": {"name": null, "address": null},
  "sellers": [{"name": null, "afm": null, "address": null, "id_document": null}],
  "buyers": [{"name": null, "afm": null, "address": null, "id_document": null}],
  "representatives": [{"name": null, "represents": null, "id_document": null}],
  "properties": [{"type": null, "location": null, "municipality": null, "block": null, "area_sqm": null, "floor": null, "kaek": null, "building_permit": null}]
}

Field hints:
- contract_number: look for "ΑΡΙΘΜΟΣ" followed by digits
- contract_date: look for a date in the text
- notary name: look for "ΣΥΜΒΟΛΑΙΟΓΡΑΦΟΣ" or "Συμβολαιογράφο"
- seller: look for "πωλητ" or "αφ' ενός" — may be a company (Α.Ε., Τράπεζα)
- buyer: look for "αγοραστ" or "αφ' ετέρου"
- AFM (tax number): look for "ΑΦΜ" followed by digits
- property type: look for "οικόπεδο", "κατάστημα", "διαμέρισμα", "κτίσμα"
- area: look for "τετραγωνικών μέτρων" or "τ.μ." followed by number
- KAEK: look for "ΚΑΕΚ" followed by digits

Use null for any field not found. Return ONLY valid JSON."""


# ============================================================
# PROMPT 2 — Chain of Thought
# Step-by-step reasoning
# ============================================================
COT_PROMPT = """You are a legal document extraction system for Greek property deeds.

Think step by step:

Step 1: Find contract metadata
- Look for "ΑΡΙΘΜΟΣ" → contract number
- Look for date (day/month/year) → contract date

Step 2: Find the notary
- Look for "ΣΥΜΒΟΛΑΙΟΓΡΑΦΟΣ" or "Συμβολαιογράφο" → notary name
- Look for address near notary name → notary address

Step 3: Find sellers (πωλητές)
- Look for "αφ' ενός", "πωλητ", "πωλήτρια τράπεζα"
- For each seller: extract name, AFM (digits after "ΑΦΜ"), address, ID document

Step 4: Find buyers (αγοραστές)
- Look for "αφ' ετέρου", "αγοραστ"
- For each buyer: extract name, AFM, address, ID document

Step 5: Find representatives
- Look for "πληρεξούσιος", "αντιπρόσωπος", "νόμιμος εκπρόσωπος"
- Extract who they represent

Step 6: Find property details
- Look for "οικόπεδο", "κτίσμα", "κατάστημα", "διαμέρισμα"
- Extract: location, municipality, area in sqm, floor, KAEK, building permit

After reasoning, return ONLY this JSON (no other text):
{
  "contract_number": null,
  "contract_date": null,
  "notary": {"name": null, "address": null},
  "sellers": [{"name": null, "afm": null, "address": null, "id_document": null}],
  "buyers": [{"name": null, "afm": null, "address": null, "id_document": null}],
  "representatives": [{"name": null, "represents": null, "id_document": null}],
  "properties": [{"type": null, "location": null, "municipality": null, "block": null, "area_sqm": null, "floor": null, "kaek": null, "building_permit": null}]
}"""


# ============================================================
# PROMPT 3 — Few-shot
# With examples for better understanding
# ============================================================
FEW_SHOT_PROMPT = """You are a legal document extraction system for Greek property deeds.

Here is an example of correct extraction:

Example input:
"ΑΡΙΘΜΟΣ 11.924. Στην Αθήνα σήμερα στις είκοσι εννέα (29) Δεκεμβρίου 1999, στο συμβολαιογραφείο μου που βρίσκεται στην οδό Δημοκρίτου αρ.4, εγώ η Συμβολαιογράφος ΜΑΡΙΑ ΜΑΣΟΥΡΟΥ-ΤΣΑΝΑΚΑ. Ι.- (αφ' ενός): Αθανάσιος Αλμπάνης, ΑΦΜ 94325270, κάτοικος Αγίας Παρασκευής, οδός Αρτέμιδος 18, ΑΔΤ Ν 245733/1984."

Example output:
{
  "contract_number": "11.924",
  "contract_date": "29-12-1999",
  "notary": {
    "name": "Μαρία Μασούρου-Τσανάκα",
    "address": "Δημοκρίτου 4, Αθήνα"
  },
  "sellers": [
    {
      "name": "Αθανάσιος Αλμπάνης",
      "afm": "94325270",
      "address": "Αγίας Παρασκευής, Αρτέμιδος 18",
      "id_document": "ΑΔΤ Ν 245733/1984"
    }
  ],
  "buyers": [],
  "representatives": [],
  "properties": []
}

Now extract from the text below. Return ONLY valid JSON, no explanation:
{
  "contract_number": null,
  "contract_date": null,
  "notary": {"name": null, "address": null},
  "sellers": [{"name": null, "afm": null, "address": null, "id_document": null}],
  "buyers": [{"name": null, "afm": null, "address": null, "id_document": null}],
  "representatives": [{"name": null, "represents": null, "id_document": null}],
  "properties": [{"type": null, "location": null, "municipality": null, "block": null, "area_sqm": null, "floor": null, "kaek": null, "building_permit": null}]
}"""


# Dictionary για εύκολη πρόσβαση
PROMPTS = {
    "zero_shot": ZERO_SHOT_PROMPT,
    "chain_of_thought": COT_PROMPT,
    "few_shot": FEW_SHOT_PROMPT
}