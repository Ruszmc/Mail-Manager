"""init

Revision ID: 0001
Revises: 
Create Date: 2025-01-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("imap_host", sa.String(length=255), nullable=False),
        sa.Column("imap_port", sa.Integer(), nullable=False),
        sa.Column("imap_tls", sa.Boolean(), nullable=False),
        sa.Column("smtp_host", sa.String(length=255), nullable=False),
        sa.Column("smtp_port", sa.Integer(), nullable=False),
        sa.Column("smtp_tls", sa.Boolean(), nullable=False),
        sa.Column("password_enc", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "threads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("thread_key", sa.String(length=512), nullable=False),
        sa.Column("subject", sa.String(length=512)),
        sa.Column("last_message_at", sa.DateTime()),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("priority_score", sa.Integer(), nullable=False),
        sa.Column("priority_reason", sa.String(length=255), nullable=False),
        sa.Column("is_newsletter", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.UniqueConstraint("account_id", "thread_key", name="uq_thread_key"),
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("thread_id", sa.Integer(), nullable=False),
        sa.Column("imap_uid", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.String(length=512)),
        sa.Column("in_reply_to", sa.String(length=512)),
        sa.Column("references", sa.Text()),
        sa.Column("from_addr", sa.String(length=512)),
        sa.Column("to_addr", sa.String(length=1024)),
        sa.Column("subject", sa.String(length=512)),
        sa.Column("date", sa.DateTime()),
        sa.Column("list_unsubscribe", sa.Text()),
        sa.Column("snippet", sa.Text()),
        sa.ForeignKeyConstraint(["thread_id"], ["threads.id"]),
        sa.UniqueConstraint("thread_id", "imap_uid", name="uq_imap_uid"),
    )
    op.create_table(
        "labels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "thread_labels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("thread_id", sa.Integer(), nullable=False),
        sa.Column("label_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["thread_id"], ["threads.id"]),
        sa.ForeignKeyConstraint(["label_id"], ["labels.id"]),
        sa.UniqueConstraint("thread_id", "label_id", name="uq_thread_label"),
    )
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("sender", sa.String(length=512), nullable=False),
        sa.Column("list_unsubscribe", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
    )
    op.create_table(
        "action_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("thread_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["thread_id"], ["threads.id"]),
    )


def downgrade() -> None:
    op.drop_table("action_items")
    op.drop_table("subscriptions")
    op.drop_table("thread_labels")
    op.drop_table("labels")
    op.drop_table("messages")
    op.drop_table("threads")
    op.drop_table("accounts")
