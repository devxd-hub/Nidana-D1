"""Initial database schema for NIDANA.

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-10-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="learner"),
        sa.Column("preferred_language", sa.String(length=20), nullable=False, server_default="odia"),
        sa.Column("exam_target", sa.String(length=50), nullable=False, server_default="chse_class_12"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])

    # 2. Subjects table
    op.create_table(
        "subjects",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name_en", sa.String(length=100), nullable=False),
        sa.Column("name_or", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_subjects_code", "subjects", ["code"], unique=True)

    # 3. Chapters table
    op.create_table(
        "chapters",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("subject_id", sa.String(length=50), nullable=False),
        sa.Column("class_level", sa.Integer(), nullable=False),
        sa.Column("chapter_number", sa.Integer(), nullable=False),
        sa.Column("title_en", sa.String(length=255), nullable=False),
        sa.Column("title_or", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("language_availability", sa.JSON(), nullable=False),
        sa.Column("content_version", sa.String(length=20), nullable=False, server_default="1.0.0"),
        sa.Column("approval_state", sa.String(length=20), nullable=False, server_default="approved"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("class_level IN (9, 10, 12)", name="ck_chapters_class_level"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chapters_subject_id", "chapters", ["subject_id"])
    op.create_index("ix_chapters_class_level", "chapters", ["class_level"])
    op.create_index("ix_chapters_approval_state", "chapters", ["approval_state"])
    op.create_index("ix_chapters_subject_class", "chapters", ["subject_id", "class_level"])

    # 4. Concepts table
    op.create_table(
        "concepts",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("subject_id", sa.String(length=50), nullable=False),
        sa.Column("chapter_id", sa.String(length=50), nullable=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name_en", sa.String(length=255), nullable=False),
        sa.Column("name_or", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("prerequisite_concept_ids", sa.JSON(), nullable=False),
        sa.Column("terminology_mapping", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_concepts_code", "concepts", ["code"], unique=True)
    op.create_index("ix_concepts_subject_id", "concepts", ["subject_id"])
    op.create_index("ix_concepts_chapter_id", "concepts", ["chapter_id"])

    # 5. Questions table
    op.create_table(
        "questions",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("chapter_id", sa.String(length=50), nullable=False),
        sa.Column("concept_id", sa.String(length=50), nullable=False),
        sa.Column("type", sa.String(length=30), nullable=False, server_default="single_choice"),
        sa.Column("difficulty", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("marks", sa.Float(), nullable=False, server_default="4.0"),
        sa.Column("negative_marks", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("expected_time_seconds", sa.Integer(), nullable=False, server_default="120"),
        sa.Column("language", sa.String(length=20), nullable=False, server_default="bilingual"),
        sa.Column("stem_en", sa.Text(), nullable=False),
        sa.Column("stem_or", sa.Text(), nullable=True),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("correct_answer", sa.JSON(), nullable=False),
        sa.Column("explanation_en", sa.Text(), nullable=True),
        sa.Column("explanation_or", sa.Text(), nullable=True),
        sa.Column("distractor_metadata", sa.JSON(), nullable=False),
        sa.Column("approval_state", sa.String(length=20), nullable=False, server_default="approved"),
        sa.Column("version", sa.String(length=20), nullable=False, server_default="1.0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["concept_id"], ["concepts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_questions_chapter_id", "questions", ["chapter_id"])
    op.create_index("ix_questions_concept_id", "questions", ["concept_id"])
    op.create_index("ix_questions_difficulty", "questions", ["difficulty"])
    op.create_index("ix_questions_approval_state", "questions", ["approval_state"])
    op.create_index("ix_questions_chapter_concept", "questions", ["chapter_id", "concept_id"])
    op.create_index("ix_questions_difficulty_approval", "questions", ["difficulty", "approval_state"])

    # 6. Question Variants table
    op.create_table(
        "question_variants",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("base_question_id", sa.String(length=50), nullable=False),
        sa.Column("variant_purpose", sa.String(length=50), nullable=False),
        sa.Column("stem_en", sa.Text(), nullable=True),
        sa.Column("stem_or", sa.Text(), nullable=True),
        sa.Column("options", sa.JSON(), nullable=True),
        sa.Column("correct_answer", sa.JSON(), nullable=False),
        sa.Column("explanation_en", sa.Text(), nullable=True),
        sa.Column("explanation_or", sa.Text(), nullable=True),
        sa.Column("changes_summary", sa.Text(), nullable=True),
        sa.Column("approval_state", sa.String(length=20), nullable=False, server_default="approved"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["base_question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_question_variants_base_question_id", "question_variants", ["base_question_id"])
    op.create_index("ix_question_variants_variant_purpose", "question_variants", ["variant_purpose"])
    op.create_index("ix_question_variants_approval_state", "question_variants", ["approval_state"])

    # 7. Content Chunks table
    op.create_table(
        "content_chunks",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("chapter_id", sa.String(length=50), nullable=False),
        sa.Column("concept_id", sa.String(length=50), nullable=True),
        sa.Column("source_title", sa.String(length=255), nullable=False),
        sa.Column("section_title", sa.String(length=255), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(length=20), nullable=False, server_default="bilingual"),
        sa.Column("text_content", sa.Text(), nullable=False),
        sa.Column("content_version", sa.String(length=20), nullable=False, server_default="1.0.0"),
        sa.Column("approval_state", sa.String(length=20), nullable=False, server_default="approved"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["concept_id"], ["concepts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_content_chunks_chapter_id", "content_chunks", ["chapter_id"])
    op.create_index("ix_content_chunks_concept_id", "content_chunks", ["concept_id"])
    op.create_index("ix_content_chunks_approval_state", "content_chunks", ["approval_state"])

    # 8. Attempts table
    op.create_table(
        "attempts",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column("question_id", sa.String(length=50), nullable=True),
        sa.Column("variant_id", sa.String(length=50), nullable=True),
        sa.Column("lifecycle_state", sa.String(length=30), nullable=False, server_default="in_progress"),
        sa.Column("submitted_response", sa.JSON(), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("marks_obtained", sa.Float(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_taken_seconds", sa.Integer(), nullable=True),
        sa.Column("learning_signals", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["variant_id"], ["question_variants.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_attempts_user_id", "attempts", ["user_id"])
    op.create_index("ix_attempts_question_id", "attempts", ["question_id"])
    op.create_index("ix_attempts_lifecycle_state", "attempts", ["lifecycle_state"])
    op.create_index("ix_attempts_user_lifecycle", "attempts", ["user_id", "lifecycle_state"])

    # 9. Study Plans table
    op.create_table(
        "study_plans",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("target_exam", sa.String(length=50), nullable=False, server_default="chse_class_12"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_study_plans_user_id", "study_plans", ["user_id"])
    op.create_index("ix_study_plans_status", "study_plans", ["status"])

    # 10. Study Plan Tasks table
    op.create_table(
        "study_plan_tasks",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("study_plan_id", sa.String(length=50), nullable=False),
        sa.Column("concept_id", sa.String(length=50), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence_source", sa.String(length=255), nullable=True),
        sa.Column("target_weakness", sa.String(length=100), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("follow_up_question_id", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["study_plan_id"], ["study_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["concept_id"], ["concepts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["follow_up_question_id"], ["questions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_study_plan_tasks_study_plan_id", "study_plan_tasks", ["study_plan_id"])
    op.create_index("ix_study_plan_tasks_status", "study_plan_tasks", ["status"])
    op.create_index("ix_tasks_plan_status", "study_plan_tasks", ["study_plan_id", "status"])


def downgrade() -> None:
    op.drop_table("study_plan_tasks")
    op.drop_table("study_plans")
    op.drop_table("attempts")
    op.drop_table("content_chunks")
    op.drop_table("question_variants")
    op.drop_table("questions")
    op.drop_table("concepts")
    op.drop_table("chapters")
    op.drop_table("subjects")
    op.drop_table("users")
