FROM python:3.11-slim

WORKDIR /app

# Install Tesseract with Greek language
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ell \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]