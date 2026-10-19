from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, Numeric, String, UniqueConstraint
from app.database import Base


class Participation(Base):
    __tablename__ = "participations"
    __table_args__ = (
        UniqueConstraint("olympiad_id", "student_id", name="unique_enrollment"),
        CheckConstraint("score >= 0", name="nonnegative_score"),
    )
    id = Column(Integer, primary_key=True)
    olympiad_id = Column(Integer, ForeignKey("olympiads.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Numeric(8, 2))
    result = Column(String(20))

