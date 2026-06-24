from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.controllers.analytics_controller import get_learning_progress, get_dashboard_analytics

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/progress', methods=['GET'])
@jwt_required()
def progress():
    """Retrieve learning progress metrics by topic."""
    user_id = int(get_jwt_identity())
    result, status_code = get_learning_progress(user_id)
    return jsonify(result), status_code

@analytics_bp.route('/analytics', methods=['GET'])
@jwt_required()
def analytics():
    """Retrieve consolidated analytics metrics for dashboard."""
    user_id = int(get_jwt_identity())
    result, status_code = get_dashboard_analytics(user_id)
    return jsonify(result), status_code
