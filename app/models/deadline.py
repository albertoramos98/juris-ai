from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean, DateTime
from app.core.database import Base


class Deadline(Base):
    __tablename__ = "deadlines"

    id = Column(Integer, primary_key=True, index=True)

    description = Column(String, nullable=False)
    due_date = Column(Date, nullable=False)

    responsible = Column(String, nullable=False)

    completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    completed_by = Column(Integer, nullable=True)

    is_critical = Column(Boolean, default=False, nullable=False)
    status = Column(String, default="pending", nullable=False)

    process_id = Column(Integer, ForeignKey("processes.id"), nullable=False)
    office_id = Column(Integer, ForeignKey("offices.id"), nullable=False)
