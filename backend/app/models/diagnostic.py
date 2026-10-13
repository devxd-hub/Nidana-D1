"""Diagnostic, probe, and recovery report domain models for the WHY Engine."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class DiagnosticRun(Base, TimestampMixin):
    """Authoritative record of a WHY Engine diagnostic investigation for an attempt."""

    __tablename__ = "diagnostic_runs"
    __table_args__ = (
        Index("ix_diag_runs_user_status", "user_id", "status"),
        Index("ix_diag_runs_attempt", "attempt_id"),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # UUID
    attempt_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("attempts.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), default="IN_PROGRESS", nullable=False, index=True)
    # Hypotheses: PREREQUISITE_GAP, MISCONCEPTION, LANGUAGE_CONFUSION, PROCEDURAL_ERROR, CARELESS_EXECUTION, INSUFFICIENT_EVIDENCE
    primary_hypothesis: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Scored hypotheses array: [{"hypothesis": "MISCONCEPTION", "score": 0.85, "reason": "..."}]
    hypotheses_data: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    # Selected probe IDs (max 2 for MVP)
    selected_probe_ids: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    # Grounded evidence references (chunk IDs / titles)
    evidence_refs: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    # Safe user-observable trace explanation (strictly avoids hidden chain-of-thought)
    trace_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    recovery_eligible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    probes: Mapped[List["DiagnosticProbe"]] = relationship(
        "DiagnosticProbe", back_populates="diagnostic_run", cascade="all, delete-orphan"
    )
    recovery_report: Mapped[Optional["RecoveryReport"]] = relationship(
        "RecoveryReport", back_populates="diagnostic_run", uselist=False, cascade="all, delete-orphan"
    )


class DiagnosticProbe(Base, TimestampMixin):
    """Specific diagnostic probe administered to test candidate hypotheses."""

    __tablename__ = "diagnostic_probes"
    __table_args__ = (
        Index("ix_probes_run", "diagnostic_run_id"),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    diagnostic_run_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("diagnostic_runs.id", ondelete="CASCADE"), nullable=False
    )
    probe_type: Mapped[str] = mapped_column(String(50), nullable=False)  # PREREQUISITE_CHECK, DISAMBIGUATION, STEP_ISOLATION
    question_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("questions.id", ondelete="SET NULL"), nullable=True
    )
    prompt_stem: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    expected_discriminator: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    student_response: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    outcome: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # CONFIRMED_GAP, DISPROVED_GAP, INCONCLUSIVE

    # Relationships
    diagnostic_run: Mapped["DiagnosticRun"] = relationship("DiagnosticRun", back_populates="probes")


class RecoveryReport(Base, TimestampMixin):
    """Mark Recovery Report summarizing diagnosed weakness, targeted repair, and mastery verification."""

    __tablename__ = "recovery_reports"
    __table_args__ = (
        Index("ix_reports_user", "user_id"),
        Index("ix_reports_attempt", "attempt_id"),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    diagnostic_run_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("diagnostic_runs.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    attempt_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("attempts.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    marks_at_risk: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    identified_cause: Mapped[str] = mapped_column(String(100), nullable=False)
    targeted_repair: Mapped[str] = mapped_column(Text, nullable=False)
    mastery_check_details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    diagnostic_run: Mapped["DiagnosticRun"] = relationship("DiagnosticRun", back_populates="recovery_report")
