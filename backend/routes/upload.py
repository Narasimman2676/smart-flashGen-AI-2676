from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.controllers.upload_controller import handle_upload
from backend.nlp.generator import generate_flashcards_from_doc

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload():
    """Protected endpoint for document uploads."""
    user_id = int(get_jwt_identity())
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request. Upload file with key 'file'."}), 400
        
    file = request.files['file']
    result, status_code = handle_upload(user_id, file)
    return jsonify(result), status_code

@upload_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate():
    """Protected endpoint to trigger NLP question generation on a completed document."""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    
    document_id = data.get('document_id')
    topic_id = data.get('topic_id')
    topic_name = data.get('topic_name')
    num_cards = data.get('num_cards', 10)
    
    if not document_id:
        return jsonify({"error": "Missing required field 'document_id'."}), 400

    from backend.models.topic import Topic
    from backend.database.db import db_session

    # If topic_name is provided, find or create the Topic record
    if topic_name and not topic_id:
        topic_name_clean = topic_name.strip()
        if topic_name_clean:
            try:
                topic = db_session.query(Topic).filter_by(user_id=user_id, name=topic_name_clean).first()
                if not topic:
                    topic = Topic(name=topic_name_clean, user_id=user_id)
                    db_session.add(topic)
                    db_session.commit()
                topic_id = topic.id
            except Exception as e:
                db_session.rollback()
                return jsonify({"error": f"Failed to handle topic creation: {str(e)}"}), 500

    try:
        cards = generate_flashcards_from_doc(document_id, topic_id, num_cards)
        if not cards:
            return jsonify({
                "message": "Flashcards generation completed with no cards.",
                "flashcards_count": 0,
                "flashcards": []
            }), 200
        return jsonify({
            "message": "Flashcards generated successfully.",
            "flashcards_count": len(cards),
            "flashcards": cards
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to generate flashcards: {str(e)}"}), 500
