import os
import re
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from sentence_transformers import SentenceTransformer
from backend.database.db import db_session
from backend.models.document import UploadedDocument
from backend.models.flashcard import Flashcard
from backend.models.keyword import Keyword
from backend.nlp.extractor import run_nlp_pipeline, nlp
from flask import current_app

# Lazy loaded NLP model singletons
_t5_tokenizer = None
_t5_model = None
_similarity_model = None

def get_t5_models():
    """Lazy load tokenizer and model for T5-small, returning None on failure."""
    global _t5_tokenizer, _t5_model
    if _t5_model is None:
        model_name = "t5-small"
        try:
            _t5_tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
            _t5_model = AutoModelForSeq2SeqLM.from_pretrained(model_name, local_files_only=True)
        except Exception:
            _t5_tokenizer = None
            _t5_model = None
    return _t5_tokenizer, _t5_model

def get_similarity_model():
    """Lazy load SentenceTransformer model, returning None on failure."""
    global _similarity_model
    if _similarity_model is None:
        try:
            _similarity_model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
        except Exception:
            _similarity_model = None
    return _similarity_model

def clean_sentence_for_cloze(sentence, answer):
    """Ensure casing and punctuation are clean for cloze deletion."""
    # Find answer with word boundaries in case-insensitive manner
    pattern = re.compile(r'\b' + re.escape(answer) + r'\b', re.IGNORECASE)
    # Check if answer exists in sentence
    if pattern.search(sentence):
        return pattern.sub("_____", sentence), answer
    
    # Fallback: substring replacement if boundary fails
    if answer.lower() in sentence.lower():
        idx = sentence.lower().find(answer.lower())
        cloze = sentence[:idx] + "_____" + sentence[idx + len(answer):]
        # Return exact answer capitalization from sentence
        actual_answer = sentence[idx:idx + len(answer)]
        return cloze, actual_answer
        
    return None

def select_answer_candidates(sentence_text, doc_keywords, doc_entities):
    """Analyze a sentence and pick the best noun/entity/keyword candidate as the answer."""
    if nlp is None:
        return None

    try:
        doc = nlp(sentence_text)
    except Exception:
        return None

    # 1. Look for Named Entities in this sentence
    sent_ents = [ent.text for ent in doc.ents if ent.label_ not in ['CARDINAL', 'QUANTITY', 'DATE', 'TIME']]
    for ent in sent_ents:
        # Check if ent matches any doc keywords or is prominent
        if any(ent.lower() in kw.lower() or kw.lower() in ent.lower() for kw in doc_keywords):
            return ent

    # 2. Check if any exact doc keywords are in this sentence
    for kw in doc_keywords:
        pattern = re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
        if pattern.search(sentence_text):
            return kw

    # 3. Fallback: check noun chunks in the sentence
    try:
        noun_chunks = [chunk.text for chunk in doc.noun_chunks if len(chunk.text.split()) < 4]
    except Exception:
        noun_chunks = []
    if noun_chunks:
        # Sort by length descending to pick most specific noun chunk
        noun_chunks.sort(key=len, reverse=True)
        return noun_chunks[0]

    # 4. Fallback: use a simple keyword-based answer if no NLP structure is available
    if doc_keywords:
        for kw in doc_keywords:
            if kw and kw.lower() in sentence_text.lower():
                return kw

    return None

def generate_question_t5(sentence, answer):
    """Use local T5-small to translate statement into a question about the answer."""
    tokenizer, model = get_t5_models()
    if tokenizer is None or model is None:
        return None

    # Standard T5 translation-like instruction to formulate a question
    prompt = f"translate English to English: generate question: {sentence} answer: {answer}"
    
    try:
        inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=64,
                num_beams=4,
                early_stopping=True
            )
        question = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        
        # Post-processing validation
        if question and len(question) > 10 and ("?" in question or any(q in question.lower() for q in ["what", "who", "where", "how", "why"])):
            # Ensure question capitalization
            if not question.endswith("?"):
                question += "?"
            return question[0].upper() + question[1:]
    except Exception:
        return None
        
    return None

