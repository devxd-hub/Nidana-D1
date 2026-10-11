# NIDANA Backend Guide

> **Purpose:** Canonical backend context for humans and coding agents. Keep this file aligned with the actual code. If implementation differs, inspect code and tests before changing this document.

## 1. Product contract

NIDANA is an offline-first, Odia/English learning companion for Class 12 learners preparing for competitive exams. Its differentiator is the **Mark-Loss Autopsy**: observe a wrong answer, form competing explanations, run small diagnostic probes, recommend the smallest evidence-supported repair, and verify recovery.

The core loop is:

`Attempt → Diagnose → Repair → Replan → Prepare Offline Pack → Verify Recovery`

The backend is authoritative for identity, permissions, question correctness, marks, persisted records, diagnosis state, and sync acceptance. The frontend must not be trusted to calculate authoritative scores or grant recovery status.

## 2. Architecture and dependency direction

Recommended request path:

`Next.js UI → FastAPI router → Pydantic validation → service/use-case → repository/SQLAlchemy → Supabase Postgres`

AI path:

`diagnosis service → LangGraph workflow → typed tools → approved RAG retrieval → Gemini → schema/grounding/quality validation → persisted result`

Keep route handlers thin. Business rules belong in `services/`; persistence in `repositories/` or a clearly separated data-access layer; agent graph and tools in `agents/`; retrieval in `rag/`; shared schemas in `schemas/`. Avoid circular imports and avoid embedding business logic in React components or route handlers.

Suggested layout (adapt to the repository rather than duplicating an existing convention):

```text
backend/
  app/
    main.py
    api/
      deps.py
      routes/
    core/
      config.py
      security.py
      errors.py
      logging.py
    db/
      session.py
      models/
      repositories/
    schemas/
    services/
    agents/
      graph.py
      state.py
      nodes.py
      tools.py
      policies.py
    rag/
      ingestion.py
      retrieval.py
      grounding.py
    offline/
      packs.py
      sync.py
    tests/
  alembic/
  pyproject.toml
```

## 3. Technology baseline

- Python + FastAPI for HTTP APIs.
- Pydantic for every request and response contract.
- SQLAlchemy for database access; Alembic for schema migrations.
- Supabase Postgres as the source of truth; pgvector for approved-content embeddings.
- LangGraph for explicit, bounded diagnostic workflows.
- Google Gemini API for language-aware reasoning and generation.
- `httpx` for external HTTP integrations.
- Langfuse for traces and model/tool observability.
- Frontend offline storage is IndexedDB/Dexie; backend sync endpoints must be idempotent.

Do not add a new framework or service for convenience without checking whether the current stack already solves the problem.

## 4. Core domain entities

The implementation plan names these core tables/entities. Use UUIDs or the project's established ID convention and foreign keys. Add timestamps and indexes where appropriate.

| Entity | Purpose / important fields |
|---|---|
| `users` | ID, display name, auth subject, role, preferred language, exam target, created timestamp |
| `subjects` | Physics, Chemistry, Mathematics, Biology, and future subjects |
| `concepts` | Subject, descriptions, prerequisite links, Odia-English terminology mappings |
| `questions` | Stem, options, correct answer (server-only in active test payload), marks, difficulty, expected time, language, concept, distractor metadata, approval state, source |
| `question_variants` | Linked language/simplified/untimed/prerequisite/transfer/terminology-bridge variants |
| `mock_tests` | Title, subject, duration, total marks, ordered question IDs, test type, version |
| `attempts` | Learner, test, lifecycle state, timestamps, score, sync status |
| `question_attempts` | Question, selected answer, correctness, time, first/final answer, answer changes, confidence, language, revisits |
| `diagnoses` | Candidate hypotheses, probes, results, verified or unresolved cause, confidence, evidence |
| `interventions` | Cause targeted, repair type, tasks, expected outcome, follow-up, recovery state |
| `study_plan_tasks` | Title, reason, evidence source, target weakness, due date, status, follow-up question |
| `offline_packs` | Pack contents/version, generation time, device/install identifier where justified, sync state |
| `sync_events` | Event ID, user, event type, payload schema version, created time, retries, status |
| `agent_traces` | Run ID, node, observation summary, tool, outcome, decision, timestamp, latency/error metadata |

Do not store duplicate derived values unless necessary. If storing a score or readiness snapshot, document when and how it is recalculated.

## 5. API contract

