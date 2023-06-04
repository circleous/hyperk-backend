"""init_empty

Revision ID: 087ed675fea3
Revises: 
Create Date: 2023-03-19 17:17:50.562051

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '087ed675fea3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    pre_upgrade()

    pass

    post_upgrade()


def downgrade():
    pre_downgrade()

    pass

    post_downgrade()


def pre_upgrade():
    pass


def post_upgrade():
    pass


def pre_downgrade():
    pass


def post_downgrade():
    pass
