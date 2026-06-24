import os
from dotenv import load_dotenv

# Determine the directory of this file and load .env from the backend root directory
config_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.dirname(config_dir)
env_path = os.path.join(backend_root, '.env')

if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

class Config:
    """Base configuration class."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_change_me_in_production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt_secret_key_change_me_in_production")
    
    # Defaults to a local SQLite database in the backend folder if DATABASE_URL is not set
    default_db_path = os.path.join(backend_root, "flashcards.db")
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{default_db_path}")
    
    # Ensure SQLite paths are correctly formed for absolute paths
    if DATABASE_URL.startswith("sqlite:///"):
        # If it's a relative path in sqlite, make it absolute relative to backend root
        db_file = DATABASE_URL.replace("sqlite:///", "")
        if not os.path.isabs(db_file) and not db_file.startswith(":memory:"):
            DATABASE_URL = f"sqlite:///{os.path.join(backend_root, db_file)}"

    # Uploads folder settings
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(backend_root, "uploads"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # 16 MB limit
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
