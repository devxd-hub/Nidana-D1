# NIDANA Backend State Audit (Prompt 1)

**Date**: 2026-10-12  
**Repository Root**: `E:\PROJECTS\Nirmit-D1\Nidana-D1`  
**Execution Baseline**: 22 passed tests (`pytest -v` run via `backend\.venv\Scripts\pytest.exe`)

---

## 1. Repository Structure & Map

```text
Nidana-D1/
├── docs/
│   ├── TECH_STACK.md                 # Locked v2 stack specification
│   └── backend-state-audit.md        # This audit document
├── backend/
│   ├── alembic/                      # Alembic migrations & config
│   │   ├── env.py
│   │   └── versions/
│   │       └── 0001_initial_schema.py # 10 initial tables (users, subjects, chapters, etc.)
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py               # DI: get_db, get_current_user
│   │   │   └── v1/                   # REST endpoints (health, users, subjects, attempts, etc.)
│   │   ├── core/
│   │   │   ├── config.py             # Settings (pydantic-settings)
│   │   │   ├── constants.py          # Enums (ClassLevel, AttemptLifecycle, etc.)
│   │   │   ├── errors.py             # Standard API exception hierarchy & handlers
│   │   │   ├── logging.py            # Structured JSON logger with token masking
│   │   │   └── security.py           # JWT decoding & ownership enforcement
│   │   ├── db/
│   │   │   ├── base.py               # DeclarativeBase with TimestampMixin
│   │   │   └── session.py            # Engine & sessionmaker
│   │   ├── models/                   # 10 domain entities (User, Question, Attempt, etc.)
│   │   ├── repositories/             # CRUD repositories for all entities
│   │   ├── schemas/                  # Pydantic schemas for request/response
│   │   ├── services/                 # Business logic (grading, content, attempts)
│   │   └── main.py                   # FastAPI application factory
│   ├── tests/                        # 10 test files (22 tests)
│   ├── .env.example                  # Environment template
│   ├── .gitignore                    # Backend git exclusions
│   ├── alembic.ini                   # Alembic configuration
│   ├── pyproject.toml                # Project packaging & pytest config
│   └── requirements.txt              # Pinned dependencies
├── .gitignore                        # Root git exclusions (ignores prompt files & local data)
└── changelog_backend.md              # Authoritative changelog
```

---

## 2. Audit of Components & Current State

| Component / Subsystem | Status | Evidence / Notes |
|---|---|---|
| **App Startup & Health** | **Complete** | `/api/v1/health` verifies database readiness without leaking sensitive paths or credentials. |
| **Settings Validation** | **Partial** | Uses Pydantic Settings; requires modernization to make `SQLITE_DATABASE_URL` first-class and eliminate mandatory Supabase variables in dev. |
| **Relational DB & Migrations** | **Complete (MVP)** | 10 models defined in SQLAlchemy 2.0; Alembic migration `0001_initial_schema.py` functional. Needs SQLite-specific PRAGMAs (WAL, foreign keys). |
| **Authentication & Ownership** | **Complete (Mock/JWT)** | Validates JWTs, resolves user identity, and strictly enforces resource ownership (`enforce_ownership()`). |
| **Curriculum Taxonomy** | **Complete** | `subjects`, `chapters`, `concepts` with ClassLevel constrained to 9, 10, 12. |
| **Question Bank & Concealment** | **Complete** | `QuestionPublic` conceals `correct_answer` and explanation during active testing. |
| **Mini-Mock & Authoritative Grading** | **Partial** | Server-side objective evaluation (+4 / -1) and attempt idempotency implemented; needs 5-question mini-mock orchestration endpoints and demo seed data. |
| **RAG / ChromaDB** | **Missing** | ContentChunk model exists in SQLite; ChromaDB wrapper, chunk indexing, embedding adapter, and provenance retrieval need implementation (Prompt 4). |
| **Offline Content Packs & Sync** | **Missing** | Contracts for pack generation, manifest delivery, and idempotent batch event sync need implementation (Prompt 5). |
| **LangGraph WHY Engine** | **Missing** | StudyPlan and StudyPlanTask models exist; LangGraph diagnostic graph, Gemini adapter, and recovery verification need implementation (Prompt 6). |

---

## 3. Active Old-Stack References

1. **`backend/app/core/config.py`**:
   - `DATABASE_URL` contains PostgreSQL fallbacks.
   - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET` are declared.
2. **`backend/app/core/security.py`**:
   - Mentions `decode_supabase_jwt`. It functions cleanly as a standard HS256/JWT validator, but can decouple from Supabase naming.
3. **`backend/alembic/env.py`**:
   - Compatible with SQLite and PostgreSQL; will configure explicitly for SQLite.
4. **`backend/requirements.txt`**:
   - Contains `psycopg2-binary>=2.9.9` (can be marked optional/historical).

---

## 4. Data Loss & Migration Risks

- **SQLite Ephemeral Filesystems**: SQLite files placed in serverless/container temporary directories risk loss on container restart. Configuration must enforce `./data/nidana.db` with persistent volume mount warnings.
- **Foreign Keys in SQLite**: SQLite defaults to `PRAGMA foreign_keys = OFF`. The engine must explicitly execute `PRAGMA foreign_keys = ON` on connection connect.
- **Concurrency / Busy Timeouts**: In SQLite, concurrent writes block. Must configure WAL mode (`PRAGMA journal_mode = WAL`) and a 5000ms `busy_timeout`.
- **Existing Schema Preservation**: Historical Alembic migrations must be preserved; new models will use incremental migrations.

---

## 5. Ordered Implementation Plan

1. **Prompt 1 (Current)**: Baseline verification, documentation of tech stack and audit, initial safe settings adjustments.
2. **Prompt 2**: SQLite reliability hardening (WAL, foreign keys, busy timeout, decouple runtime from Postgres/Supabase, new models for diagnosis/provenance).
3. **Prompt 3**: 5-question mini-mock engine, demo question seeding (Class 9/10/12), test suite expansion.
4. **Prompt 4**: ChromaDB persistent store, embedding adapter, curriculum-scoped retrieval, provenance validation.
5. **Prompt 5**: Offline packs, idempotent event sync, deterministic offline diagnosis rules.
6. **Prompt 6**: LangGraph WHY Engine, Gemini provider adapter, mark recovery flow, end-to-end testing.

---

## 6. Verification & Test Evidence

- **Command**: `backend\.venv\Scripts\pytest.exe -v`
- **Result**: `22 passed, 4 warnings in 14.99s`
- **Tests verified**: Startup, health, config validation, error structures, schema constraints, auth tokens, migrations, and attempt grading.
