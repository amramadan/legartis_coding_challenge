"""add timestamps to clause types and patterns

Revision ID: 622398860f71
Revises: 86d1dfd3d6d0
Create Date: 2026-02-05 19:55:21.803125

"""
from alembic import op
import sqlalchemy as sa

revision = '622398860f71'
down_revision = '86d1dfd3d6d0'
branch_labels = None
depends_on = None

def upgrade():
    # clause_patterns timestamps
    op.add_column(
        "clause_patterns",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column(
        "clause_patterns",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # clause_types timestamps
    op.add_column(
        "clause_types",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column(
        "clause_types",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # contracts: preserve uploaded_at by renaming it to created_at
    op.execute("ALTER TABLE contracts RENAME COLUMN uploaded_at TO created_at")
    # interpret old naive timestamps as UTC and convert to timestamptz
    op.execute("ALTER TABLE contracts ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE contracts ALTER COLUMN created_at SET DEFAULT now()")

    # add updated_at
    op.add_column(
        "contracts",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # processed_at -> timestamptz 
    op.execute("ALTER TABLE contracts ALTER COLUMN processed_at TYPE timestamptz USING processed_at AT TIME ZONE 'UTC'")

def downgrade():
    # contracts: processed_at back to timestamp
    op.execute("ALTER TABLE contracts ALTER COLUMN processed_at TYPE timestamp USING processed_at AT TIME ZONE 'UTC'")

    op.drop_column("contracts", "updated_at")

    # created_at back to timestamp naive UTC, then rename to uploaded_at
    op.execute("ALTER TABLE contracts ALTER COLUMN created_at TYPE timestamp USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE contracts RENAME COLUMN created_at TO uploaded_at")

    op.drop_column("clause_types", "updated_at")
    op.drop_column("clause_types", "created_at")
    op.drop_column("clause_patterns", "updated_at")
    op.drop_column("clause_patterns", "created_at")

