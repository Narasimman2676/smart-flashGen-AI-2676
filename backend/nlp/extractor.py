import os
import re
import nltk
import spacy
from backend.database.db import db_session
from backend.models.document import UploadedDocument
from backend.models.keyword import Keyword
from flask import current_app

# Download NLTK data if not present
def init_nltk():
    """Download required NLTK datasets in a fail-safe manner."""
    for package in ['punkt', 'punkt_tab', 'stopwords']:
        try:
            if package == 'punkt':
                nltk.data.find('tokenizers/punkt')
            elif package == 'punkt_tab':
                nltk.data.find('tokenizers/punkt_tab')
            else:
                nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download(package, quiet=True)

init_nltk()

# Load spaCy model dynamically
def get_spacy_nlp():
    """Load a spaCy model if available; otherwise fall back to a blank English pipeline."""
    if os.getenv("LOW_MEMORY_MODE", "False").lower() == "true":
        try:
            return spacy.blank("en")
        except Exception:
            return None
    try:
        return spacy.load("en_core_web_sm")
    except Exception:
        try:
            return spacy.blank("en")
        except Exception:
            return None

nlp = get_spacy_nlp()

# Lazy-loaded KeyBERT singleton
_kw_model = None

def get_keybert_model():
    """Get or initialize the KeyBERT model, returning None on failure."""
    global _kw_model
    if os.getenv("LOW_MEMORY_MODE", "False").lower() == "true":
        return None
    if _kw_model is None:
        try:
            from keybert import KeyBERT
            _kw_model = KeyBERT()
        except Exception:
            _kw_model = None
    return _kw_model

def clean_text(text):
    """Normalize whitespace and remove non-printable characters."""
    if not text:
        return ""
    # Standardize whitespace and remove control characters
    text = re.sub(r'[\r\n]+', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    # Remove non-ASCII printable chars, but keep accents/common symbols
    text = ''.join(c for c in text if c.isprintable() or c == '\n')
    return text.strip()

def tokenize_sentences(text):
    """Split text into sentences using NLTK."""
    cleaned = clean_text(text)
    if not cleaned:
        return []
    return nltk.sent_tokenize(cleaned)

def extract_keywords(text, top_n=10):
    """Extract keywords/keyphrases using KeyBERT."""
    cleaned = clean_text(text)
    if not cleaned:
        return []
    
    # Restrict top_n if text is extremely short
    words_count = len(cleaned.split())
    if words_count < 5:
        return []
        
    kw_extractor = get_keybert_model()
    if kw_extractor is None:
        words = re.findall(r'\b[a-zA-Z]{3,}\b', cleaned.lower())
        from nltk.corpus import stopwords
        stop_words = set(stopwords.words('english'))
        filtered_words = [w for w in words if w not in stop_words]
        
        from collections import Counter
        counts = Counter(filtered_words).most_common(top_n)
        total = sum(counts[1] for counts in counts) or 1
        return [(word, count / total) for word, count in counts]
    try:
        # Extract single words and short phrases
        raw_keywords = kw_extractor.extract_keywords(
            cleaned, 
            keyphrase_ngram_range=(1, 2), 
            stop_words='english', 
            top_n=top_n
        )
        return raw_keywords
    except Exception as e:
        # Fallback to simple NLTK/regex term frequency if KeyBERT fails (fail-safe)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', cleaned.lower())
        from nltk.corpus import stopwords
        stop_words = set(stopwords.words('english'))
        filtered_words = [w for w in words if w not in stop_words]
        
        from collections import Counter
        counts = Counter(filtered_words).most_common(top_n)
        total = sum(counts[1] for counts in counts) or 1
        return [(word, count / total) for word, count in counts]

def extract_entities(text):
    """Extract Named Entities using spaCy."""
    cleaned = clean_text(text)
    if not cleaned:
        return []
        
    if nlp is None:
        return []

    doc = nlp(cleaned)
    entities = []
    seen = set()
    
    for ent in doc.ents:
        # Filter out numbers and generic entities to keep high-value noun entities
        if ent.label_ in ['QUANTITY', 'CARDINAL', 'ORDINAL', 'PERCENT', 'MONEY']:
            continue
            
        entity_key = (ent.text.strip(), ent.label_)
        if entity_key not in seen and len(ent.text.strip()) > 1:
            seen.add(entity_key)
            entities.append({
                "text": ent.text.strip(),
                "label": ent.label_
            })
            
    return entities

def run_nlp_pipeline(document_id):
    """Extract content, clean, tokenise, extract entities & keywords, and save to DB."""
    # Fetch UploadedDocument from DB
    doc_record = db_session.get(UploadedDocument, document_id)
    if not doc_record:
        raise ValueError(f"Document with ID {document_id} not found.")

    # Find the extracted text companion file
    if current_app:
        upload_folder = current_app.config['UPLOAD_FOLDER']
    else:
        # Fallback for testing/standalone script runs
        from backend.config.config import Config
        upload_folder = Config.UPLOAD_FOLDER
        
    extracted_text_path = os.path.join(upload_folder, "extracted", f"{document_id}.txt")
    if not os.path.exists(extracted_text_path):
        raise FileNotFoundError(f"Extracted text file not found at: {extracted_text_path}")

    with open(extracted_text_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    cleaned = clean_text(raw_text)
    sentences = tokenize_sentences(cleaned)
    entities = extract_entities(cleaned)
    keywords = extract_keywords(cleaned, top_n=10)

    try:
        # Delete existing keywords if re-running pipeline
        db_session.query(Keyword).filter_by(document_id=document_id).delete()
        
        # Save extracted keywords to the Keyword table
        for word, score in keywords:
            db_kw = Keyword(
                word=word,
                importance_score=score,
                document_id=document_id
            )
            db_session.add(db_kw)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise IOError(f"Database error writing keywords: {str(e)}") from e

    return {
        "keywords": [{"word": k, "score": s} for k, s in keywords],
        "entities": entities,
        "sentences_count": len(sentences),
        "sentences": sentences
    }
