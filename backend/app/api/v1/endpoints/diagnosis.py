"""API endpoints for the LangGraph WHY Engine and Mark Recovery flow."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_user_service
from app.core.security import AuthenticatedUser, get_current_user
from app.models import DiagnosticRun, RecoveryReport
from app.services.user_service import UserService
from app.why_engine.service import WhyEngineService

router = APIRouter(prefix="/diagnosis", tags=["WHY Engine & Mark Recovery"])


def get_why_engine(db: Session = Depends(get_db)) -> WhyEngineService:
    return WhyEngineService(db)


class RecoveryVerifyRequest(BaseModel):
    is_mastery_correct: bool = Field(description="Whether the follow-up mastery check was answered correctly")


@router.post("/run/{attempt_id}", status_code=status.HTTP_200_OK, summary="Execute WHY Engine diagnosis on an attempt")
def execute_diagnosis(
    attempt_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    engine: WhyEngineService = Depends(get_why_engine),
) -> Dict[str, Any]:
    user_service.get_or_create_from_token(current_user)
    run = engine.diagnose_attempt(attempt_id=attempt_id, user=current_user)
    return {
        "run_id": run.id,
        "attempt_id": run.attempt_id,
        "status": run.status,
        "primary_hypothesis": run.primary_hypothesis,
        "confidence_score": run.confidence_score,
        "hypotheses": run.hypotheses_data,
        "selected_probes": [
            {
                "id": p.id,
                "type": p.probe_type,
                "prompt": p.prompt_stem,
                "options": p.options,
            }
            for p in run.probes
        ],
        "evidence_refs": run.evidence_refs,
        "trace_summary": run.trace_summary,
        "recovery_eligible": run.recovery_eligible,
        "recovery_report_id": run.recovery_report.id if run.recovery_report else None,
    }


@router.get("/reports/{report_id}", status_code=status.HTTP_200_OK, summary="Get Mark Recovery Report")
def get_recovery_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    report = db.query(RecoveryReport).filter_by(id=report_id, user_id=current_user.id).first()
    if not report:
        return {"error": "Report not found or not owned by caller"}
    return {
        "report_id": report.id,
        "diagnostic_run_id": report.diagnostic_run_id,
        "attempt_id": report.attempt_id,
        "marks_at_risk": report.marks_at_risk,
        "identified_cause": report.identified_cause,
        "targeted_repair": report.targeted_repair,
        "mastery_check_details": report.mastery_check_details,
        "is_verified": report.is_verified,
        "verified_at": report.verified_at,
    }


@router.post("/reports/{report_id}/verify", status_code=status.HTTP_200_OK, summary="Verify Mark Recovery outcome")
def verify_mark_recovery(
    report_id: str,
    payload: RecoveryVerifyRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    engine: WhyEngineService = Depends(get_why_engine),
) -> Dict[str, Any]:
    report = engine.verify_recovery(
        report_id=report_id,
        is_mastery_correct=payload.is_mastery_correct,
        user=current_user,
    )
    return {
        "report_id": report.id,
        "is_verified": report.is_verified,
        "verified_at": report.verified_at,
        "status": "RECOVERED" if report.is_verified else "UNVERIFIED",
    }
