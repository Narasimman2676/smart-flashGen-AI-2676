from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.controllers.quiz_controller import generate_quiz_questions, evaluate_quiz_submission

quiz_bp = Blueprint('quiz', __name__)

@quiz_bp.route('/quiz', methods=['POST'])
@jwt_required()
def start_quiz():
    """Endpoint to initiate a random MCQ quiz."""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    
    topic_id = data.get('topic_id')
    document_id = data.get('document_id')
    num_questions = data.get('num_questions', 10)
    
    result, status_code = generate_quiz_questions(user_id, topic_id, document_id, num_questions)
    return jsonify(result), status_code

@quiz_bp.route('/quiz/submit', methods=['POST'])
@jwt_required()
def submit_quiz():
    """Endpoint to grade a quiz submission and log progress/history metrics."""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    
    topic_id = data.get('topic_id')
    answers = data.get('answers')
    
    if not answers:
        return jsonify({"error": "Missing key 'answers' in request body."}), 400
        
    result, status_code = evaluate_quiz_submission(user_id, topic_id, answers)
    return jsonify(result), status_code
