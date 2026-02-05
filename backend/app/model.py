from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, UniqueConstraint, ForeignKey, Boolean, Index


class Base(DeclarativeBase):
    pass


class ClauseType(Base):
    __tablename__ = "clause_types"
    __table_args__ = (UniqueConstraint("name", name="uq_clause_types_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    patterns: Mapped[list["ClausePattern"]] = relationship(
        back_populates="clause_type",
        cascade="all, delete-orphan",
    )

class ClausePattern(Base):
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
