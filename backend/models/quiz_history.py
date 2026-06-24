import datetime
from sqlalchemy import Column, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.db import Base

class QuizHistory(Base):
    __tablename__ = 'quiz_histories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    topic_id = Column(Integer, ForeignKey('topics.id', ondelete='SET NULL'), nullable=True)
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)  # Percentage score e.g., 85.5
    attempted_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    incorrect_questions_json = Column(Text, nullable=True)  # Stores questions user got wrong

    # Relationships
    user = relationship("User", back_populates="quiz_histories")
    topic = relationship("Topic", back_populates="quiz_histories")

    def __repr__(self):
        return f"<QuizHistory id={self.id} user_id={self.user_id} score={self.score}%>"
