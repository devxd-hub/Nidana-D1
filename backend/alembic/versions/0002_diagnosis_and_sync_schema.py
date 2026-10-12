"""Diagnosis, recovery reports, sync receipts, and chunk provenance schema.

Revision ID: 0002_diagnosis_and_sync_schema
Revises: 0001_initial_schema
Create Date: 2026-10-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_diagnosis_and_sync_schema"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Diagnostic Runs table
    op.create_table(
        "diagnostic_runs",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("attempt_id", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="IN_PROGRESS"),
        sa.Column("primary_hypothesis", sa.String(length=50), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("hypotheses_data", sa.JSON(), nullable=False),
        sa.Column("selected_probe_ids", sa.JSON(), nullable=False),
        sa.Column("evidence_refs", sa.JSON(), nullable=False),
        sa.Column("trace_summary", sa.Text(), nullable=True),
        sa.Column("recovery_eligible", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["attempt_id"], ["attempts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_diag_runs_user_status", "diagnostic_runs", ["user_id", "status"])
    op.create_index("ix_diag_runs_attempt", "diagnostic_runs", ["attempt_id"])

    # 2. Diagnostic Probes table
    op.create_table(
        "diagnostic_probes",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("diagnostic_run_id", sa.String(length=50), nullable=False),
        sa.Column("probe_type", sa.String(length=50), nullable=False),
        sa.Column("question_id", sa.String(length=50), nullable=True),
        sa.Column("prompt_stem", sa.Text(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=True),
        sa.Column("expected_discriminator", sa.JSON(), nullable=True),
        sa.Column("student_response", sa.JSON(), nullable=True),
        sa.Column("outcome", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["diagnostic_run_id"], ["diagnostic_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_probes_run", "diagnostic_probes", ["diagnostic_run_id"])

    # 3. Recovery Reports table
    op.create_table(
        "recovery_reports",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("diagnostic_run_id", sa.String(length=50), nullable=False),
        sa.Column("attempt_id", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column("marks_at_risk", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("identified_cause", sa.String(length=100), nullable=False),
        sa.Column("targeted_repair", sa.Text(), nullable=False),
        sa.Column("mastery_check_details", sa.JSON(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["diagnostic_run_id"], ["diagnostic_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["attempt_id"], ["attempts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("diagnostic_run_id"),
    )
    op.create_index("ix_reports_user", "recovery_reports", ["user_id"])
    op.create_index("ix_reports_attempt", "recovery_reports", ["attempt_id"])

    # 4. Sync Receipts table
    op.create_table(
        "sync_receipts",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("client_event_id", sa.String(length=100), nullable=False),
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="ACCEPTED"),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sync_receipts_client_event", "sync_receipts", ["client_event_id"], unique=True)
    op.create_index("ix_sync_receipts_user_status", "sync_receipts", ["user_id", "status"])

    # 5. Add provenance columns to content_chunks
    with op.batch_alter_table("content_chunks") as batch_op:
        batch_op.add_column(sa.Column("subject_id", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("class_level", sa.Integer(), nullable=False, server_default="10"))
        batch_op.add_column(sa.Column("source_locator", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("checksum", sa.String(length=64), nullable=True))
        batch_op.create_foreign_key("fk_chunks_subject", "subjects", ["subject_id"], ["id"], ondelete="SET NULL")
        batch_op.create_index("ix_content_chunks_class_level", ["class_level"])
        batch_op.create_index("ix_content_chunks_language", ["language"])


def downgrade() -> None:
    with op.batch_alter_table("content_chunks") as batch_op:
        batch_op.drop_index("ix_content_chunks_language")
        batch_op.drop_index("ix_content_chunks_class_level")
        batch_op.drop_constraint("fk_chunks_subject", type_="foreignkey")
        batch_op.drop_column("checksum")
        batch_op.drop_column("source_locator")
        batch_op.drop_column("class_level")
        batch_op.drop_column("subject_id")

    op.drop_table("sync_receipts")
    op.drop_table("recovery_reports")
    op.drop_table("diagnostic_probes")
    op.drop_table("diagnostic_runs")
