from sqlalchemy import Column, ForeignKey, Integer, String
from app.database import Base


class Attachment(Base):
    __tablename__ = "attachments"
    id = Column(Integer, primary_key=True)
    olympiad_id = Column(Integer, ForeignKey("olympiads.id"), nullable=False)
    kind = Column(String(20), nullable=False)
    title = Column(String(150), nullable=False)
    original_name = Column(String(200), nullable=False)
    stored_name = Column(String(100), nullable=False)
