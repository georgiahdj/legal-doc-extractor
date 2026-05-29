from preprocessor import preprocess_for_llm
from extractor import pdf_to_images

images = pdf_to_images('data/simbolaio-agorapolisias-public.pdf')
result = preprocess_for_llm(images[0])
print("Chars:", result["total_chars"])
print("Chunks:", result["total_chunks"])
print("--- Chunk 1 ---")
print(result["chunks"][0])