def create_cloze_question(sentence, answer):
    """Create a fill-in-the-blank (cloze deletion) question as a bulletproof fallback."""
    res = clean_sentence_for_cloze(sentence, answer)
    if res:
        cloze_text, actual_answer = res
        question = f"Complete the statement: \"{cloze_text}\""
        return question, actual_answer
    return None, None

def deduplicate_flashcards(candidates, similarity_threshold=0.85):
    """Group and filter semantically identical questions using SentenceTransformers."""
    if not candidates:
        return []
        
    sim_model = get_similarity_model()
    questions = [c["question"] for c in candidates]
    
    try:
        if sim_model is None:
            raise RuntimeError("Similarity model unavailable")
        embeddings = sim_model.encode(questions, convert_to_tensor=True)
        # Compute cosine similarity matrix
        # (normalized embeddings matrix multiplication yields cosine similarity)
        norm_embeddings = embeddings / embeddings.norm(dim=1, keepdim=True)
        sim_matrix = torch.mm(norm_embeddings, norm_embeddings.t()).cpu().numpy()
    except Exception:
        # Fallback to exact text duplication checking if SentenceTransformer fails
        seen = set()
        unique_candidates = []
        for c in candidates:
            q_clean = re.sub(r'\s+', ' ', c["question"].lower().strip())
            if q_clean not in seen:
                seen.add(q_clean)
                unique_candidates.append(c)
        return unique_candidates

    keep_indices = []
    removed = set()
    
    for i in range(len(candidates)):
        if i in removed:
            continue
        keep_indices.append(i)
        
        # Find similar questions to suppress
        for j in range(i + 1, len(candidates)):
            if sim_matrix[i, j] > similarity_threshold:
                removed.add(j)
                
    return [candidates[idx] for idx in keep_indices]

def generate_flashcards_from_doc(document_id, topic_id=None, num_cards=10):
    """Run extraction, generate QA pairs, deduplicate, and seed the database."""
    # 1. Run pipeline to extract sentence components, keywords, and entities
    pipeline_data = run_nlp_pipeline(document_id)
    sentences = pipeline_data["sentences"]
    keywords = [k["word"] for k in pipeline_data["keywords"]]
    entities = [e["text"] for e in pipeline_data["entities"]]

    # Fetch document record to know which user owns it
    doc_record = db_session.get(UploadedDocument, document_id)
    user_id = doc_record.user_id

    candidates = []
    
    # 2. Iterate sentences and generate QA pairs
    for sentence in sentences:
        if len(sentence.split()) < 7 or len(sentence.split()) > 35:
            continue  # Ignore too short or overly complex sentences

        answer = select_answer_candidates(sentence, keywords, entities)
        if not answer:
            answer = sentence.split()[0]

        # Try T5 question generation
        question = generate_question_t5(sentence, answer)
        final_answer = answer
        
        # If T5 fails or yields weak output, fallback to Cloze question
        if not question:
            question, final_answer = create_cloze_question(sentence, answer)
            
        if question and final_answer:
            candidates.append({
                "question": question,
                "answer": final_answer,
                "sentence": sentence
            })

    # 3. Deduplicate semantically
    unique_candidates = deduplicate_flashcards(candidates, similarity_threshold=0.85)

    # 4. Limit to requested count
    final_cards = unique_candidates[:num_cards]

    # 5. Save flashcards to DB
    created_cards = []
    try:
        # Delete old flashcards generated for this document to enable clean regeneration
        db_session.query(Flashcard).filter_by(document_id=document_id).delete()
        
        for card in final_cards:
            db_card = Flashcard(
                user_id=user_id,
                document_id=document_id,
                topic_id=topic_id,
                question=card["question"],
                answer=card["answer"],
                difficulty='medium',
                is_favorite=False
            )
            db_session.add(db_card)
            created_cards.append(db_card)
            
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise IOError(f"Database error writing flashcards: {str(e)}") from e

    return [
        {
            "id": c.id,
            "question": c.question,
            "answer": c.answer,
            "difficulty": c.difficulty,
            "is_favorite": c.is_favorite
        } for c in created_cards
    ]