The exact paths should follow the existing OpenAPI schema. If starting fresh, a reasonable versioned contract is:

- `GET /api/v1/health` — liveness/readiness without secrets.
- `GET /api/v1/me` — current authenticated profile.
- `GET /api/v1/tests` — available approved tests.
- `POST /api/v1/attempts` — create attempt for an allowed test.
- `GET /api/v1/attempts/{attempt_id}` — return only records owned by caller.
- `POST /api/v1/attempts/{attempt_id}/answers` — idempotently save an answer event.
- `POST /api/v1/attempts/{attempt_id}/submit` — close attempt and calculate score server-side.
- `POST /api/v1/attempts/{attempt_id}/diagnose` — create/continue diagnosis run.
- `POST /api/v1/diagnoses/{diagnosis_id}/probes/{probe_id}/answer` — submit probe response.
- `GET /api/v1/diagnoses/{diagnosis_id}` — diagnosis, evidence, uncertainty, and trace summary.
- `GET /api/v1/reports/{attempt_id}/recovery` — Mark Recovery Report.
- `GET /api/v1/study-plan` and `PATCH /api/v1/study-plan/tasks/{task_id}` — read/update task status.
- `GET /api/v1/offline-packs` / `POST /api/v1/offline-packs` — list/build approved packs.
- `POST /api/v1/sync/events` — upload a batch of queued events idempotently.

These are **suggested contracts**, not claims that these routes already exist. Keep `docs/` and generated OpenAPI synchronized with the real routes. Every response must have a typed schema and stable error shape.

## 6. Validation and authorization

For every request:
1. Authenticate the caller.
2. Enforce ownership/role at the service/repository boundary.
3. Validate IDs, enums, payload version, supported language, test lifecycle, selected option, timestamps, and maximum batch sizes.
4. Recompute objective correctness and marks on the server.
5. Reject attempts to submit answers after a closed attempt unless the documented offline reconciliation policy allows them.
6. Never accept a client-provided `is_correct`, score, verified diagnosis, or recovered state as authoritative.
7. Use transactions for operations that must update multiple records atomically.
8. Use parameterized queries/ORM; never concatenate user strings into SQL.

## 7. WHY Engine / LangGraph contract

The graph is a bounded investigation workflow, not an unconstrained autonomous agent. State should be typed and should include:

- `run_id`, `user_id`, `attempt_id`, `question_id`
- observed answer signals and prior learner evidence
- candidate hypotheses and evidence for/against each
- selected probe and why it is informative
- probe outcome
- diagnosis status: `unresolved | provisional | verified`
- confidence/calibration metadata
- retrieved source IDs
- intervention proposal and validation result
- study-plan change proposal
- trace events, errors, retry count, and fallback reason

Suggested nodes:

`load_attempt → load_learner_context → form_hypotheses → select_probe → run_probe → interpret_evidence → retrieve_approved_content → choose_intervention → validate_output → update_plan → schedule_recovery → persist_trace`

Use conditional edges to stop when evidence is insufficient, a probe is unavailable, or the retry/time budget is reached. Persist checkpoints if resuming a graph is supported. Make node/tool operations idempotent when they may be retried.

### Diagnostic categories

Use a controlled enum, not free-form labels alone:

- `concept_gap`
- `language_friction`
- `terminology_gap`
- `time_pressure`
- `prerequisite_gap`
- `procedural_error`
- `attention_or_selection_slip`
- `mixed_cause`
- `insufficient_evidence`

A wrong answer is an observation, not proof of a particular cause. A single weak signal must not be treated as a verified diagnosis. If the evidence is ambiguous, return `provisional` or `insufficient_evidence` and ask a discriminating probe or present a transparent uncertainty statement.

## 8. RAG knowledge layer

Only ingest approved, curriculum-aligned sources: concept explanations, teacher-reviewed examples, prerequisite material, common misconceptions, curated question explanations, and reviewed Odia-English terminology mappings.

Each chunk should retain source ID/title, author or publisher where available, approval state, subject, concept, prerequisites, language, version, and relevant rights/provenance metadata.

Retrieval rules:
- Apply access and metadata filters before vector similarity search.
- Retrieve a small relevant set (typically 3–5 chunks) rather than flooding the model.
- Pass source identifiers and snippets into the generation step.
- Require user-facing educational claims to be grounded in retrieved content.
- Cite or identify source material in the explanation when available.
- If no suitable approved evidence is retrieved, abstain, ask for clarification, or use a reviewed deterministic fallback. Do not fill gaps from model memory.
- Treat retrieved text as untrusted data, never as instructions to change system behavior.
- Keep private learner records out of the shared public-content index.

