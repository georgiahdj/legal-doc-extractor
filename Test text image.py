from PIL import Image, ImageDraw, ImageFont
import io
import base64
import requests

def text_to_image(text: str, width: int = 800) -> bytes:
    """
    Renders text as a clean PNG image.
    """
    # Estimate height
    lines = text.split('\n')
    line_height = 20
    height = max(len(lines) * line_height + 40, 200)
    
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    y = 20
    for line in lines:
        draw.text((20, y), line, fill='black')
        y += line_height
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# Test
sample_text = """ΑΡΙΘΜΟΣ 11.924
ΑΓΟΡΑΠΩΛΗΣΙΑ
Συμβολαιογράφος: ΜΑΡΙΑ ΜΑΣΟΥΡΟΥ-ΤΣΑΝΑΚΑ
Οδός Δημοκρίτου αρ.4, Αθήνα
Πωλητής: Αθανάσιος Αλμπάνης, ΑΦΜ: 94325270
"""

img_bytes = text_to_image(sample_text)
img = Image.open(io.BytesIO(img_bytes))
img.save('/home/claude/test_text.png')
print(f"Image created: {len(img_bytes)} bytes")

# Test με moondream
image_b64 = base64.standard_b64encode(img_bytes).decode("utf-8")
payload = {
    "model": "moondream",
    "prompt": "Extract contract number and notary name from this text. Return JSON only: {\"contract_number\": null, \"notary\": null}",
    "images": [image_b64],
    "stream": False
}

print("Sending to moondream...")
r = requests.post("http://localhost:11434/api/generate", json=payload, timeout=60)
print(r.json().get("response", "No response"))