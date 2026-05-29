# Legal Document Data Extractor
**Synthetica AI — Technical Assessment**

A pipeline for extracting structured data from Greek property deeds (συμβόλαια αγοραπωλησίας) using Vision Language Models (VLM).

---

## Overview

This solution processes scanned Greek legal documents and extracts key information using a hybrid OCR + VLM pipeline:

```
PDF → PyMuPDF → Image → Tesseract OCR → Clean Text → VLM (Ollama) → JSON
```

The Streamlit web application allows users to upload a PDF, select a VLM model and prompt strategy, and view the extracted structured data.

---

## Architecture & Design Decisions

### Why OCR + VLM instead of pure VLM vision?

The documents are **scanned PDFs** (not digital). Direct VLM vision on scanned pages produces poor results because:
- Low image quality after scanning
- Greek stamps and seals create noise
- Small VLMs (1-3B params) struggle with dense scanned text

**Solution**: Use Tesseract OCR to extract clean text first, then send the text to the VLM for structured extraction. This is a common pattern in production document processing systems.

### Why Ollama?

Ollama allows running VLMs locally inside Docker — no API keys needed, fully self-contained deployment.

### Model Selection

| Model | Size | Speed | Accuracy | Requirement |
|-------|------|-------|----------|-------------|
| moondream | 1.7GB | Slow on CPU | Low | Any machine |
| qwen2.5vl:3b | 3.2GB | Fast on GPU | High | GPU (Colab T4) |
| llava:7b | 4.7GB | Very slow on CPU | Medium | GPU |

**Default**: moondream (runs on any machine with Docker)
**Recommended**: qwen2.5vl:3b via Google Colab T4 GPU

---

## Preprocessing Pipeline

The image preprocessing pipeline (in `preprocessor.py`) applies the following steps before OCR:

1. **Crop stamp area** — removes right 25% of page (stamps, seals)
2. **Crop margins** — removes page borders
3. **Grayscale** — reduces memory, improves OCR
4. **Deskew** — corrects page rotation
5. **Sharpen** — improves text clarity
6. **Enhance contrast** — makes text more readable
7. **Adaptive thresholding** — binarizes image for optimal OCR
8. **Text cleaning** — removes OCR noise characters
9. **Chunk splitting** — splits text into manageable pieces for VLM context

---

## Prompt Strategies

Three prompting strategies are implemented in `prompts.py`:

| Strategy | Description | Best For |
|----------|-------------|----------|
| zero_shot | Direct extraction without examples | Speed |
| chain_of_thought | Step-by-step reasoning before extraction | Accuracy |
| few_shot | Includes example input/output | Balanced |

### 1. Cloud GPU Evaluation & Comparative Experiments (qwen2.5vl:3b, Colab T4)

We executed **3 distinct validation experiments** on the cloud GPU infrastructure to benchmark prompt strategies, error handler resilience, and full-scale production throughput.

#### Experiment 1: Prompt Engineering Strategy Benchmark
* **Objective:** Compare extraction performance across the three prompt strategies (`zero_shot`, `chain_of_thought`, `few_shot`) using a 3-page document slice.
* **Resulting Artifact:** `evaluation_results.json`

| Strategy | Avg Time (s) | Fields Found | GT Score (0-5) | JSON Valid Rate | Error Rate | Sellers | Buyers | Properties |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **zero_shot** | 22.15 | 14 | 1 | 1.00 | 0.00 | 2 | 2 | 3 |
| **chain_of_thought** | 22.76 | 18 | 2 | 1.00 | 0.00 | 4 | 4 | 3 |
| **few_shot** | 16.77 | 5 | 2 | 1.00 | 0.00 | 1 | 0 | 0 |

*Key Takeaway:* `chain_of_thought` proved to be the most accurate strategy, mapping deep nested relationships (4 Sellers/4 Buyers), while `few_shot` was the fastest but suffered from severe text truncation across multi-page contexts.

