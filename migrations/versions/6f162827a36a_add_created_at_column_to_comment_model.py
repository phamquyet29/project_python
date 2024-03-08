"""Add created_at column to Comment model

Revision ID: 6f162827a36a
Revises: 435ec8da5512
Create Date: 2024-03-08 15:25:49.397374

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6f162827a36a'
down_revision = '435ec8da5512'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('comment', sa.Column('created_at', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('comment', 'created_at')
    # ### end Alembic commands ###
