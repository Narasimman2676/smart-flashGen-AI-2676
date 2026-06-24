from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from backend.config.config import Config

# Dynamic engine parameters based on DB driver
engine_kwargs = {}
if Config.DATABASE_URL.startswith("sqlite:"):
    # Allow SQLite to be used across multiple threads in Flask context
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # MySQL specific connection settings for production reliability
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 3600

# Create DB engine
engine = create_engine(Config.DATABASE_URL, **engine_kwargs)

# Create a scoped session for thread-safety in Flask
db_session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
)

# Declarative Base for models
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    """Import all models and create database tables if they do not exist."""
    # Import all models here so that they are registered properly on Base.metadata
    from backend.models.user import User
    from backend.models.document import UploadedDocument
    from backend.models.keyword import Keyword
    from backend.models.topic import Topic
    from backend.models.flashcard import Flashcard
    from backend.models.quiz_history import QuizHistory
    from backend.models.learning_progress import LearningProgress
    
    Base.metadata.create_all(bind=engine)

def close_db_session(exception=None):
    """Close the active database session."""
    db_session.remove()
