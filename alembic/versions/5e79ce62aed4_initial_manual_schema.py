"""initial_manual_schema

Revision ID: 5e79ce62aed4
Revises: None
Create Date: 2026-06-18 11:44:11.124055
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '5e79ce62aed4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            lang TEXT DEFAULT 'en',
            card_name TEXT,
            card_prof TEXT,
            wallet TEXT,
            balance FLOAT DEFAULT 0,
            price FLOAT DEFAULT 1,
            share_count INT DEFAULT 0,
            is_premium BOOLEAN DEFAULT FALSE,
            iwa_balance FLOAT DEFAULT 0,
            points FLOAT DEFAULT 0,
            role TEXT DEFAULT 'user',
            photo_file_id TEXT,
            state TEXT DEFAULT 'IDLE',
            community_verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            user_id BIGINT,
            ref_id BIGINT,
            PRIMARY KEY (user_id, ref_id)
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS premium_users (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            bot_name TEXT,
            amount FLOAT,
            tx_hash TEXT
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS casino_settings (
            id SERIAL PRIMARY KEY,
            house_edge FLOAT DEFAULT 0.15,
            is_active BOOLEAN DEFAULT TRUE
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS admin_logs (
            id SERIAL PRIMARY KEY,
            admin_id BIGINT,
            action TEXT,
            details TEXT,
            ts TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS market_cards (
            id SERIAL PRIMARY KEY,
            seller_id BIGINT,
            card_name TEXT,
            card_prof TEXT,
            price FLOAT,
            photo_file_id TEXT,
            level TEXT DEFAULT 'Newbie',
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS analytics (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            event_type VARCHAR(50),
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("""
        INSERT INTO casino_settings (house_edge, is_active)
        SELECT 0.15, TRUE
        WHERE NOT EXISTS (SELECT 1 FROM casino_settings)
    """)

def downgrade():
    op.drop_table('analytics')
    op.drop_table('market_cards')
    op.drop_table('admin_logs')
    op.drop_table('casino_settings')
    op.drop_table('premium_users')
    op.drop_table('referrals')
    op.drop_table('users')
