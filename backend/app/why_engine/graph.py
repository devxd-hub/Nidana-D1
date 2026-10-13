"""LangGraph orchestration state machine for NIDANA's WHY Engine.

Loop: Attempt -> Diagnose -> Evidence Retrieval -> Probe Selection -> Recovery Report.
"""

from typing import Any, Dict, List, Optional, TypedDict
from langgraph.graph import END, StateGraph

from app.rag.chroma_client import ChromaVectorIndex
from app.rag.provenance import build_grounded_context
from app.why_engine.gemini_adapter import GeminiAdapter


class DiagnosisState(TypedDict):
    """Execution state for the WHY Engine diagnosis state machine."""

    attempt_id: str
    user_id: str
    question_id: str
    stem: str
    selected_option: Optional[str]
    correct_option: Optional[str]
    is_correct: bool
    marks_lost: float
    class_level: int
    subject_id: Optional[str]
    chapter_id: Optional[str]

    # RAG Retrieval
    retrieved_chunks: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]
    grounded_evidence_text: str

    # Hypotheses & Probes (at most 2 probes)
    hypotheses: List[Dict[str, Any]]
    selected_probes: List[Dict[str, Any]]
    primary_cause: str
    confidence_score: float
    is_uncertain: bool

    # Output Report & Trace
    recovery_report: Optional[Dict[str, Any]]
    safe_trace_summary: str


def evaluate_attempt_node(state: DiagnosisState) -> Dict[str, Any]:
    """Node 1: Evaluates attempt eligibility."""
    if state["is_correct"]:
        return {
            "primary_cause": "NONE_CORRECT_ANSWER",
            "is_uncertain": False,
            "confidence_score": 1.0,
            "safe_trace_summary": "Attempt was evaluated as correct. No remediation required.",
        }

    return {
        "safe_trace_summary": f"Starting diagnosis for incorrect response on question {state['question_id']}."
    }


def retrieve_rag_evidence_node(state: DiagnosisState) -> Dict[str, Any]:
    """Node 2: Retrieves 3-5 approved syllabus chunks with strict curriculum filters."""
    if state["is_correct"]:
        return {"retrieved_chunks": [], "citations": [], "grounded_evidence_text": ""}

    index = ChromaVectorIndex()
    chunks = index.query(
        query_text=state["stem"],
        class_level=state["class_level"],
        subject_id=state["subject_id"],
        chapter_id=state["chapter_id"],
        top_k=4,
    )
    grounded_data = build_grounded_context(chunks)

    return {
        "retrieved_chunks": chunks,
        "citations": grounded_data["citations"],
        "grounded_evidence_text": grounded_data["grounded_text"],
    }


def formulate_hypotheses_node(state: DiagnosisState) -> Dict[str, Any]:
    """Node 3: Formulates candidate hypotheses using Gemini adapter."""
    if state["is_correct"]:
        return {"hypotheses": []}

    gemini = GeminiAdapter()
    hypotheses = gemini.formulate_hypotheses(
        question_stem=state["stem"],
        selected_option=state["selected_option"] or "",
        correct_option=state["correct_option"] or "",
    )
    hypotheses_dicts = [h.model_dump() for h in hypotheses]

    primary = hypotheses_dicts[0] if hypotheses_dicts else {"hypothesis": "INSUFFICIENT_EVIDENCE", "score": 0.5}
    is_uncertain = primary["score"] < 0.6 or primary["hypothesis"] == "INSUFFICIENT_EVIDENCE"

    return {
        "hypotheses": hypotheses_dicts,
        "primary_cause": primary["hypothesis"],
        "confidence_score": primary["score"],
        "is_uncertain": is_uncertain,
    }


def select_probes_node(state: DiagnosisState) -> Dict[str, Any]:
    """Node 4: Selects up to 2 high-information diagnostic probes."""
    if state["is_correct"] or state["is_uncertain"]:
        return {"selected_probes": []}

    # Generate up to 2 targeted diagnostic probes based on the primary hypothesis
    probes = [
        {
            "probe_id": f"prb_{state['question_id']}_1",
            "probe_type": "PREREQUISITE_CHECK",
            "prompt_stem": f"Before re-attempting, do you recall the core defining rule regarding {state['primary_cause']}?",
            "options": [
                {"id": "A", "text": "Yes, I understand the definition and formula."},
                {"id": "B", "text": "No, I confused the terms with a related concept."},
            ],
            "outcome": None,
        },
        {
            "probe_id": f"prb_{state['question_id']}_2",
            "probe_type": "CONCEPT_DISAMBIGUATION",
            "prompt_stem": "Which property changes direction during this process?",
            "options": [
                {"id": "A", "text": "Direction of velocity vector."},
                {"id": "B", "text": "Scalar magnitude only."},
            ],
            "outcome": None,
        },
    ]

    return {"selected_probes": probes[:2]}


def generate_recovery_report_node(state: DiagnosisState) -> Dict[str, Any]:
    """Node 5: Assembles the Mark Recovery Report with targeted repair plan."""
    if state["is_correct"]:
        return {"recovery_report": None}

    gemini = GeminiAdapter()
    repair_plan = gemini.generate_repair_explanation(
        identified_cause=state["primary_cause"],
        evidence_text=state["grounded_evidence_text"],
    )

    report_dict = {
        "marks_at_risk": state["marks_lost"],
        "identified_cause": state["primary_cause"],
        "targeted_repair": repair_plan,
        "is_uncertain": state["is_uncertain"],
        "mastery_check_details": {
            "type": "FOLLOW_UP_VARIANT",
            "concept_id": state.get("chapter_id"),
            "passing_threshold": 1.0,
        },
    }

    safe_summary = (
        f"Diagnosed cause: {state['primary_cause']} (confidence: {state['confidence_score']:.2f}). "
        f"Retrieved {len(state['retrieved_chunks'])} approved syllabus citations. "
        f"{len(state['selected_probes'])} probes scheduled."
    )

    return {
        "recovery_report": report_dict,
        "safe_trace_summary": safe_summary,
    }


def should_continue_after_eval(state: DiagnosisState) -> str:
    if state["is_correct"]:
        return END
    return "retrieve_rag_evidence"


def create_why_engine_graph():
    """Builds and compiles the diagnosis StateGraph."""
    workflow = StateGraph(DiagnosisState)

    workflow.add_node("evaluate_attempt", evaluate_attempt_node)
    workflow.add_node("retrieve_rag_evidence", retrieve_rag_evidence_node)
    workflow.add_node("formulate_hypotheses", formulate_hypotheses_node)
    workflow.add_node("select_probes", select_probes_node)
    workflow.add_node("generate_recovery_report", generate_recovery_report_node)

    workflow.set_entry_point("evaluate_attempt")

    workflow.add_conditional_edges(
        "evaluate_attempt",
        should_continue_after_eval,
        {END: END, "retrieve_rag_evidence": "retrieve_rag_evidence"},
    )
    workflow.add_edge("retrieve_rag_evidence", "formulate_hypotheses")
    workflow.add_edge("formulate_hypotheses", "select_probes")
    workflow.add_edge("select_probes", "generate_recovery_report")
    workflow.add_edge("generate_recovery_report", END)

    return workflow.compile()
