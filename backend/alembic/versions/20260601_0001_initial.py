from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260601_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("hashed_password", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_email_active", "users", ["email", "is_active"])
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("average_score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("duration_seconds >= 0", name="ck_sessions_duration_non_negative"),
        sa.CheckConstraint("average_score >= 0 AND average_score <= 100", name="ck_sessions_average_score_range"),
    )
    op.create_index("ix_sessions_user_started", "sessions", ["user_id", "started_at"])
    op.create_table(
        "posture_metrics",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("classification", sa.String(32), nullable=False),
        sa.Column("ratio", sa.Float()),
        sa.Column("distance", sa.Float()),
        sa.Column("angle", sa.Float()),
        sa.Column("alert", sa.String(255)),
        sa.CheckConstraint("score >= 0 AND score <= 100", name="ck_posture_metrics_score_range"),
    )
    op.create_index("ix_posture_metrics_session_captured", "posture_metrics", ["session_id", "captured_at"])
    op.create_table(
        "reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("file_path", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("session_id", name="uq_reports_session_id"),
    )
    op.create_index("ix_reports_user_generated", "reports", ["user_id", "generated_at"])
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_revoked", "refresh_tokens", ["user_id", "revoked_at"])


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("reports")
    op.drop_table("posture_metrics")
    op.drop_table("sessions")
    op.drop_table("users")
