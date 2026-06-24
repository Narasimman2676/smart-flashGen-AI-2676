import os
import pytest
import datetime
from backend.app import create_app
from backend.config.config import Config
from backend.database.db import db_session
from backend.models import User, Topic, UploadedDocument, Flashcard, QuizHistory, LearningProgress, TokenBlocklist

# Separate database for analytics testing
test_analytics_db = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_analytics.db"))
test_db_url = f"sqlite:///{test_analytics_db}"

class TestConfig(Config):
    TESTING = True
    DATABASE_URL = test_db_url

@pytest.fixture(scope="module")
def app():
    # Remove files if exist
    if os.path.exists(test_analytics_db):
        try:
            os.remove(test_analytics_db)
        except PermissionError:
            pass

    app = create_app(TestConfig)
    
    yield app

    # Teardown database
    db_session.remove()
    from backend.database.db import engine
    engine.dispose()
    
    if os.path.exists(test_analytics_db):
        try:
            os.remove(test_analytics_db)
        except PermissionError:
            pass

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    """Fixture to register a user and return authorization headers."""
    client.post('/signup', json={
        "email": "analytics_user@example.com",
        "password": "password123"
    })
    login_resp = client.post('/login', json={
        "email": "analytics_user@example.com",
        "password": "password123"
    })
    token = login_resp.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(autouse=True)
def clean_db(app):
    with app.app_context():
        db_session.query(QuizHistory).delete()
        db_session.query(LearningProgress).delete()
        db_session.query(Flashcard).delete()
        db_session.query(UploadedDocument).delete()
        db_session.query(Topic).delete()
        db_session.query(TokenBlocklist).delete()
        db_session.query(User).delete()
        db_session.commit()
    yield

def test_progress_and_analytics_endpoints(client, auth_headers):
    """Test progress listing and analytics dashboard calculations."""
    user = db_session.query(User).filter_by(email="analytics_user@example.com").first()
    user_id = user.id
    
    # 1. Seed Topics
    topic_a = Topic(name="Data Science", user_id=user_id)
    topic_b = Topic(name="Organic Chemistry", user_id=user_id)
    db_session.add_all([topic_a, topic_b])
    db_session.commit()
    
    topic_a_id = topic_a.id
    topic_b_id = topic_b.id

    # 2. Seed Uploaded Documents
    now = datetime.datetime.utcnow()
    doc1 = UploadedDocument(user_id=user_id, filename="data_notes.pdf", file_path="/mock/1.pdf", file_type="pdf", file_size=120, status="completed", created_at=now - datetime.timedelta(minutes=10))
    doc2 = UploadedDocument(user_id=user_id, filename="chemistry_elements.docx", file_path="/mock/2.docx", file_type="docx", file_size=240, status="completed", created_at=now)
    db_session.add_all([doc1, doc2])
    db_session.commit()

    # 3. Seed Flashcards
    for i in range(3):
        fc = Flashcard(user_id=user_id, topic_id=topic_a_id, question=f"DS Question {i}", answer=f"DS Answer {i}")
        db_session.add(fc)
    for i in range(2):
        fc = Flashcard(user_id=user_id, topic_id=topic_b_id, question=f"Chem Question {i}", answer=f"Chem Answer {i}")
        db_session.add(fc)
    db_session.commit()

    # 4. Seed Quiz History (Topic A average: 90%, Topic B average: 40%)
    qh1 = QuizHistory(user_id=user_id, topic_id=topic_a_id, total_questions=5, correct_answers=4, score=80.0, attempted_at=now - datetime.timedelta(minutes=5))
    qh2 = QuizHistory(user_id=user_id, topic_id=topic_a_id, total_questions=5, correct_answers=5, score=100.0, attempted_at=now - datetime.timedelta(minutes=3))
    qh3 = QuizHistory(user_id=user_id, topic_id=topic_b_id, total_questions=5, correct_answers=2, score=40.0, attempted_at=now)
    db_session.add_all([qh1, qh2, qh3])
    db_session.commit()

    # 5. Seed Learning Progress records
    lp1 = LearningProgress(user_id=user_id, topic_id=topic_a_id, flashcards_viewed=10, mastery_level=90.0)
    lp2 = LearningProgress(user_id=user_id, topic_id=topic_b_id, flashcards_viewed=5, mastery_level=40.0)
    db_session.add_all([lp1, lp2])
    db_session.commit()

    # 6. Test GET /progress endpoint
    progress_resp = client.get('/progress', headers=auth_headers)
    assert progress_resp.status_code == 200
    progress_data = progress_resp.get_json()
    assert len(progress_data) == 2
    
    # Verify records map correct stats
    progress_map = {p["topic_name"]: p for p in progress_data}
    assert progress_map["Data Science"]["mastery_level"] == 90.0
    assert progress_map["Data Science"]["flashcards_viewed"] == 10
    assert progress_map["Organic Chemistry"]["mastery_level"] == 40.0
    assert progress_map["Organic Chemistry"]["flashcards_viewed"] == 5

    # 7. Test GET /analytics endpoint
    analytics_resp = client.get('/analytics', headers=auth_headers)
    assert analytics_resp.status_code == 200
    analytics_data = analytics_resp.get_json()
    
    # Verify statistics
    stats = analytics_data["statistics"]
    assert stats["total_documents"] == 2
    assert stats["total_flashcards"] == 5
    assert stats["total_quizzes"] == 3
    # Average accuracy = (80 + 100 + 40) / 3 = 73.33%
    assert stats["average_accuracy"] == 73.33
    
    # Verify weak topics detection (Only Organic Chemistry should be returned since mastery < 60)
    weak_topics = analytics_data["weak_topics"]
    assert len(weak_topics) == 1
    assert weak_topics[0]["topic_name"] == "Organic Chemistry"
    assert weak_topics[0]["mastery_level"] == 40.0

    # Verify recent records (ordered desc)
    recent_uploads = analytics_data["recent_uploads"]
    assert len(recent_uploads) == 2
    assert recent_uploads[0]["filename"] == "chemistry_elements.docx" # Seeded second, so most recent
    
    recent_quizzes = analytics_data["recent_quizzes"]
    assert len(recent_quizzes) == 3
    assert recent_quizzes[0]["topic_name"] == "Organic Chemistry" # Seeded third, so most recent
