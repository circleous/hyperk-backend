"""create user table

Revision ID: 2923986177bb
Revises: 087ed675fea3
Create Date: 2023-03-19 17:17:56.145783

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2923986177bb'
down_revision = '087ed675fea3'
branch_labels = None
depends_on = None


def upgrade():
    user_tbl = op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("realname", sa.String(length=64), nullable=True),
        sa.Column("is_admin", sa.Boolean(), default=False, nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("id", name=op.f("uq_users_id")),
        sa.UniqueConstraint("username", name=op.f("uq_users_username")),
    )

    op.bulk_insert(user_tbl, [{
        "id": 1,
        "username": "usman_ahalim",
        "realname": "Usman",
        "is_admin": True,
    }, {
        "id": 2,
        "username": "arya_pramuja",
        "realname": "Arya",
        "is_admin": False,
    }])


def downgrade():
    op.drop_table("users")
