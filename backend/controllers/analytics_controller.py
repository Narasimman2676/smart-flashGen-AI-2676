from sqlalchemy import func
from backend.database.db import db_session
from backend.models.document import UploadedDocument
from backend.models.flashcard import Flashcard
from backend.models.quiz_history import QuizHistory
from backend.models.learning_progress import LearningProgress
from backend.models.topic import Topic

def get_learning_progress(user_id):
    """Retrieve user progress statistics across all attempted study topics."""
    progress_records = db_session.query(LearningProgress).filter_by(user_id=user_id).all()
    
    progress_list = []
    for p in progress_records:
        progress_list.append({
            "id": p.id,
            "topic_id": p.topic_id,
            "topic_name": p.topic.name if p.topic else "Unknown Topic",
            "flashcards_viewed": p.flashcards_viewed,
            "mastery_level": p.mastery_level,
            "last_studied_at": p.last_studied_at.isoformat()
        })
        
    return progress_list, 200

def get_dashboard_analytics(user_id):
    """Compile aggregated statistics, weak topics, and recent activities for the dashboard."""
    # 1. Basic Counts
    total_docs = db_session.query(UploadedDocument).filter_by(user_id=user_id).count()
    total_cards = db_session.query(Flashcard).filter_by(user_id=user_id).count()
    total_quizzes = db_session.query(QuizHistory).filter_by(user_id=user_id).count()
    
    # 2. Cumulative Accuracy
    avg_score = db_session.query(func.avg(QuizHistory.score)).filter_by(user_id=user_id).scalar()
    average_accuracy = round(float(avg_score), 2) if avg_score is not None else 0.0

    # 3. Detect Weak Topics (Mastery below 60%)
    weak_records = db_session.query(LearningProgress).filter(
        LearningProgress.user_id == user_id,
        LearningProgress.mastery_level < 60.0
    ).order_by(LearningProgress.mastery_level.asc()).all()
    
    weak_topics = []
    for w in weak_records:
        weak_topics.append({
            "topic_id": w.topic_id,
            "topic_name": w.topic.name if w.topic else "Unknown Topic",
            "mastery_level": w.mastery_level,
            "flashcards_viewed": w.flashcards_viewed
        })

    # 4. Recent uploads (Last 5)
    recent_uploads_records = db_session.query(UploadedDocument).filter_by(user_id=user_id).order_by(
        UploadedDocument.created_at.desc()
    ).limit(5).all()
    
    recent_uploads = []
    for doc in recent_uploads_records:
        recent_uploads.append({
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "status": doc.status,
            "created_at": doc.created_at.isoformat()
        })

    # 5. Recent quizzes (Last 5)
    recent_quizzes_records = db_session.query(QuizHistory).filter_by(user_id=user_id).order_by(
        QuizHistory.attempted_at.desc()
    ).limit(5).all()
    
    recent_quizzes = []
    for quiz in recent_quizzes_records:
        recent_quizzes.append({
            "id": quiz.id,
            "topic_id": quiz.topic_id,
            "topic_name": quiz.topic.name if quiz.topic else "General Study",
            "total_questions": quiz.total_questions,
            "correct_answers": quiz.correct_answers,
            "score": quiz.score,
            "attempted_at": quiz.attempted_at.isoformat()
        })

    return {
        "statistics": {
            "total_documents": total_docs,
            "total_flashcards": total_cards,
            "total_quizzes": total_quizzes,
            "average_accuracy": average_accuracy
        },
        "weak_topics": weak_topics,
        "recent_uploads": recent_uploads,
        "recent_quizzes": recent_quizzes
    }, 200
