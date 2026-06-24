from backend.database.db import db_session
from backend.models.flashcard import Flashcard

def get_all_flashcards(user_id, document_id=None, topic_id=None, search_query=None, favorite_only=False):
    """Retrieve flashcards belonging to the user with search and key filters."""
    query = db_session.query(Flashcard).filter(Flashcard.user_id == user_id)
    
    if document_id:
        query = query.filter(Flashcard.document_id == document_id)
        
    if topic_id:
        query = query.filter(Flashcard.topic_id == topic_id)
        
    if favorite_only:
        query = query.filter(Flashcard.is_favorite == True)
        
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            (Flashcard.question.like(search_pattern)) | 
            (Flashcard.answer.like(search_pattern))
        )
        
    # Return sorted by created_at descending
    flashcards = query.order_by(Flashcard.created_at.desc()).all()
    
    return [
        {
            "id": c.id,
            "document_id": c.document_id,
            "topic_id": c.topic_id,
            "question": c.question,
            "answer": c.answer,
            "difficulty": c.difficulty,
            "is_favorite": c.is_favorite,
            "created_at": c.created_at.isoformat()
        } for c in flashcards
    ], 200

def get_flashcard_by_id(user_id, flashcard_id):
    """Retrieve a single flashcard, checking user ownership."""
    card = db_session.get(Flashcard, flashcard_id)
    if not card or card.user_id != user_id:
        return {"error": "Flashcard not found or unauthorized."}, 404
        
    return {
        "id": card.id,
        "document_id": card.document_id,
        "topic_id": card.topic_id,
        "question": card.question,
        "answer": card.answer,
        "difficulty": card.difficulty,
        "is_favorite": card.is_favorite,
        "created_at": card.created_at.isoformat()
    }, 200

def create_manual_flashcard(user_id, data):
    """Create a manual flashcard."""
    question = data.get("question", "").strip()
    answer = data.get("answer", "").strip()
    
    if not question or not answer:
        return {"error": "Question and answer are required fields."}, 400
        
    topic_id = data.get("topic_id")
    document_id = data.get("document_id")
    difficulty = data.get("difficulty", "medium")
    
    if difficulty not in ["easy", "medium", "hard"]:
        difficulty = "medium"

    try:
        new_card = Flashcard(
            user_id=user_id,
            document_id=document_id,
            topic_id=topic_id,
            question=question,
            answer=answer,
            difficulty=difficulty,
            is_favorite=False
        )
        db_session.add(new_card)
        db_session.commit()
        
        return {
            "message": "Flashcard created successfully.",
            "flashcard": {
                "id": new_card.id,
                "question": new_card.question,
                "answer": new_card.answer,
                "difficulty": new_card.difficulty,
                "is_favorite": new_card.is_favorite
            }
        }, 201
    except Exception as e:
        db_session.rollback()
        return {"error": f"Failed to create flashcard: {str(e)}"}, 500

def update_flashcard(user_id, flashcard_id, data):
    """Update details of a flashcard."""
    card = db_session.get(Flashcard, flashcard_id)
    if not card or card.user_id != user_id:
        return {"error": "Flashcard not found or unauthorized."}, 404
        
    # Check fields
    if "question" in data:
        q = data["question"].strip()
        if q:
            card.question = q
            
    if "answer" in data:
        a = data["answer"].strip()
        if a:
            card.answer = a
            
    if "difficulty" in data:
        diff = data["difficulty"]
        if diff in ["easy", "medium", "hard"]:
            card.difficulty = diff
            
    if "is_favorite" in data:
        card.is_favorite = bool(data["is_favorite"])
        
    try:
        db_session.commit()
        return {
            "message": "Flashcard updated successfully.",
            "flashcard": {
                "id": card.id,
                "question": card.question,
                "answer": card.answer,
                "difficulty": card.difficulty,
                "is_favorite": card.is_favorite
            }
        }, 200
    except Exception as e:
        db_session.rollback()
        return {"error": f"Failed to update flashcard: {str(e)}"}, 500

def delete_flashcard(user_id, flashcard_id):
    """Delete a flashcard."""
    card = db_session.get(Flashcard, flashcard_id)
    if not card or card.user_id != user_id:
        return {"error": "Flashcard not found or unauthorized."}, 404
        
    try:
        db_session.delete(card)
        db_session.commit()
        return {"message": "Flashcard deleted successfully."}, 200
    except Exception as e:
        db_session.rollback()
        return {"error": f"Failed to delete flashcard: {str(e)}"}, 500

def toggle_favorite(user_id, flashcard_id):
    """Toggle a flashcard's favorite status."""
    card = db_session.get(Flashcard, flashcard_id)
    if not card or card.user_id != user_id:
        return {"error": "Flashcard not found or unauthorized."}, 404
        
    card.is_favorite = not card.is_favorite
    try:
        db_session.commit()
        return {
            "message": f"Flashcard {'marked as favorite' if card.is_favorite else 'removed from favorites'}.",
            "is_favorite": card.is_favorite
        }, 200
    except Exception as e:
        db_session.rollback()
        return {"error": f"Failed to toggle favorite: {str(e)}"}, 500