#### Experiment 2: Pipeline Robustness & Page-by-Page Validation
* **Objective:** Verify page-by-page system stability under persistent inference loads using the validation container layers.
* **Resulting Artifact:** `results_with_handler.json`
* **Metrics:** Successfully isolated granular processing anomalies per page, ensuring that formatting bugs were intercepted before moving data objects into the compiler stage.

#### Experiment 3: Full-Scale End-to-End Production Run
* **Objective:** Process the entire 23-page deed contract sequentially using the optimal configuration (`chain_of_thought` + `error_handler`) and compile them into a unified dataset.
* **Resulting Artifact:** `final_results_full.json`
* **Performance Metrics:**
  - **Total Runtime:** 527 seconds (~8.8 minutes)
  - **Total Data Objects Captured:** 42 dense legal attributes
  - **Aggregated Output Tree:** 9 Sellers, 9 Buyers, 8 Representatives, and 12 distinct Property segments merged seamlessly into a single JSON schema.
  - **Pipeline Recovery Rate:** ~13% error intervention (The retry mechanism caught and repaired 3 initially malformed layouts mid-run).

 
### 2. Local CPU Evaluation (moondream benchmark across all strategies)

Tested fully locally inside the core Docker container (1 page per strategy) to benchmark localized performance and architectural constraints on restricted environments:

<img width="571" height="525" alt="αρχείο λήψης" src="https://github.com/user-attachments/assets/1a4365d2-65d8-48a2-876d-47875dfd3292" />

<img width="571" height="525" alt="αρχείο λήψης (1)" src="https://github.com/user-attachments/assets/ae3dab95-559c-4fae-bb17-3d1730657c74" />

| Prompt | Avg Time (s) | Fields Found | GT Score (0-5) | JSON Valid Rate | Error Rate | Sellers | Buyers | Properties |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **zero_shot** | 110.25 | 4 | 0 | 1.00 | 0.00 | 0 | 0 | 0 |
| **chain_of_thought** | 114.16 | 4 | 0 | 1.00 | 0.00 | 0 | 0 | 0 |
| **few_shot** | 319.60 | 4 | 1 | 0.33 | 0.67 | 0 | 0 | 0 |


#### Local Architectural Conclusions & Logs Analysis

* **The Few-Shot Context Bottleneck:** The `few_shot` strategy caused a massive performance degradation, skyrocketing execution time to **319.6 seconds** with a **67% Error Rate**. Because `moondream` is a 1.6B parameter model, stuffing the prompt context with full example deeds overwhelms the CPU, causing heavy token processing delays and container timeouts.
* **Strict JSON Mode Stability:** Both `zero_shot` and `chain_of_thought` maintained a **100% JSON Valid Rate**, proving that our explicit API schema enforcement layer successfully forces the localized model to adhere to the requested structure.
* **Error Handler Interception:** During the `few_shot` breakdown, the pipeline's runtime intercepted the failures, logging standard schema validation anomalies:  
  `WARNING:error_handler:Validation warnings: ['Missing key: sellers', 'Missing key: buyers', 'Missing key: properties']`  
  The framework safely recovered by dynamically injecting empty structural fallbacks (`[]`), keeping the Streamlit UI responsive and preventing application crashes.
* **Linguistic Hardware Limits:** While `few_shot` managed to guess 1 ground truth entity correctly, all local runs suffered from phonetic character hallucinations on dense Greek legal strings (e.g., parsing the Notary Address as `ΑΡΙΜΟΥΙΣΠΕΔΡΑΣΤΟΥ ΓΣΛΑΣΚΗΣΙΑ`). This confirms that routing reasoning tasks to the larger **Qwen2.5-VL via GPU (Option B)** remains mandatory for actual production deployment.

#### Raw Extracted JSON Output (Moondream Local Fallback)
```json
{
  "contract_number": "86",
  "contract_date": "19.924",
  "notary": {
    "name": "Συνάθητο",
    "address": "ΑΡΙΜΟΥΙΣΠΕΔΡΑΣΤΟΥ ΓΣΛΑΣΚΗΣΙΑ"
  },
  "sellers": [],
  "buyers": [],
  "representatives": [],
  "properties": []
}
```

