"""initial migration

Revision ID: 27407898bb22
Revises: 
Create Date: 2026-06-26 12:47:30.818960

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '27407898bb22'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all initial tables, indexes, and constraints for LeadForge AI."""
    
    # 1. Create 'users' table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('role', sa.String(length=50), server_default='USER', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # 2. Create 'user_settings' table
    op.create_table(
        'user_settings',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('gemini_api_key', sa.String(length=255), nullable=True),
        sa.Column('serpapi_key', sa.String(length=255), nullable=True),
        sa.Column('cloudinary_cloud_name', sa.String(length=100), nullable=True),
        sa.Column('cloudinary_api_key', sa.String(length=100), nullable=True),
        sa.Column('cloudinary_api_secret', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_settings_id'), 'user_settings', ['id'], unique=False)
    op.create_index(op.f('ix_user_settings_user_id'), 'user_settings', ['user_id'], unique=True)

    # 3. Create 'leads' table
    op.create_table(
        'leads',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('website', sa.String(length=2083), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('reviews_count', sa.Integer(), nullable=True),
        sa.Column('maps_url', sa.String(length=2083), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=False),
        sa.Column('industry', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='NEW', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_leads_city'), 'leads', ['city'], unique=False)
    op.create_index(op.f('ix_leads_country'), 'leads', ['country'], unique=False)
    op.create_index(op.f('ix_leads_id'), 'leads', ['id'], unique=False)
    op.create_index(op.f('ix_leads_industry'), 'leads', ['industry'], unique=False)
    op.create_index(op.f('ix_leads_user_id'), 'leads', ['user_id'], unique=False)

    # 4. Create 'lead_scores' table
    op.create_table(
        'lead_scores',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('lead_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('overall_score', sa.Integer(), server_default='0', nullable=False),
        sa.Column('seo_score', sa.Integer(), server_default='0', nullable=False),
        sa.Column('ux_score', sa.Integer(), server_default='0', nullable=False),
        sa.Column('branding_score', sa.Integer(), server_default='0', nullable=False),
        sa.Column('trust_score', sa.Integer(), server_default='0', nullable=False),
        sa.Column('conversion_score', sa.Integer(), server_default='0', nullable=False),
        sa.Column('category', sa.String(length=50), server_default='Cold Lead', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lead_id')
    )
    op.create_index(op.f('ix_lead_scores_id'), 'lead_scores', ['id'], unique=False)
    op.create_index(op.f('ix_lead_scores_lead_id'), 'lead_scores', ['lead_id'], unique=True)

    # 5. Create 'audits' table
    op.create_table(
        'audits',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('lead_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('website_title', sa.String(length=500), nullable=True),
        sa.Column('meta_description', sa.String(length=1000), nullable=True),
        sa.Column('emails', sa.JSON(), nullable=True),
        sa.Column('phone_numbers', sa.JSON(), nullable=True),
        sa.Column('contact_form_present', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('social_links', sa.JSON(), nullable=True),
        sa.Column('technologies', sa.JSON(), nullable=True),
        sa.Column('ssl_status', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('images', sa.JSON(), nullable=True),
        sa.Column('navigation_structure', sa.JSON(), nullable=True),
        sa.Column('cta_buttons', sa.JSON(), nullable=True),
        sa.Column('testimonials_present', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('faq_present', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('executive_summary', sa.Text(), nullable=True),
        sa.Column('weaknesses', sa.JSON(), nullable=True),
        sa.Column('verdict', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lead_id')
    )
    op.create_index(op.f('ix_audits_id'), 'audits', ['id'], unique=False)
    op.create_index(op.f('ix_audits_lead_id'), 'audits', ['lead_id'], unique=True)

    # 6. Create 'screenshots' table
    op.create_table(
        'screenshots',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('lead_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('local_path', sa.String(length=1000), nullable=True),
        sa.Column('cloudinary_url', sa.String(length=2083), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lead_id')
    )
    op.create_index(op.f('ix_screenshots_id'), 'screenshots', ['id'], unique=False)
    op.create_index(op.f('ix_screenshots_lead_id'), 'screenshots', ['lead_id'], unique=True)

    # 7. Create 'outreaches' table
    op.create_table(
        'outreaches',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('lead_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('cold_email', sa.Text(), nullable=True),
        sa.Column('followup_email', sa.Text(), nullable=True),
        sa.Column('linkedin_message', sa.Text(), nullable=True),
        sa.Column('whatsapp_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lead_id')
    )
    op.create_index(op.f('ix_outreaches_id'), 'outreaches', ['id'], unique=False)
    op.create_index(op.f('ix_outreaches_lead_id'), 'outreaches', ['lead_id'], unique=True)

    # 8. Create 'revoked_tokens' table
    op.create_table(
        'revoked_tokens',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(length=500), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_revoked_tokens_id'), 'revoked_tokens', ['id'], unique=False)
    op.create_index(op.f('ix_revoked_tokens_token'), 'revoked_tokens', ['token'], unique=True)
    op.create_index(op.f('ix_revoked_tokens_expires_at'), 'revoked_tokens', ['expires_at'], unique=False)


def downgrade() -> None:
    """Drop all tables, indexes, and constraints for LeadForge AI."""
    op.drop_index(op.f('ix_revoked_tokens_expires_at'), table_name='revoked_tokens')
    op.drop_index(op.f('ix_revoked_tokens_token'), table_name='revoked_tokens')
    op.drop_index(op.f('ix_revoked_tokens_id'), table_name='revoked_tokens')
    op.drop_table('revoked_tokens')

    op.drop_index(op.f('ix_outreaches_lead_id'), table_name='outreaches')
    op.drop_index(op.f('ix_outreaches_id'), table_name='outreaches')
    op.drop_table('outreaches')
    
    op.drop_index(op.f('ix_screenshots_lead_id'), table_name='screenshots')
    op.drop_index(op.f('ix_screenshots_id'), table_name='screenshots')
    op.drop_table('screenshots')
    
    op.drop_index(op.f('ix_audits_lead_id'), table_name='audits')
    op.drop_index(op.f('ix_audits_id'), table_name='audits')
    op.drop_table('audits')
    
    op.drop_index(op.f('ix_lead_scores_lead_id'), table_name='lead_scores')
    op.drop_index(op.f('ix_lead_scores_id'), table_name='lead_scores')
    op.drop_table('lead_scores')
    
    op.drop_index(op.f('ix_leads_user_id'), table_name='leads')
    op.drop_index(op.f('ix_leads_industry'), table_name='leads')
    op.drop_index(op.f('ix_leads_id'), table_name='leads')
    op.drop_index(op.f('ix_leads_country'), table_name='leads')
    op.drop_index(op.f('ix_leads_city'), table_name='leads')
    op.drop_table('leads')
    
    op.drop_index(op.f('ix_user_settings_user_id'), table_name='user_settings')
    op.drop_index(op.f('ix_user_settings_id'), table_name='user_settings')
    op.drop_table('user_settings')
    
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
