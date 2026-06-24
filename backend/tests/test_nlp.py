import os
import pytest
from backend.app import create_app
from backend.config.config import Config
from backend.database.db import db_session
from backend.models import User, UploadedDocument, Keyword
from backend.nlp.extractor import (
    clean_text,
    tokenize_sentences,
    extract_keywords,
    extract_entities,
    run_nlp_pipeline
)

# Test setup variables
test_nlp_db = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_nlp.db"))
test_db_url = f"sqlite:///{test_nlp_db}"
test_upload_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_nlp_uploads"))

class TestConfig(Config):
    TESTING = True
    DATABASE_URL = test_db_url
    UPLOAD_FOLDER = test_upload_folder

@pytest.fixture(scope="module")
def app():
    # Remove files if exist
    if os.path.exists(test_nlp_db):
        try:
            os.remove(test_nlp_db)
        except PermissionError:
            pass

    app = create_app(TestConfig)
    
    yield app

    # Teardown database
    db_session.remove()
    from backend.database.db import engine
    engine.dispose()
    
    if os.path.exists(test_nlp_db):
        try:
            os.remove(test_nlp_db)
        except PermissionError:
            pass
            
    # Clean up test uploads directory
    if os.path.exists(test_upload_folder):
        import shutil
        shutil.rmtree(test_upload_folder, ignore_errors=True)

@pytest.fixture(autouse=True)
def clean_db_and_files(app):
    with app.app_context():
        db_session.query(Keyword).delete()
        db_session.query(UploadedDocument).delete()
        db_session.query(User).delete()
        db_session.commit()
        
    if os.path.exists(test_upload_folder):
        import shutil
        shutil.rmtree(test_upload_folder, ignore_errors=True)
    os.makedirs(test_upload_folder, exist_ok=True)
    os.makedirs(os.path.join(test_upload_folder, "extracted"), exist_ok=True)
    yield

def test_clean_text():
    """Verify that clean_text removes double spaces and raw control chars."""
    raw = "Hello   world!\x00 This is\n\n a   sentence\twith tabs."
    cleaned = clean_text(raw)
    assert "  " not in cleaned
    assert "\x00" not in cleaned
    assert "Hello world!" in cleaned
    assert "tabs." in cleaned

def test_tokenize_sentences():
    """Verify sentence segmentation splitting is accurate."""
    text = "First sentence. Second sentence! Is this the third? Yes, indeed."
    sents = tokenize_sentences(text)
    assert len(sents) == 4
    assert sents[0] == "First sentence."
    assert sents[1] == "Second sentence!"
    assert sents[2] == "Is this the third?"
    assert sents[3] == "Yes, indeed."

def test_extract_keywords():
    """Verify KeyBERT keyword extraction extracts relevant phrases."""
    text = (
        "Supervised machine learning algorithms build a mathematical model of a set of data "
        "that contains both the inputs and the desired outputs. The data is known as training data, "
        "and consists of a set of training examples."
    )
    keywords = extract_keywords(text, top_n=3)
    assert len(keywords) > 0
    # KeyBERT output should be a list of tuples (keyword, score)
    for kw, score in keywords:
        assert isinstance(kw, str)
        assert isinstance(score, float)
    
    # Check if key ML terms are captured
    words = [k[0] for k in keywords]
    assert any("machine" in w or "learning" in w or "algorithms" in w or "training" in w for w in words)

def test_extract_entities():
    """Verify spaCy NER captures proper locations and organizations."""
    text = "Steve Jobs co-founded Apple Inc. in Cupertino, California on April 1, 1976."
    entities = extract_entities(text)
    
    entity_texts = [e["text"] for e in entities]
    entity_labels = [e["label"] for e in entities]
    
    # Apple Inc should be ORG
    assert "Apple Inc." in entity_texts or "Apple" in entity_texts
    # Steve Jobs should be PERSON
    assert "Steve Jobs" in entity_texts
    # Cupertino or California should be GPE
    assert "Cupertino" in entity_texts or "California" in entity_texts
    
    # Verify entity labels are appropriate
    assert "ORG" in entity_labels
    assert "PERSON" in entity_labels
    assert "GPE" in entity_labels

def test_run_nlp_pipeline(app):
    """Test full pipeline database save and file reading integrations."""
    # 1. Create a dummy User & UploadedDocument
    with app.app_context():
        user = User(email="nlp_test@example.com", password_hash="pass")
        db_session.add(user)
        db_session.commit()
        
        doc = UploadedDocument(
            user_id=user.id,
            filename="ml_doc.txt",
            file_path="/mock/ml_doc.txt",
            file_type="txt",
            file_size=500,
            status="completed"
        )
        db_session.add(doc)
        db_session.commit()
        
        doc_id = doc.id
        
    # 2. Write raw text companion file to mock disk
    text_content = (
        "Artificial intelligence and deep learning are revolutionary technologies. "
        "Neural networks process large amounts of visual data to identify objects. "
        "Google and Microsoft are investing billions in AI research labs in London."
    )
    
    extracted_text_path = os.path.join(test_upload_folder, "extracted", f"{doc_id}.txt")
    with open(extracted_text_path, 'w', encoding='utf-8') as f:
        f.write(text_content)

    # 3. Run the pipeline
    with app.app_context():
        res = run_nlp_pipeline(doc_id)
        
        # Verify returned structure
        assert "keywords" in res
        assert "entities" in res
        assert "sentences" in res
        assert res["sentences_count"] == 3
        
        # Verify keywords were written to the database
        db_kws = db_session.query(Keyword).filter_by(document_id=doc_id).all()
        assert len(db_kws) > 0
        db_words = [k.word for k in db_kws]
        assert any("intelligence" in w or "learning" in w or "ai" in w or "networks" in w for w in db_words)
        
        # Verify relationships can be walked
        db_doc = db_session.get(UploadedDocument, doc_id)
        assert len(db_doc.keywords) == len(db_kws)
