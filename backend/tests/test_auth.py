import os
import pytest
from backend.app import create_app
from backend.config.config import Config
from backend.database.db import Base, db_session
from backend.models import User, TokenBlocklist

# Use a test database for auth test isolation
test_auth_db = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_auth.db"))
test_db_url = f"sqlite:///{test_auth_db}"

class TestConfig(Config):
    TESTING = True
    DATABASE_URL = test_db_url
    JWT_SECRET_KEY = "test_jwt_secret_must_be_over_32_characters_long_for_security"
    SECRET_KEY = "test_secret_must_be_over_32_characters_long_for_security"
    # Ensure SQLite uses absolute path and is single threaded friendly
    if DATABASE_URL.startswith("sqlite:///"):
        db_file = DATABASE_URL.replace("sqlite:///", "")
        if not os.path.isabs(db_file):
            DATABASE_URL = f"sqlite:///{test_auth_db}"

@pytest.fixture(scope="module")
def app():
    # Remove database if exists
    if os.path.exists(test_auth_db):
        try:
            os.remove(test_auth_db)
        except PermissionError:
            pass

    app = create_app(TestConfig)
    
    yield app

    # Teardown database file
    db_session.remove()
    # Close connections so we can remove
    from backend.database.db import engine
    engine.dispose()
    if os.path.exists(test_auth_db):
        try:
            os.remove(test_auth_db)
        except PermissionError:
            pass

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def clean_db(app):
    # Clear tables before each test
    with app.app_context():
        db_session.query(TokenBlocklist).delete()
        db_session.query(User).delete()
        db_session.commit()
    yield

def test_signup_success(client):
    """Test successful user registration."""
    response = client.post('/signup', json={
        "email": "user@example.com",
        "password": "securepassword123"
    })
    assert response.status_code == 201
    data = response.get_json()
    assert "user_id" in data
    assert data["message"] == "User registered successfully."
    
    # Verify user is in database
    user = db_session.query(User).filter_by(email="user@example.com").first()
    assert user is not None

def test_signup_invalid_email(client):
    """Test registration with invalid email format."""
    response = client.post('/signup', json={
        "email": "bademailformat.com",
        "password": "password"
    })
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "Invalid email address format" in data["error"]

def test_signup_short_password(client):
    """Test registration with password under 6 characters."""
    response = client.post('/signup', json={
        "email": "user@example.com",
        "password": "123"
    })
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "Password must be at least 6 characters" in data["error"]

def test_signup_duplicate_email(client):
    """Test registering the same email twice."""
    # First signup
    client.post('/signup', json={
        "email": "duplicate@example.com",
        "password": "password123"
    })
    
    # Duplicate signup
    response = client.post('/signup', json={
        "email": "duplicate@example.com",
        "password": "differentpass"
    })
    assert response.status_code == 409
    data = response.get_json()
    assert "error" in data
    assert "already exists" in data["error"]

def test_login_success(client):
    """Test successful login and receipt of JWT."""
    # Register first
    client.post('/signup', json={
        "email": "login@example.com",
        "password": "correctpassword"
    })
    
    # Perform login
    response = client.post('/login', json={
        "email": "login@example.com",
        "password": "correctpassword"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["email"] == "login@example.com"

def test_login_invalid_credentials(client):
    """Test login failure with incorrect credentials."""
    # Register first
    client.post('/signup', json={
        "email": "login@example.com",
        "password": "correctpassword"
    })
    
    # Try logging in with incorrect password
    response = client.post('/login', json={
        "email": "login@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    data = response.get_json()
    assert "error" in data
    assert "Invalid email or password" in data["error"]

def test_logout_success(client):
    """Test logout invalidates the JWT."""
    # Register and Login to get token
    client.post('/signup', json={
        "email": "logout@example.com",
        "password": "password123"
    })
    login_resp = client.post('/login', json={
        "email": "logout@example.com",
        "password": "password123"
    })
    token = login_resp.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Perform logout (protected endpoint)
    logout_resp = client.post('/logout', headers=headers)
    assert logout_resp.status_code == 200
    assert logout_resp.get_json()["message"] == "Logged out successfully."
    
    # Attempting logout again with the same token should fail (token is revoked)
    second_logout = client.post('/logout', headers=headers)
    # Flask-JWT-Extended triggers a 401 / Revoked Token response automatically
    assert second_logout.status_code == 401
