import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.db import Base

class Keyword(Base):
    __tablename__ = 'keywords'

    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String(100), nullable=False, index=True)
    importance_score = Column(Float, nullable=False, default=0.0)
    document_id = Column(Integer, ForeignKey('uploaded_documents.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("UploadedDocument", back_populates="keywords")

    def __repr__(self):
        return f"<Keyword id={self.id} word='{self.word}' score={self.importance_score}>"
