from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
import uuid
from .database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True)
    original_filename = Column(String)
    local_path = Column(String)
    status = Column(String, default="pending")  # pending, processed, error
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)