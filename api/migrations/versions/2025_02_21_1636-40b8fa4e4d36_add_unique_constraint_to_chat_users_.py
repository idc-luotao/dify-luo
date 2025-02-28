"""add unique constraint to chat_users email

Revision ID: 40b8fa4e4d36
Revises: 4096602f36d6
Create Date: 2025-02-21 16:36:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '40b8fa4e4d36'
down_revision = '4096602f36d6'
branch_labels = None
depends_on = None

def upgrade():
    # 添加唯一约束
    op.create_unique_constraint('uq_chat_users_email', 'chat_users', ['email'])

def downgrade():
    op.drop_constraint('uq_chat_users_email', 'chat_users', type_='unique')
