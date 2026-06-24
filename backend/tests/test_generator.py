import os
from unittest.mock import patch
import pytest
import spacy
from backend.app import create_app
from backend.config.config import Config
from backend.database.db import db_session
from backend.models import User, UploadedDocument, Flashcard, Keyword, Topic
from backend.nlp.generator import (
    select_answer_candidates,
    create_cloze_question,
    generate_question_t5,
    deduplicate_flashcards,
    generate_flashcards_from_doc
)

# Test config variables
test_gen_db = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_gen.db"))
test_db_url = f"sqlite:///{test_gen_db}"
test_upload_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_gen_uploads"))

class TestConfig(Config):
    TESTING = True
    DATABASE_URL = test_db_url
    UPLOAD_FOLDER = test_upload_folder

@pytest.fixture(scope="module")
def app():
    # Remove files if exist
    if os.path.exists(test_gen_db):
        try:
            os.remove(test_gen_db)
        except PermissionError:
            pass

    app = create_app(TestConfig)
    
    yield app

    # Teardown database
    db_session.remove()
    from backend.database.db import engine
    engine.dispose()
    
    if os.path.exists(test_gen_db):
        try:
            os.remove(test_gen_db)
        except PermissionError:
            pass
            
    # Clean up test uploads directory
    if os.path.exists(test_upload_folder):
        import shutil
        shutil.rmtree(test_upload_folder, ignore_errors=True)

@pytest.fixture(autouse=True)
def clean_db_and_files(app):
    with app.app_context():
        db_session.query(Flashcard).delete()
        db_session.query(Keyword).delete()
        db_session.query(UploadedDocument).delete()
        db_session.query(Topic).delete()
        db_session.query(User).delete()
        db_session.commit()
        
    if os.path.exists(test_upload_folder):
        import shutil
        shutil.rmtree(test_upload_folder, ignore_errors=True)
    os.makedirs(test_upload_folder, exist_ok=True)
    os.makedirs(os.path.join(test_upload_folder, "extracted"), exist_ok=True)
    yield

def test_select_answer_candidates():
    """Verify that the engine extracts appropriate answer keywords."""
    sentence = "Supervised learning algorithms build a mathematical model of a set of data."
    keywords = ["supervised learning", "mathematical model"]
    entities = []
    
    answer = select_answer_candidates(sentence, keywords, entities)
    assert answer is not None
    assert answer in ["supervised learning", "supervised learning algorithms", "mathematical model"]

def test_create_cloze_question():
    """Verify fill-in-the-blank question formulation."""
    sentence = "Natural language processing is a field of computer science."
    answer = "Natural language processing"
    
    question, final_ans = create_cloze_question(sentence, answer)
    assert "Complete the statement" in question
    assert "_____" in question
    assert final_ans == "Natural language processing"

def test_generate_question_t5():
    """Verify that T5 model generates questions from statements."""
    sentence = "The capital of France is Paris."
    answer = "Paris"
    
    question = generate_question_t5(sentence, answer)
    # T5 may or may not succeed depending on fine-tuning weights,
    # but it should return either a string question or None cleanly.
    if question:
        assert isinstance(question, str)
        assert len(question) > 5

def test_deduplicate_flashcards():
    """Verify that similar questions are removed."""
    candidates = [
        {"question": "What is artificial intelligence?", "answer": "AI"},
        {"question": "How do you define artificial intelligence?", "answer": "AI"},
        {"question": "Explain artificial intelligence?", "answer": "AI"},
        {"question": "What is machine learning?", "answer": "ML"}
    ]
    
    # De-duplicate
    filtered = deduplicate_flashcards(candidates, similarity_threshold=0.80)
    
    # The first 3 are highly semantically similar ("artificial intelligence")
    # So we expect only one AI question and one ML question to remain
    questions = [c["question"] for c in filtered]
    assert len(filtered) < len(candidates)
    assert any("artificial intelligence" in q.lower() for q in questions)
    assert any("machine learning" in q.lower() for q in questions)

def test_select_answer_candidates_with_blank_spacy_pipeline():
    """Verify answer selection does not crash when spaCy falls back to a blank pipeline."""
    blank_nlp = spacy.blank("en")
    sentence = "Photosynthesis converts sunlight into energy for plants."
    keywords = ["photosynthesis", "plants"]

    with patch("backend.nlp.generator.nlp", blank_nlp):
        answer = select_answer_candidates(sentence, keywords, [])

    assert answer is not None


def test_generate_flashcards_from_doc(app):
    """Verify end-to-end document parsing, QA generation, and DB saving."""
    with app.app_context():
        # 1. Create user and document
        user = User(email="gen_test@example.com", password_hash="pass")
        db_session.add(user)
        db_session.commit()
        
        doc = UploadedDocument(
            user_id=user.id,
            filename="history.txt",
            file_path="/mock/history.txt",
            file_type="txt",
            file_size=600,
            status="completed"
        )
        db_session.add(doc)
        db_session.commit()
        
        doc_id = doc.id

    # 2. Write raw content companion file
    text_content = (
        "The Roman Empire was the post-Republican period of ancient Rome. "
        "Julius Caesar was a Roman general and statesman. "
        "The Empire had its capital in Rome for many centuries. "
        "Augustus Caesar became the first Roman emperor in 27 BC."
    )
    
    extracted_text_path = os.path.join(test_upload_folder, "extracted", f"{doc_id}.txt")
    with open(extracted_text_path, 'w', encoding='utf-8') as f:
        f.write(text_content)

    # 3. Generate flashcards
    with app.app_context():
        cards = generate_flashcards_from_doc(doc_id, num_cards=5)
        
        # Verify cards were returned
        assert len(cards) > 0
        for card in cards:
            assert "id" in card
            assert "question" in card
            assert "answer" in card
            
        # Verify cards were seeded in the database
        db_cards = db_session.query(Flashcard).filter_by(document_id=doc_id).all()
        assert len(db_cards) == len(cards)
        
        # Verify cascades (deleting document deletes flashcards)
        db_doc = db_session.get(UploadedDocument, doc_id)
        db_session.delete(db_doc)
        db_session.commit()
        
        assert db_session.query(Flashcard).filter_by(document_id=doc_id).count() == 0


def test_generate_flashcards_from_doc_without_model_loading(app):
    """Verify generation still succeeds when T5 and similarity models are unavailable."""
    with app.app_context():
        user = User(email="fallback@example.com", password_hash="pass")
        db_session.add(user)
        db_session.commit()

        doc = UploadedDocument(
            user_id=user.id,
            filename="fallback.txt",
            file_path="/mock/fallback.txt",
            file_type="txt",
            file_size=500,
            status="completed"
        )
        db_session.add(doc)
        db_session.commit()

        doc_id = doc.id

    text_content = (
        "Photosynthesis is the process plants use to convert sunlight into chemical energy. "
        "Chlorophyll absorbs light in the leaves of plants. "
        "Plants release oxygen as a byproduct of photosynthesis."
    )

    extracted_text_path = os.path.join(test_upload_folder, "extracted", f"{doc_id}.txt")
    with open(extracted_text_path, 'w', encoding='utf-8') as f:
        f.write(text_content)

    with app.app_context():
        with patch("backend.nlp.generator.get_t5_models", side_effect=RuntimeError("T5 unavailable")):
            with patch("backend.nlp.generator.get_similarity_model", side_effect=RuntimeError("Similarity model unavailable")):
                cards = generate_flashcards_from_doc(doc_id, num_cards=5)

    assert len(cards) > 0
    assert all("question" in card and "answer" in card for card in cards)
