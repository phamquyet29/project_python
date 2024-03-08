"""Add user_id column to Comment table

Revision ID: 63a9ab350794
Revises: 6f162827a36a
Create Date: 2024-03-08 17:12:32.949475

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '63a9ab350794'
down_revision = '6f162827a36a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('comment', sa.Column('user_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'comment', 'user', ['user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'comment', type_='foreignkey')
    op.drop_column('comment', 'user_id')
    # ### end Alembic commands ###
