"""Add role column to user model

Revision ID: 3eca84dce27f
Revises: fefc4237c189
Create Date: 2024-02-25 18:43:37.187385

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3eca84dce27f'
down_revision = 'fefc4237c189'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('role', sa.Integer(), nullable=True))
    op.drop_column('user', 'is_admin')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('is_admin', sa.BOOLEAN(), nullable=True))
    op.drop_column('user', 'role')
    # ### end Alembic commands ###
