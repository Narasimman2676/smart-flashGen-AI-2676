import os
import pytest
import json
from backend.app import create_app
from backend.config.config import Config
from backend.database.db import db_session
from backend.models import User, Topic, Flashcard, QuizHistory, LearningProgress, TokenBlocklist

# Test database and directory specs
test_quiz_db = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_quiz.db"))
test_db_url = f"sqlite:///{test_quiz_db}"

class TestConfig(Config):
    TESTING = True
    DATABASE_URL = test_db_url

@pytest.fixture(scope="module")
def app():
    # Remove files if exist
    if os.path.exists(test_quiz_db):
        try:
            os.remove(test_quiz_db)
        except PermissionError:
            pass

    app = create_app(TestConfig)
    
    yield app

    # Teardown database
    db_session.remove()
    from backend.database.db import engine
    engine.dispose()
    
    if os.path.exists(test_quiz_db):
        try:
            os.remove(test_quiz_db)
        except PermissionError:
            pass

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    """Fixture to register a user and return authorization headers."""
    client.post('/signup', json={
        "email": "study_user@example.com",
        "password": "password123"
    })
    login_resp = client.post('/login', json={
        "email": "study_user@example.com",
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
        db_session.query(Topic).delete()
        db_session.query(TokenBlocklist).delete()
        db_session.query(User).delete()
        db_session.commit()
    yield

def test_flashcard_crud(client, auth_headers):
    """Test full CRUD operations on the Flashcards endpoints."""
    # 1. Create a Topic
    # We will seed it directly in the DB to test flashcard association
    user = db_session.query(User).filter_by(email="study_user@example.com").first()
    topic = Topic(name="Database Systems", user_id=user.id)
    db_session.add(topic)
    db_session.commit()
    
    # 2. Test Create Flashcard (POST /flashcards)
    response = client.post('/flashcards', headers=auth_headers, json={
        "question": "What is normalization?",
        "answer": "A process of organizing data in a database.",
        "topic_id": topic.id,
        "difficulty": "medium"
    })
    assert response.status_code == 201
    res_data = response.get_json()
    assert "flashcard" in res_data
    card_id = res_data["flashcard"]["id"]
    assert res_data["flashcard"]["question"] == "What is normalization?"
    
    # 3. Test List Flashcards (GET /flashcards)
    list_resp = client.get('/flashcards', headers=auth_headers)
    assert list_resp.status_code == 200
    cards_list = list_resp.get_json()
    assert len(cards_list) == 1
    assert cards_list[0]["id"] == card_id
    
    # 4. Test List Flashcards with search filters
    search_resp = client.get('/flashcards?search=normalization', headers=auth_headers)
    assert len(search_resp.get_json()) == 1
    
    search_resp_empty = client.get('/flashcards?search=notpresent', headers=auth_headers)
    assert len(search_resp_empty.get_json()) == 0

    # 5. Test Get Flashcard by ID (GET /flashcards/<id>)
    get_resp = client.get(f'/flashcards/{card_id}', headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.get_json()["question"] == "What is normalization?"

    # 6. Test Update Flashcard (PUT /flashcards/<id>)
    update_resp = client.put(f'/flashcards/{card_id}', headers=auth_headers, json={
        "question": "What is DB normalization?",
        "difficulty": "hard"
    })
    assert update_resp.status_code == 200
    assert update_resp.get_json()["flashcard"]["question"] == "What is DB normalization?"
    assert update_resp.get_json()["flashcard"]["difficulty"] == "hard"

    # 7. Test Toggle Favorite (POST /flashcards/<id>/favorite)
    fav_resp = client.post(f'/flashcards/{card_id}/favorite', headers=auth_headers)
    assert fav_resp.status_code == 200
    assert fav_resp.get_json()["is_favorite"] is True
    
    # Verify filter favorite works
    fav_filter_resp = client.get('/flashcards?favorite=true', headers=auth_headers)
    assert len(fav_filter_resp.get_json()) == 1

    # 8. Test Delete Flashcard (DELETE /flashcards/<id>)
    del_resp = client.delete(f'/flashcards/{card_id}', headers=auth_headers)
    assert del_resp.status_code == 200
    
    # Verify no cards exist
    final_list = client.get('/flashcards', headers=auth_headers).get_json()
    assert len(final_list) == 0

def test_quiz_generation_and_evaluation(client, auth_headers):
    """Test generating a quiz and evaluating its results."""
    user = db_session.query(User).filter_by(email="study_user@example.com").first()
    topic = Topic(name="Web Protocols", user_id=user.id)
    db_session.add(topic)
    db_session.commit()
    
    user_id = user.id
    topic_id = topic.id
    
    # Seed 5 flashcards to create options
    card_data = [
        ("What does HTTP stand for?", "Hypertext Transfer Protocol"),
        ("What does URL stand for?", "Uniform Resource Locator"),
        ("What does IP stand for?", "Internet Protocol"),
        ("What does DNS stand for?", "Domain Name System"),
        ("What does SSL stand for?", "Secure Sockets Layer")
    ]
    
    cards = []
    for q, a in card_data:
        c = Flashcard(user_id=user_id, topic_id=topic_id, question=q, answer=a)
        db_session.add(c)
        cards.append(c)
    db_session.commit()
    
    # 1. Test quiz generation (POST /quiz)
    quiz_resp = client.post('/quiz', headers=auth_headers, json={
        "topic_id": topic_id,
        "num_questions": 3
    })
    assert quiz_resp.status_code == 200
    quiz_data = quiz_resp.get_json()
    assert "questions" in quiz_data
    questions = quiz_data["questions"]
    assert len(questions) == 3
    
    for q in questions:
        assert "flashcard_id" in q
        assert "question" in q
        assert "options" in q
        assert len(q["options"]) == 4  # Should generate exactly 4 multiple choice options
        
    # 2. Test quiz evaluation (POST /quiz/submit)
    # We will submit 2 correct answers and 1 incorrect answer
    # Fetch original answers for matching
    card_map = {c.id: c.answer for c in cards}
    
    ans_submissions = [
        {"flashcard_id": questions[0]["flashcard_id"], "selected_option": card_map[questions[0]["flashcard_id"]]}, # Correct
        {"flashcard_id": questions[1]["flashcard_id"], "selected_option": card_map[questions[1]["flashcard_id"]]}, # Correct
        {"flashcard_id": questions[2]["flashcard_id"], "selected_option": "Wrong Answer Choice"} # Incorrect
    ]
    
    submit_resp = client.post('/quiz/submit', headers=auth_headers, json={
        "topic_id": topic_id,
        "answers": ans_submissions
    })
    assert submit_resp.status_code == 200
    res = submit_resp.get_json()
    
    assert res["total_questions"] == 3
    assert res["correct_answers"] == 2
    # Score should be (2/3) * 100 = 66.67
    assert res["score"] == 66.67
    assert "quiz_history_id" in res
    assert "progress" in res
    assert res["progress"]["flashcards_viewed"] == 3
    assert res["progress"]["mastery_level"] == 66.67
    
    # Verify QuizHistory record
    history_id = res["quiz_history_id"]
    db_history = db_session.get(QuizHistory, history_id)
    assert db_history is not None
    assert db_history.score == 66.67
    assert "Wrong Answer Choice" in db_history.incorrect_questions_json

    # Verify LearningProgress record
    db_progress = db_session.query(LearningProgress).filter_by(user_id=user_id, topic_id=topic_id).first()
    assert db_progress is not None
    assert db_progress.flashcards_viewed == 3
    assert db_progress.mastery_level == 66.67

    # 3. Test subsequent quiz submission updates the average mastery level
    # Submit another quiz with 100% (3/3)
    next_submissions = [
        {"flashcard_id": questions[0]["flashcard_id"], "selected_option": card_map[questions[0]["flashcard_id"]]},
        {"flashcard_id": questions[1]["flashcard_id"], "selected_option": card_map[questions[1]["flashcard_id"]]},
        {"flashcard_id": questions[2]["flashcard_id"], "selected_option": card_map[questions[2]["flashcard_id"]]}
    ]
    
    second_submit = client.post('/quiz/submit', headers=auth_headers, json={
        "topic_id": topic_id,
        "answers": next_submissions
    })
    assert second_submit.status_code == 200
    res_second = second_submit.get_json()
    assert res_second["score"] == 100.0
    # Mastery level should update to average of [66.67, 100.0] = 83.335 -> 83.34
    assert res_second["progress"]["mastery_level"] == 83.34
    assert res_second["progress"]["flashcards_viewed"] == 6
