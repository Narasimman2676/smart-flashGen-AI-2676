import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.db import Base

class Topic(Base):
    __tablename__ = 'topics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="topics")
    flashcards = relationship("Flashcard", back_populates="topic", cascade="all, delete-orphan")
    learning_progresses = relationship("LearningProgress", back_populates="topic", cascade="all, delete-orphan")
    quiz_histories = relationship("QuizHistory", back_populates="topic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Topic id={self.id} name='{self.name}' user_id={self.user_id}>"
