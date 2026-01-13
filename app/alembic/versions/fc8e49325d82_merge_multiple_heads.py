"""merge multiple heads

Revision ID: fc8e49325d82
Revises: 1744981f8aec, 65704911fc4c
Create Date: 2026-01-12 17:19:14.301560

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'fc8e49325d82'
down_revision = ('1744981f8aec', '65704911fc4c')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
