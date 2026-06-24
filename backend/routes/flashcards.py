from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.controllers.flashcard_controller import (
    get_all_flashcards,
    get_flashcard_by_id,
    create_manual_flashcard,
    update_flashcard,
    delete_flashcard,
    toggle_favorite
)

flashcards_bp = Blueprint('flashcards', __name__)

@flashcards_bp.route('/flashcards', methods=['GET'])
@jwt_required()
def list_flashcards():
    """List all flashcards with optional filters (document_id, topic_id, search, favorite)."""
    user_id = int(get_jwt_identity())
    
    document_id = request.args.get('document_id', type=int)
    topic_id = request.args.get('topic_id', type=int)
    search_query = request.args.get('search', type=str)
    favorite_only = request.args.get('favorite', type=str) == 'true'
    
    result, status_code = get_all_flashcards(user_id, document_id, topic_id, search_query, favorite_only)
    return jsonify(result), status_code

@flashcards_bp.route('/flashcards', methods=['POST'])
@jwt_required()
def create_flashcard():
    """Create a new manual flashcard."""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    
    result, status_code = create_manual_flashcard(user_id, data)
    return jsonify(result), status_code

@flashcards_bp.route('/flashcards/<int:flashcard_id>', methods=['GET'])
@jwt_required()
def get_flashcard(flashcard_id):
    """Retrieve details of a specific flashcard."""
    user_id = int(get_jwt_identity())
    
    result, status_code = get_flashcard_by_id(user_id, flashcard_id)
    return jsonify(result), status_code

@flashcards_bp.route('/flashcards/<int:flashcard_id>', methods=['PUT'])
@jwt_required()
def update_flashcard_details(flashcard_id):
    """Update details of a specific flashcard."""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    
    result, status_code = update_flashcard(user_id, flashcard_id, data)
    return jsonify(result), status_code

@flashcards_bp.route('/flashcards/<int:flashcard_id>', methods=['DELETE'])
@jwt_required()
def delete_flashcard_item(flashcard_id):
    """Delete a specific flashcard."""
    user_id = int(get_jwt_identity())
    
    result, status_code = delete_flashcard(user_id, flashcard_id)
    return jsonify(result), status_code

@flashcards_bp.route('/flashcards/<int:flashcard_id>/favorite', methods=['POST'])
@jwt_required()
def toggle_flashcard_favorite(flashcard_id):
    """Toggle the favorite status of a specific flashcard."""
    user_id = int(get_jwt_identity())
    
    result, status_code = toggle_favorite(user_id, flashcard_id)
    return jsonify(result), status_code
