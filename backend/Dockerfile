# Use an official lightweight Python 3.10 image
FROM python:3.10-slim

# Set environment variables for Python and Hugging Face
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/tmp/hf_cache \
    PORT=7860

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Gunicorn, PostgreSQL adapter, and all requirements
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir gunicorn psycopg2-binary && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download spaCy models and Hugging Face models into the image
# This ensures fast container startup times and offline model loading
RUN python -m spacy download en_core_web_sm && \
    python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True); nltk.download('stopwords', quiet=True)" && \
    python -c "from transformers import AutoTokenizer, AutoModelForSeq2SeqLM; AutoTokenizer.from_pretrained('t5-small'); AutoModelForSeq2SeqLM.from_pretrained('t5-small'); from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy the entire backend directory into the /app/backend folder
COPY . ./backend

# Expose port 7860 (Hugging Face Spaces default)
EXPOSE 7860

# Run the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "1", "--timeout", "180", "backend.wsgi:app"]
