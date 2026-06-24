import datetime
from sqlalchemy import Column, Integer, Text, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.db import Base

class Flashcard(Base):
    __tablename__ = 'flashcards'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    document_id = Column(Integer, ForeignKey('uploaded_documents.id', ondelete='SET NULL'), nullable=True)
    topic_id = Column(Integer, ForeignKey('topics.id', ondelete='SET NULL'), nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    difficulty = Column(String(20), default='medium', nullable=False)  # 'easy', 'medium', 'hard'
    is_favorite = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, 
        default=datetime.datetime.utcnow, 
        onupdate=datetime.datetime.utcnow, 
        nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="flashcards")
    document = relationship("UploadedDocument", back_populates="flashcards")
    topic = relationship("Topic", back_populates="flashcards")

    def __repr__(self):
        return f"<Flashcard id={self.id} user_id={self.user_id} question='{self.question[:30]}...'>"
