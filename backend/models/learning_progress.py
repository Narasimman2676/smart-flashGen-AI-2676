import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.database.db import Base

class LearningProgress(Base):
    __tablename__ = 'learning_progresses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    topic_id = Column(Integer, ForeignKey('topics.id', ondelete='CASCADE'), nullable=False)
    flashcards_viewed = Column(Integer, default=0, nullable=False)
    mastery_level = Column(Float, default=0.0, nullable=False)  # Mastery rate from 0.0 to 100.0
    last_studied_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Make user_id and topic_id unique together
    __table_args__ = (
        UniqueConstraint('user_id', 'topic_id', name='_user_topic_uc'),
    )

    # Relationships
    user = relationship("User", back_populates="learning_progresses")
    topic = relationship("Topic", back_populates="learning_progresses")

    def __repr__(self):
        return f"<LearningProgress id={self.id} user_id={self.user_id} topic_id={self.topic_id} mastery={self.mastery_level}%>"
