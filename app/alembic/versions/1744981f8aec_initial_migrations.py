"""initial migrations

Revision ID: 1744981f8aec
Revises: 
Create Date: 2025-12-06 15:24:49.754942
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1744981f8aec'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # PROFILES
    op.create_table(
        'profiles',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('middle_name', sa.String(length=100)),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('email_address', sa.String(), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=False),
        sa.Column('data', sa.JSON()),
        sa.Column('is_deleted', sa.Integer(), server_default='0', nullable=False),
        sa.Column('status', sa.Integer(), server_default='10', nullable=False),
        sa.Column('created_at', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email_address'),
        sa.UniqueConstraint('phone_number'),
    )

    # USERS — FIXED (NO "id" column!)
    op.create_table(
        'users',
        sa.Column('user_id', sa.Uuid(), primary_key=True, nullable=False),
        sa.Column('username', sa.String(length=64), nullable=False, unique=True),
        sa.Column('profile_id', sa.String(length=32), nullable=False, unique=True),
        sa.Column('auth_key', sa.String(length=64)),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('password_reset_token', sa.String(length=255)),
        sa.Column('verification_token', sa.String(length=255)),
        sa.Column('status', sa.Integer(), server_default='10', nullable=False),
        sa.Column('created_at', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.Integer(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['profiles.id'], ondelete='CASCADE')
    )

    # OTP TABLE
    op.create_table(
        'one_time_passwords',
        sa.Column('otp_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('password', sa.String(), nullable=False),
        sa.Column('created_at', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.Integer(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('otp_id')
    )

    # PASSWORD HISTORY
    op.create_table(
        'password_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('old_password', sa.String(), nullable=False),
        sa.Column('created_at', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.Integer(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # USER SETTINGS
    op.create_table(
        'user_settings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False, unique=True),
        sa.Column('data', sa.JSON(), nullable=False),
        sa.Column('status', sa.Integer(), server_default='10', nullable=False),
        sa.Column('created_at', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.Integer(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # ACCESS TOKENS
    op.create_table(
        'refresh_tokens',
        sa.Column('token_id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Uuid()),
        sa.Column('token', sa.Text(), nullable=False, unique=True),
        sa.Column('ip_address', sa.String(length=32), server_default='127.0.0.1', nullable=False),
        sa.Column('user_agent', sa.String(), nullable=False),
        sa.Column('is_trusted', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE', onupdate='CASCADE')
    )

    # 2FA TOKENS
    op.create_table(
        'twofa_tokens',
        sa.Column('token_id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('expires_at', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE', onupdate='CASCADE')
    )

    # ACCESS LOG
    op.create_table(
        'access_log',
        sa.Column('access_id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Uuid()),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('extra_data', sa.Text()),
        sa.Column('ip_address', sa.String(length=45)),
        sa.Column('user_agent', sa.Text()),
        sa.Column('is_deleted', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE', onupdate='CASCADE')
    )

    # LOGIN ATTEMPT
    op.create_table(
        'login_attempt',
        sa.Column('attempt_id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Uuid()),
        sa.Column('username', sa.String(length=255)),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('is_deleted', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.user_id'],
            ondelete='SET NULL'
        )
    )

    # Indexes for login_attempt
    op.create_index('idx_login_attempt_user_id', 'login_attempt', ['user_id'])
    op.create_index('idx_login_attempt_ip_address', 'login_attempt', ['ip_address'])



def downgrade():
    op.drop_index('idx_login_attempt_ip_address', table_name='login_attempt')
    op.drop_index('idx_login_attempt_user_id', table_name='login_attempt')
    op.drop_table('login_attempt')

    # DROP access_log
    op.drop_table('access_log')
    # DROP twofa_tokens
    op.drop_table('twofa_tokens')
    # DROP refresh_tokens
    op.drop_table('refresh_tokens')
    op.drop_table('user_settings')
    op.drop_table('password_history')
    op.drop_table('one_time_passwords')
    op.drop_table('users')
    op.drop_table('profiles')
