"""initial schema

Revision ID: 001
Revises:
Create Date: ...

"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('users',
        sa.Column('user_id', sa.BigInteger, primary_key=True),
        sa.Column('lang', sa.String(), default='en'),
        sa.Column('card_name', sa.String()),
        sa.Column('card_prof', sa.String()),
        sa.Column('wallet', sa.String()),
        sa.Column('price', sa.Float(), default=1),
        sa.Column('ref_id', sa.BigInteger),
        sa.Column('share_count', sa.Integer(), default=0),
        sa.Column('level', sa.String(), default='free'),
        sa.Column('minisite', sa.String()),
        sa.Column('balance', sa.Numeric(), default=0),
        sa.Column('is_premium', sa.Boolean(), default=False),
    )
    op.create_table('wallets',
        sa.Column('user_id', sa.BigInteger, sa.ForeignKey('users.user_id'), unique=True),
        sa.Column('address', sa.String()),
        sa.Column('verified', sa.Boolean(), default=False),
    )
    op.create_table('settings',
        sa.Column('key', sa.String(), primary_key=True),
        sa.Column('value', sa.String()),
    )

def downgrade():
    op.drop_table('wallets')
    op.drop_table('settings')
    op.drop_table('users')