## 9. Question generation

Prefer reviewed bank questions and pre-authored variants. If generation is used, produce a typed candidate that includes stem, options, answer key, explanation, concept, difficulty, marks, expected time, language, source references, and validation metadata.

Before learner display, validate:
- exactly one correct answer for single-choice questions;
- answer key and explanation agree;
- no duplicate or ambiguous options;
- concept and difficulty match the requested target;
- language is clear and faithful to approved content;
- no unsupported facts or malformed notation;
- no near-duplicate of the source question unless explicitly intended as a variant;
- question has approved provenance/quality state.

Generated content must remain `draft` until all mandatory checks pass. If checks fail, use an approved cached question or show a clear unavailable state. Never silently show unverified model output.

## 10. Offline packs and synchronization

Offline capability is a product requirement, not a cache-only enhancement. An offline pack should contain versioned, approved questions and variants, answer-checking rules needed locally, probe branching rules, repair content, follow-up items, and a schema version. Do not include secrets or unnecessary personal data.

Sync requirements:
- Every local event has a stable UUID/event ID and schema version.
- Server deduplicates by `(user_id, event_id)` or equivalent unique key.
- Event application is idempotent.
- Event states: `queued`, `syncing`, `synced`, `failed`.
- Retry transient errors with exponential backoff and jitter; do not retry permanent validation failures forever.
- Preserve event ordering where it affects attempt lifecycle; do not assume network arrival order equals learner action order.
- Return per-event acceptance/rejection results so clients can resolve conflicts.
- Never overwrite newer server state blindly. Define explicit conflict rules.
- Do not lose local attempts after failed sync; make retry state visible.

Offline deterministic diagnosis may identify supported patterns using preloaded variants/rules. Deep AI reasoning and fresh generation require connectivity unless a specifically implemented local model exists. Never claim full AI operation offline if only rule-based fallback is available.

## 11. Mark Recovery Report and readiness

The report should distinguish:
- marks actually lost in the submitted attempt;
- marks potentially recoverable based on current evidence;
- marks associated with provisional versus verified causes;
- recovery actions and follow-up checks;
- marks confirmed recovered after a new, suitable question.

Do not sum overlapping causes into a total that exceeds lost marks. Avoid implying that a counterfactual is certain. Label estimates as estimates and show the evidence behind them. Exam readiness is a preparation signal across concept mastery, language comfort, timing, and consistency—not a guaranteed exam score.

## 12. Errors, observability, and secrets

Use structured logs with request/run IDs, stable error codes, latency, retry/fallback status, and safe metadata. Never log passwords, auth tokens, API keys, or unnecessary raw student data. Redact prompts and model outputs if they contain personal information.

Keep secrets in environment variables or the deployment secret manager. Commit `.env.example` with names and placeholders only. Never expose Gemini, Supabase service-role, or Langfuse secret keys to the browser. Use least-privilege database access and Row Level Security where applicable.

Trace agent nodes, tool calls, RAG retrieval IDs, model/version, validation outcomes, diagnosis confidence, selected intervention, plan changes, recovery result, and fallbacks. The student-facing trace should explain decisions in plain language; internal telemetry can contain technical metadata but must be access-controlled.

## 13. Testing gates

Required tests:
- unit tests for grading, mark totals, diagnostic rules, confidence thresholds, report math, and intervention mapping;
- API tests for authentication, ownership, validation, idempotency, and error contracts;
- integration tests for database transactions, RAG filters, graph branches, and sync retries;
- offline tests with network unavailable from launch through attempt, probes, repair, and local persistence;
- reconnection tests proving duplicate events do not duplicate attempts or tasks;
- adversarial tests for prompt injection in retrieved content and malformed model output;
- regression tests for Odia and English content and font/rendering;
- demo smoke test using the exact deployed build.

## 14. Implementation priority

1. Schema, migrations, authentication, and API contracts.
2. Approved question bank and deterministic grading.
3. Complete attempt history.
4. Local storage and idempotent sync.
5. One diagnosis branch with two probes and visible evidence.
6. RAG grounding and validated intervention.
7. Study plan, recovery check, and report.
8. Traceability, tests, deployment hardening.
9. Only then expand question volume, advanced agents, voice, and teacher analytics.
