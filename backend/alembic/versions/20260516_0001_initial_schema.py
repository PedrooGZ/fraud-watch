"""initial schema

Revision ID: 20260516_0001
Revises:
Create Date: 2026-05-16 00:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260516_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    op.create_table(
        "model_versions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("model_type", sa.String(length=255), nullable=False),
        sa.Column("artifact_path", sa.String(length=500), nullable=False),
        sa.Column("metadata_path", sa.String(length=500), nullable=False),
        sa.Column("pr_auc", sa.Float(), nullable=False),
        sa.Column("brier_score", sa.Float(), nullable=False),
        sa.Column("n_features", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_model_versions_name"), "model_versions", ["name"], unique=False)

    op.create_table(
        "policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("threshold_cost", sa.Float(), nullable=False),
        sa.Column("max_alerts", sa.Integer(), nullable=False),
        sa.Column("priority_mode", sa.String(length=50), nullable=False),
        sa.Column("error_cost_mode", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "policy_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("policy_id", sa.Integer(), nullable=False),
        sa.Column("changed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("old_values_json", sa.JSON(), nullable=False),
        sa.Column("new_values_json", sa.JSON(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["changed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["policy_id"], ["policies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_policy_history_changed_by_user_id"), "policy_history", ["changed_by_user_id"], unique=False)
    op.create_index(op.f("ix_policy_history_policy_id"), "policy_history", ["policy_id"], unique=False)

    op.create_table(
        "batch_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("original_path", sa.String(length=500), nullable=True),
        sa.Column("output_path", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("total_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("valid_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("invalid_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("review_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_batch_jobs_created_by_user_id"), "batch_jobs", ["created_by_user_id"], unique=False)
    op.create_index(op.f("ix_batch_jobs_status"), "batch_jobs", ["status"], unique=False)

    op.create_table(
        "drift_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("psi", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("bins", sa.Integer(), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("amount_multiplier", sa.Float(), nullable=False),
        sa.Column("ref_mean", sa.Float(), nullable=False),
        sa.Column("ref_p95", sa.Float(), nullable=False),
        sa.Column("new_mean", sa.Float(), nullable=False),
        sa.Column("new_p95", sa.Float(), nullable=False),
        sa.Column("summary_path", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_drift_runs_status"), "drift_runs", ["status"], unique=False)

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("report_code", sa.String(length=100), nullable=False),
        sa.Column("period", sa.String(length=100), nullable=False),
        sa.Column("format", sa.String(length=20), nullable=False),
        sa.Column("detail_level", sa.String(length=50), nullable=False),
        sa.Column("sections_json", sa.JSON(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("generated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["generated_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("report_code"),
    )
    op.create_index(op.f("ix_reports_generated_by_user_id"), "reports", ["generated_by_user_id"], unique=False)
    op.create_index(op.f("ix_reports_report_code"), "reports", ["report_code"], unique=False)

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=True),
        sa.Column("entity_id", sa.String(length=100), nullable=True),
        sa.Column("details_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_events_entity_id"), "audit_events", ["entity_id"], unique=False)
    op.create_index(op.f("ix_audit_events_entity_type"), "audit_events", ["entity_type"], unique=False)
    op.create_index(op.f("ix_audit_events_event_type"), "audit_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_audit_events_user_id"), "audit_events", ["user_id"], unique=False)

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("batch_job_id", sa.Integer(), nullable=True),
        sa.Column("model_version_id", sa.Integer(), nullable=True),
        sa.Column("transaction_id", sa.String(length=255), nullable=True),
        sa.Column("input_features_json", sa.JSON(), nullable=False),
        sa.Column("proba_fraud", sa.Float(), nullable=True),
        sa.Column("review", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("is_valid", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("missing_features_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["batch_job_id"], ["batch_jobs.id"]),
        sa.ForeignKeyConstraint(["model_version_id"], ["model_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_predictions_batch_job_id"), "predictions", ["batch_job_id"], unique=False)
    op.create_index(op.f("ix_predictions_model_version_id"), "predictions", ["model_version_id"], unique=False)
    op.create_index(op.f("ix_predictions_transaction_id"), "predictions", ["transaction_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_predictions_transaction_id"), table_name="predictions")
    op.drop_index(op.f("ix_predictions_model_version_id"), table_name="predictions")
    op.drop_index(op.f("ix_predictions_batch_job_id"), table_name="predictions")
    op.drop_table("predictions")

    op.drop_index(op.f("ix_audit_events_user_id"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_event_type"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_entity_type"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_entity_id"), table_name="audit_events")
    op.drop_table("audit_events")

    op.drop_index(op.f("ix_reports_report_code"), table_name="reports")
    op.drop_index(op.f("ix_reports_generated_by_user_id"), table_name="reports")
    op.drop_table("reports")

    op.drop_index(op.f("ix_drift_runs_status"), table_name="drift_runs")
    op.drop_table("drift_runs")

    op.drop_index(op.f("ix_batch_jobs_status"), table_name="batch_jobs")
    op.drop_index(op.f("ix_batch_jobs_created_by_user_id"), table_name="batch_jobs")
    op.drop_table("batch_jobs")

    op.drop_index(op.f("ix_policy_history_policy_id"), table_name="policy_history")
    op.drop_index(op.f("ix_policy_history_changed_by_user_id"), table_name="policy_history")
    op.drop_table("policy_history")

    op.drop_table("policies")

    op.drop_index(op.f("ix_model_versions_name"), table_name="model_versions")
    op.drop_table("model_versions")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
