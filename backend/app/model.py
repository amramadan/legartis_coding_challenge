from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, UniqueConstraint, ForeignKey, Boolean, Index, DateTime, BigInteger, Text, func
from datetime import datetime


class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

class ClauseType(TimestampMixin, Base):
    __tablename__ = "clause_types"
    __table_args__ = (UniqueConstraint("name", name="uq_clause_types_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    patterns: Mapped[list["ClausePattern"]] = relationship(
        back_populates="clause_type",
        cascade="all, delete-orphan",
    )

class ClausePattern(TimestampMixin, Base):
    __tablename__ = "clause_patterns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clause_type_id: Mapped[int] = mapped_column(
        ForeignKey("clause_types.id", ondelete="CASCADE"),
        nullable=False,
    )

    pattern: Mapped[str] = mapped_column(String(500), nullable=False)
    is_regex: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    clause_type: Mapped["ClauseType"] = relationship(back_populates="patterns")


Index("ix_clause_patterns_clause_type_id", ClausePattern.clause_type_id)

class Contract(TimestampMixin, Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)

    storage_backend: Mapped[str] = mapped_column(String(50), nullable=False)  # "local"
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256_hex: Mapped[str] = mapped_column(String(64), nullable=False)

    processing_status: Mapped[str] = mapped_column(String(30), nullable=False, default="uploaded")
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


Index("ix_contracts_sha256_hex", Contract.sha256_hex)
