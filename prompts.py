#### prompts.py
### 3 στρατηγικες προμπτ: zero shot, few shot, chain of thought
### 3 διαφορετικα προμπτ για καθε στρατηγικη


# ============================================================
# PROMPT 1 — Zero-shot
# prompt χωρίς παραδείγματα
# ============================================================
ZERO_SHOT_PROMPT = """
This is a page from a Greek property deed (συμβόλαιο αγοραπωλησίας).

Look carefully at the text and extract ANY of the following you can find:

- Contract number (look for "ΑΡΙΘΜΟΣ" or a number near the top)
- Date (look for a date in the text)
- Notary name (look for "ΣΥΜΒΟΛΑΙΟΓΡΑΦΟΣ" or "Συμβολαιογράφο")
- Notary address
- Seller name (look for "πωλητ" or "αφ' ενός")
- Seller AFM (look for "ΑΦΜ" followed by numbers)
- Buyer name (look for "αγοραστ" or "αφ' ετέρου")  
- Buyer AFM
- Property type (look for "οικόπεδο", "κατάστημα", "διαμέρισμα")
- Property location
- Property area (look for "τετραγωνικών μέτρων" or "τ.μ.")
- KAEK number

Return a JSON object. Use null for anything not found on this page.
Do not include markdown, just the raw JSON.

{
  "contract_number": null,
  "contract_date": null,
  "notary": {"name": null, "address": null},
  "sellers": [{"name": null, "afm": null, "address": null, "id_document": null}],
  "buyers": [{"name": null, "afm": null, "address": null, "id_document": null}],
  "representatives": [{"name": null, "represents": null, "id_document": null}],
  "properties": [{"type": null, "location": null, "municipality": null, "block": null, "area_sqm": null, "floor": null, "kaek": null, "building_permit": null}]
}
"""

# ============================================================
# PROMPT 2 — Chain of Thought
# το μοντέλο σκεφτεται βήμα βήμα
# ============================================================
COT_PROMPT = """
You are a legal document analysis system specialized in Greek property deeds.

Think step by step before extracting information:

Step 1: Is this the first page? Look for contract number and notary details.
Step 2: Are there party descriptions? Look for seller (πωλητής/πωλήτρια) and buyer (αγοραστής/αγοράστρια).
Step 3: Are there property descriptions? Look for οικόπεδο, κτίσμα, ΚΑΕΚ.
Step 4: Are there representative details? Look for πληρεξούσιος, αντιπρόσωπος.
Step 5: Extract all found information into JSON.

Extract from this page of a Greek property deed:
- Contract number and date
- Notary: name, address
- Sellers: name, AFM, address, ID document
- Buyers: name, AFM, address, ID document  
- Representatives: name, who they represent, ID document
- Properties: type, location, municipality, block, area, floor, KAEK, building permit

Return ONLY valid JSON, no text before or after.
Use null for fields not found on this page.

{
  "contract_number": null,
  "contract_date": null,
  "notary": {"name": null, "address": null},
  "sellers": [{"name": null, "afm": null, "address": null, "id_document": null}],
  "buyers": [{"name": null, "afm": null, "address": null, "id_document": null}],
  "representatives": [{"name": null, "represents": null, "id_document": null}],
  "properties": [{"type": null, "location": null, "municipality": null, "block": null, "area_sqm": null, "floor": null, "kaek": null, "building_permit": null}]
}
"""

# ============================================================
# PROMPT 3 — Few-shot
#  examples για να καταλάβει το μοντέλο
# ============================================================
FEW_SHOT_PROMPT = """
You are a legal document analysis system specialized in Greek property deeds.

Here is an example of correct extraction:

Example input text: 
"Αριθμός 11.924. Στην Αθήνα σήμερα στις 29 Δεκεμβρίου 1999, στο συμβολαιογραφείο μου, 
εγώ η Συμβολαιογράφος ΜΑΡΙΑ ΜΑΣΟΥΡΟΥ-ΤΣΑΝΑΚΑ, οδός Δημοκρίτου 4."

Example output:
{
  "contract_number": "11.924",
  "contract_date": "29-12-1999",
  "notary": {
    "name": "Μαρία Μασούρου-Τσανάκα",
    "address": "Δημοκρίτου 4, Αθήνα"
  },
  "sellers": [],
  "buyers": [],
  "representatives": [],
  "properties": []
}

Now extract from the provided page. Return ONLY valid JSON, no text before or after.
Use null for missing fields, empty list [] if no items found.

{
  "contract_number": null,
  "contract_date": null,
  "notary": {"name": null, "address": null},
  "sellers": [{"name": null, "afm": null, "address": null, "id_document": null}],
  "buyers": [{"name": null, "afm": null, "address": null, "id_document": null}],
  "representatives": [{"name": null, "represents": null, "id_document": null}],
  "properties": [{"type": null, "location": null, "municipality": null, "block": null, "area_sqm": null, "floor": null, "kaek": null, "building_permit": null}]
}
"""

# Dictionary για εύκολη πρόσβαση
PROMPTS = {
    "zero_shot": ZERO_SHOT_PROMPT,
    "chain_of_thought": COT_PROMPT,
    "few_shot": FEW_SHOT_PROMPT
}