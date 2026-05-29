import fitz
import re
import os
import gc
from PIL import Image, ImageEnhance, ImageFilter
import io
import pytesseract
import numpy as np

if os.name == 'nt':  # Windows
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# ============================================================
# STEP 1: PDF → Image (optimal DPI)
# ============================================================

def pdf_to_images(pdf_path: str, dpi: int = 250) -> list:
    """
    Μετατρέπει PDF σε εικόνες.
    DPI 250 = sweet spot (καλή ποιότητα, λογική μνήμη).
    """
    doc = fitz.open(pdf_path)
    images = []
    for i in range(len(doc)):
        page = doc[i]
        pix = page.get_pixmap(dpi=dpi)
        images.append(pix.tobytes("png"))
    doc.close()
    print(f"PDF έχει {len(images)} σελίδες")
    return images


# ============================================================
# STEP 2: Image Enhancement
# ============================================================

def crop_stamp_area(img: Image.Image, right_crop_pct: float = 0.25) -> Image.Image:
    """Κόβει δεξί τμήμα με γραμματόσημα/σφραγίδες."""
    w, h = img.size
    return img.crop((0, 0, int(w * (1 - right_crop_pct)), h))


def crop_margins(img: Image.Image, margin_pct: float = 0.03) -> Image.Image:
    """Κόβει περιθώρια."""
    w, h = img.size
    mx, my = int(w * margin_pct), int(h * margin_pct)
    return img.crop((mx, my, w - mx, h - my))


def to_grayscale(img: Image.Image) -> Image.Image:
    """Grayscale — λιγότερη μνήμη, καλύτερο OCR."""
    return img.convert("L")


def adaptive_threshold(img: Image.Image) -> Image.Image:
    """
    Adaptive thresholding — τεράστια διαφορά για scans.
    Κάνει πιο καθαρό text και καλύτερο contrast.
    """
    try:
        import cv2
        img_array = np.array(img)
        thresh = cv2.adaptiveThreshold(
            img_array, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        return Image.fromarray(thresh)
    except ImportError:
        # Fallback αν δεν υπάρχει cv2
        threshold = 128
        return img.point(lambda x: 255 if x > threshold else 0)


def sharpen(img: Image.Image) -> Image.Image:
    """Sharpening — τα scans είναι συχνά blurry."""
    return img.filter(ImageFilter.SHARPEN)


def enhance_contrast(img: Image.Image) -> Image.Image:
    """Contrast boost."""
    return ImageEnhance.Contrast(img).enhance(2.0)


def deskew(img: Image.Image) -> Image.Image:
    """Διορθώνει κλίση σελίδας."""
    try:
        osd = pytesseract.image_to_osd(img)
        angle = 0
        for line in osd.split('\n'):
            if 'Rotate' in line:
                angle = int(line.split(':')[1].strip())
        if angle != 0:
            img = img.rotate(-angle, expand=True, fillcolor=255)
    except:
        pass
    return img


def full_enhance(img: Image.Image) -> Image.Image:
    """
    Full enhancement pipeline:
    1. Grayscale
    2. Deskew
    3. Sharpen
    4. Enhance contrast
    5. Adaptive threshold
    """
    img = to_grayscale(img)
    img = deskew(img)
    img = sharpen(img)
    img = enhance_contrast(img)
    img = adaptive_threshold(img)
    return img


# ============================================================
# STEP 3: Smart Cropping με Tiling
# ============================================================

def crop_to_strips(img: Image.Image, n_strips: int = 3, overlap_pct: float = 0.05) -> list:
    """
    Κόβει σε οριζόντια strips με overlap.
    Overlap αποτρέπει κόψιμο λέξεων στα όρια.
    """
    w, h = img.size
    strip_h = h // n_strips
    overlap = int(h * overlap_pct)

    strips = []
    for i in range(n_strips):
        top = max(0, i * strip_h - overlap)
        bottom = min(h, (i + 1) * strip_h + overlap)
        strip = img.crop((0, top, w, bottom))
        buf = io.BytesIO()
        strip.save(buf, format="PNG")
        strips.append(buf.getvalue())

    return strips


def dynamic_crop_around_keywords(img: Image.Image, keywords: list) -> list:
    """
    Dynamic crop: βρίσκει regions με keywords και κάνει crop γύρω τους.
    Πχ: βρίσκει "ΑΦΜ" και κόβει εκεί.
    """
    try:
        data = pytesseract.image_to_data(img, lang='ell+eng', output_type=pytesseract.Output.DICT)
        crops = []

        for i, word in enumerate(data['text']):
            for keyword in keywords:
                if keyword.lower() in word.lower() and data['conf'][i] > 30:
                    x, y, w_box, h_box = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    # Crop με padding γύρω από το keyword
                    padding = 100
                    img_w, img_h = img.size
                    crop = img.crop((
                        max(0, x - padding),
                        max(0, y - padding),
                        min(img_w, x + w_box + padding * 5),
                        min(img_h, y + h_box + padding * 3)
                    ))
                    buf = io.BytesIO()
                    crop.save(buf, format="PNG")
                    crops.append({"keyword": keyword, "image": buf.getvalue()})

        return crops
    except:
        return []


# ============================================================
# STEP 4: OCR με optimal settings
# ============================================================

def extract_text_ocr(image_bytes: bytes) -> str:
    """
    OCR με βέλτιστες ρυθμίσεις για ελληνικά συμβόλαια.
    """
    img = Image.open(io.BytesIO(image_bytes))

    # Preprocessing
    img = crop_stamp_area(img, right_crop_pct=0.25)
    img = crop_margins(img, margin_pct=0.03)
    img = full_enhance(img)

    # OCR με PSM 6 (uniform block of text)
    text = pytesseract.image_to_string(
        img,
        lang='ell+eng',
        config='--psm 6 --oem 3'
    )

    # Cleanup μνήμης
    del img
    gc.collect()

    return text.strip()


# ============================================================
# STEP 5: Text Cleaning
# ============================================================

def clean_text(text: str) -> str:
    """
    Καθαρίζει OCR output:
    1. Αφαιρεί noise chars
    2. Κανονικοποιεί whitespace
    3. Αφαιρεί κενές γραμμές
    """
    # Κρατάει ελληνικά, λατινικά, αριθμούς και βασική στίξη
    text = re.sub(r'[^\w\s\.\,\-\(\)\:\;\/\αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩάέήίόύώΆΈΉΊΌΎΏ]', ' ', text)
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) >= 3]
    return '\n'.join(lines).strip()


def split_into_chunks(text: str, max_chars: int = 600) -> list:
    """Κόβει σε chunks για το VLM (context reduction)."""
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

    return chunks if chunks else [text]


# ============================================================
# MAIN PIPELINE
# ============================================================

def preprocess_for_llm(image_bytes: bytes) -> dict:
    """
    Full preprocessing pipeline:
    1. Crop stamps & margins
    2. Enhance (grayscale, deskew, sharpen, threshold)
    3. OCR
    4. Clean text
    5. Split into chunks
    """
    raw_text = extract_text_ocr(image_bytes)
    clean = clean_text(raw_text)
    chunks = split_into_chunks(clean, max_chars=600)

    return {
        "raw_text": raw_text,
        "clean_text": clean,
        "chunks": chunks,
        "total_chars": len(clean),
        "total_chunks": len(chunks)
    }