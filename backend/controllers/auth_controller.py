import re
from backend.database.db import db_session
from backend.models.user import User
from backend.models.token_blocklist import TokenBlocklist
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

def validate_signup_input(email, password):
    """Validate signup email and password."""
    if not email or not password:
        return "Email and password are required."
    
    if not re.match(EMAIL_REGEX, email):
        return "Invalid email address format."
        
    if len(password) < 6:
        return "Password must be at least 6 characters long."
        
    return None

def signup_user(email, password):
    """Register a new user in the database."""
    validation_error = validate_signup_input(email, password)
    if validation_error:
        return {"error": validation_error}, 400

    # Normalise email (lowercase)
    email = email.strip().lower()

    # Check if user already exists
    existing_user = db_session.query(User).filter_by(email=email).first()
    if existing_user:
        return {"error": "User with this email already exists."}, 409

    try:
        # Hash password and create user
        hashed_password = generate_password_hash(password).decode('utf-8')
        new_user = User(email=email, password_hash=hashed_password)
        db_session.add(new_user)
        db_session.commit()
        return {"message": "User registered successfully.", "user_id": new_user.id}, 201
    except Exception as e:
        db_session.rollback()
        return {"error": f"An error occurred during registration: {str(e)}"}, 500

def login_user(email, password):
    """Authenticate user and return access token."""
    if not email or not password:
        return {"error": "Email and password are required."}, 400

    email = email.strip().lower()
    user = db_session.query(User).filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return {"error": "Invalid email or password."}, 401

    try:
        # Create access token (JWT identity is the user's ID)
        access_token = create_access_token(identity=str(user.id))
        return {
            "message": "Login successful.",
            "access_token": access_token,
            "user": {
                "id": user.id,
                "email": user.email
            }
        }, 200
    except Exception as e:
        return {"error": f"An error occurred during login: {str(e)}"}, 500

def logout_user(jti):
    """Revoke active JWT token by adding it to the blocklist."""
    try:
        # Store JTI in blocklist
        revoked_token = TokenBlocklist(jti=jti)
        db_session.add(revoked_token)
        db_session.commit()
        return {"message": "Logged out successfully."}, 200
    except Exception as e:
        db_session.rollback()
        return {"error": f"An error occurred during logout: {str(e)}"}, 500
