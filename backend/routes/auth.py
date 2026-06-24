from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from backend.controllers.auth_controller import signup_user, login_user, logout_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """Endpoint for user registration."""
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    
    result, status_code = signup_user(email, password)
    return jsonify(result), status_code

@auth_bp.route('/login', methods=['POST'])
def login():
    """Endpoint for user authentication."""
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    
    result, status_code = login_user(email, password)
    return jsonify(result), status_code

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Endpoint for logging out and revoking token."""
    # Retrieve unique JWT identifier (jti)
    jti = get_jwt()["jti"]
    result, status_code = logout_user(jti)
    return jsonify(result), status_code
