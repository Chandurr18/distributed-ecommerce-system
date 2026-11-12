
"""add user scope to idempotency records

Revision ID: eb10ffd67b97
Revises: f97091a43186
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "eb10ffd67b97"
down_revision: Union[str, Sequence[str], None] = "f97091a43186"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "idempotency_records",
        sa.Column("user_id", sa.UUID(), nullable=False),
    )

    op.drop_constraint(
        "idempotency_records_idempotency_key_key",
        "idempotency_records",
        type_="unique",
    )

    op.create_unique_constraint(
        "uq_user_idempotency_key",
        "idempotency_records",
        ["user_id", "idempotency_key"],
    )

    op.create_foreign_key(
        "fk_idempotency_records_user_id_users",
        "idempotency_records",
        "users",
        ["user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_idempotency_records_user_id_users",
        "idempotency_records",
        type_="foreignkey",
    )

    op.drop_constraint(
        "uq_user_idempotency_key",
        "idempotency_records",
        type_="unique",
    )

    op.create_unique_constraint(
        "idempotency_records_idempotency_key_key",
        "idempotency_records",
        ["idempotency_key"],
    )

    op.drop_column("idempotency_records", "user_id")
