import fitz
import re
from PIL import Image, ImageEnhance, ImageFilter
import io
import pytesseract

import os
if os.name == 'nt':  # Windows
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# Linux (Docker) uses system tesseract automatically


def pdf_to_images(pdf_path: str, dpi: int = 300) -> list:
    doc = fitz.open(pdf_path)
    images = []
    for i in range(len(doc)):
        page = doc[i]
        pix = page.get_pixmap(dpi=dpi)
        images.append(pix.tobytes("png"))
    doc.close()
    print(f"PDF έχει {len(images)} σελίδες")
    return images


def crop_stamp_area(img: Image.Image, right_crop_pct: float = 0.25) -> Image.Image:
    """Κόβει το δεξί τμήμα με γραμματόσημα/σφραγίδες."""
    w, h = img.size
    return img.crop((0, 0, int(w * (1 - right_crop_pct)), h))


def crop_margins(img: Image.Image, margin_pct: float = 0.03) -> Image.Image:
    """Κόβει τα περιθώρια."""
    w, h = img.size
    mx, my = int(w * margin_pct), int(h * margin_pct)
    return img.crop((mx, my, w - mx, h - my))


def enhance_for_ocr(img: Image.Image) -> Image.Image:
    """Βελτιώνει εικόνα για OCR."""
    img = img.convert("L")
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    return img


def preprocess_image(image_bytes: bytes) -> Image.Image:
    """Full image preprocessing pipeline."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = crop_stamp_area(img, right_crop_pct=0.25)
    img = crop_margins(img, margin_pct=0.03)
    img = enhance_for_ocr(img)
    return img


def extract_text_ocr(image_bytes: bytes) -> str:
    """Εξάγει κείμενο με Tesseract."""
    img = preprocess_image(image_bytes)
    text = pytesseract.image_to_string(img, lang='ell+eng', config='--psm 6')
    return text.strip()


def clean_text(text: str) -> str:
    """
    Καθαρίζει το OCR κείμενο:
    1. Αφαιρεί πολλαπλά κενά/newlines
    2. Αφαιρεί special chars/noise
    3. Κρατάει μόνο ουσιαστικό κείμενο
    """
    # Αφαίρεση noise characters
    text = re.sub(r'[^\w\s\.\,\-\(\)\:\;\/\αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩάέήίόύώΆΈΉΊΌΎΏ]', ' ', text)
    # Αφαίρεση πολλαπλών κενών
    text = re.sub(r' +', ' ', text)
    # Αφαίρεση πολλαπλών newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Αφαίρεση γραμμών με λιγότερους από 3 χαρακτήρες (noise)
    lines = [l for l in text.split('\n') if len(l.strip()) >= 3]
    return '\n'.join(lines).strip()


def split_into_chunks(text: str, max_chars: int = 500) -> list:
    """
    Κόβει το κείμενο σε μικρά chunks για το moondream.
    Κόβει σε παραγράφους και μετά σε chunks.
    """
    paragraphs = text.split('\n\n')
    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) < max_chars:
            current += para + "\n\n"
        else:
            if current:
                chunks.append(current.strip())
            current = para + "\n\n"

    if current:
        chunks.append(current.strip())

    return chunks


def preprocess_for_llm(image_bytes: bytes) -> dict:
    """
    Full pipeline: εικόνα → OCR → clean → chunks
    Returns dict με raw text και chunks.
    """
    raw_text = extract_text_ocr(image_bytes)
    clean = clean_text(raw_text)
    chunks = split_into_chunks(clean, max_chars=500)

    return {
        "raw_text": raw_text,
        "clean_text": clean,
        "chunks": chunks,
        "total_chars": len(clean),
        "total_chunks": len(chunks)
    }