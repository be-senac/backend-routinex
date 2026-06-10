import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Float, Enum as SAEnum, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.task import Priority


class RecurrenceType(str, Enum):
    diaria = "diaria"
    semanal = "semanal"
    dias_uteis = "dias_uteis"


class Routine(Base):
    __tablename__ = "routines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(SAEnum(Priority), default=Priority.media)
    recurrence_type: Mapped[str] = mapped_column(SAEnum(RecurrenceType), default=RecurrenceType.diaria)
    recurrence_days: Mapped[list | None] = mapped_column(ARRAY(Integer), nullable=True)
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)
    estimated_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="routines")
    category: Mapped["Category | None"] = relationship()
