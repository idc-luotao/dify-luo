"""add_admin_user_id_to_providers

Revision ID: 2025_03_19_1536
Revises: 2025_03_18_1353
Create Date: 2025-03-19 15:36:23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '2025_03_19_1536'
down_revision = 'add_admin_user_id_to_chat_users'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 admin_user_id 列到 providers 表
    op.add_column('providers', sa.Column('admin_user_id', UUID(as_uuid=False), nullable=True))


def downgrade():
    # 删除 admin_user_id 列
    op.drop_column('providers', 'admin_user_id')
