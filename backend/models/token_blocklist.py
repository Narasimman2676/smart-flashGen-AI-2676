import datetime
from sqlalchemy import Column, Integer, String, DateTime
from backend.database.db import Base

class TokenBlocklist(Base):
    __tablename__ = 'token_blocklist'

    id = Column(Integer, primary_key=True, autoincrement=True)
    jti = Column(String(36), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<TokenBlocklist id={self.id} jti='{self.jti}'>"
