import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.rag.embeddings import EMBEDDING_DIM


class LogChunk(Base):
    """One embedded entry from app/rag/mock_logs.py — see ingest.py."""

    __tablename__ = "log_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    log_id: Mapped[str] = mapped_column(String(50), unique=True)  # e.g. "cw-002", matches mock_logs.py
    source: Mapped[str] = mapped_column(String(20))  # "cicd" | "cloudwatch"
    service: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
