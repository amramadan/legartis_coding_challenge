from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, UniqueConstraint


class Base(DeclarativeBase):
    pass


class ClauseType(Base):
    __tablename__ = "clause_types"
    __table_args__ = (UniqueConstraint("name", name="uq_clause_types_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)