## Error Handling

The `error_handler.py` module provides:
- **Retry mechanism**: automatically retries failed extractions (up to 2 attempts)
- **Result validation**: checks JSON structure and fixes missing keys
- **Safe extraction**: safe_extract_from_page() wraps all extractions

During the full PDF evaluation, the error handler successfully recovered 3 pages that initially returned invalid JSON.

---

## Multiple Document Types

The `document_types.py` module supports auto-detection of:
- **Αγοραπωλησία** (Property Sale Deed) — default
- **Γονική Παροχή** (Parental Provision) — seller=parent, buyer=child
- **Μίσθωση** (Lease Agreement)
- **Δωρεά** (Donation Deed)

The document type is auto-detected from OCR text and a type-specific prompt is used for better extraction.

---

## Extracted Fields

| Category | Fields |
|----------|--------|
| Contract | number, date |
| Notary | name, address |
| Sellers | name, AFM (tax ID), address, ID document |
| Buyers | name, AFM, address, ID document |
| Representatives | name, who they represent, ID document |
| Properties | type, location, municipality, block, area (sqm), floor, KAEK, building permit |

---

## Performance Optimization — Implemented

| Bottleneck | Solution | Status |
|-----------|----------|--------|
| CPU inference is slow | GPU inference via Google Colab T4 | Implemented (`colab_inference.ipynb`) |
| Full document takes too long | Page slider in UI to limit pages processed | Implemented (sidebar slider 1-23 pages) |
| Large model won't fit in RAM | Quantized models (Q4_K_M) via Ollama | Applied (qwen2.5vl:3b = 3.2GB) |
| VLM context window limits | Text chunking in preprocessor | Implemented (`split_into_chunks()`) |
| Repeated extraction on same doc | Results saved to JSON (no re-inference needed) | Implemented (`save_results()`) |
| Batch/parallel processing | Sequential inference to avoid OOM on low RAM | Implemented with `gc.collect()` per page |

---

## Setup & Run

### Option A — Docker (Recommended, CPU)

**Requirements**: Docker Desktop

```bash
git clone https://github.com/georgiahdj/legal-doc-extractor.git
cd legal-doc-extractor
docker compose up --build
```

Open: **http://localhost:8501**

> **Note**: First run downloads the moondream model (~1.7GB). This may take 5-10 minutes. Inference is slow on CPU (~2-5 minutes per page).

### Option B — Docker + Colab GPU (Best results)

For fast, accurate inference using Google Colab T4 GPU:

1. Open `colab_inference.ipynb` in Google Colab
2. Set runtime to **T4 GPU**
3. Run all cells — note the cloudflared URL printed at the end
4. Update `.env` and `docker-compose.yml`:
```
OLLAMA_HOST=https://your-tunnel-url.trycloudflare.com
VLM_MODEL=qwen2.5vl:3b
```
5. Run `docker compose up --build`
6. Open **http://localhost:8501**

### Option C — Local Python (without Docker)

```bash
pip install -r requirements.txt
# Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
# Install Ollama: https://ollama.com
ollama pull moondream
streamlit run app.py
```

---

## Project Structure

```
├── app.py                  # Streamlit UI
├── extractor.py            # PDF to images, merge results
├── preprocessor.py         # Image preprocessing & OCR
├── ollama_extractor.py     # VLM extraction via Ollama
├── evaluator.py            # Prompt strategy evaluation
├── prompts.py              # Prompt templates (3 strategies)
├── error_handler.py        # Robust error handling & retry
├── document_types.py       # Multi-document type support
├── colab_inference.ipynb   # Google Colab GPU notebook
├── docker-compose.yml      # Docker setup
├── Dockerfile
└── requirements.txt
```

---

## Assumptions

1. Documents are Greek property deeds (αγοραπωλησίες)
2. PDFs are scanned (not digital text) — OCR is required
3. The VLM may not extract all fields perfectly — this is expected for small models on CPU
4. For production use, a larger model with GPU would significantly improve accuracy
