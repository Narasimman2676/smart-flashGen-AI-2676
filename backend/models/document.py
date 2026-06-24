import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.db import Base

class UploadedDocument(Base):
    __tablename__ = 'uploaded_documents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(10), nullable=False)  # 'pdf', 'docx', 'txt'
    file_size = Column(Integer, nullable=False)  # in bytes
    status = Column(String(50), default='uploaded', nullable=False)  # 'uploaded', 'processing', 'completed', 'failed'
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="documents")
    keywords = relationship("Keyword", back_populates="document", cascade="all, delete-orphan")
    flashcards = relationship("Flashcard", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<UploadedDocument id={self.id} filename='{self.filename}' user_id={self.user_id}>"
