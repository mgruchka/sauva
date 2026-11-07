"""Pastas e compartilhamento de um documento."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0003_demo_features"
down_revision = "0002_documents"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("folders",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False))
    op.create_index("ix_folders_user_id", "folders", ["user_id"])
    op.add_column("documents", sa.Column("folder_id", UUID(as_uuid=True), sa.ForeignKey("folders.id")))
    op.create_index("ix_documents_folder_id", "documents", ["folder_id"])
    op.create_table("share_links",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("recipient_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("redeemed_at", sa.DateTime(timezone=True)),
        sa.Column("grant_hash", sa.String(64), unique=True),
        sa.Column("access_expires_at", sa.DateTime(timezone=True)),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.create_index("ix_share_links_document_id", "share_links", ["document_id"])


def downgrade():
    op.drop_table("share_links")
    op.drop_index("ix_documents_folder_id", table_name="documents")
    op.drop_column("documents", "folder_id")
    op.drop_table("folders")
