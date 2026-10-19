from sqlalchemy import CheckConstraint, Column, Date, ForeignKey, Integer, String, Text
from app.database import Base


class Olympiad(Base):
    __tablename__ = "olympiads"
    __table_args__ = (CheckConstraint("end_date >= start_date", name="dates_order"),)
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False, default="")
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    protocol_status = Column(String(20), nullable=False, default="draft")

