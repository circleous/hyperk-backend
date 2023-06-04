"""create instance table

Revision ID: 1631a60036d2
Revises: 2923986177bb
Create Date: 2023-03-19 17:27:37.650021

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1631a60036d2'
down_revision = '2923986177bb'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "instances",
        sa.Column("id", sa.String(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_instances")),
        sa.UniqueConstraint("id", name=op.f("uq_instances_id")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],
                                name=op.f("fk_instances_user_id_users")),
    )


def downgrade():
    op.drop_table("instances")
