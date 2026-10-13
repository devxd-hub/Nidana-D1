# NIDANA Tech Stack (Locked v2)

## 1. Locked Stack Principles

NIDANA enforces a simple, reliable, and strictly deterministic foundation for education, assessment, and recovery.
Deterministic Python/SQL logic governs scoring, persistent records, offline transactions, and mark accounting.
AI reasoning (LangGraph + Gemini) is strictly bounded and structured, operating as an advisory diagnosis engine.

## 2. Locked Component Matrix

| Layer | Technology | Responsibility | Non-Negotiable Guardrails |
|---|---|---|---|
| **Client UI** | Next.js / React / TypeScript PWA | Student assessment & remediation interface | No authoritative score calculation or recovery decisions in UI |
| **Client Offline Store** | IndexedDB via Dexie.js | Local pack storage, cached syllabus, offline attempt capture, retry sync queue | Client state is distinct from backend database; non-authoritative timestamps |
| **API Framework** | Python 3.12+, FastAPI | REST API endpoints, routing, dependency injection | Thin controllers, strict Pydantic schemas, server-side auth & ownership checks |
| **Relational Database** | SQLite (SQLAlchemy 2.x + Alembic) | Sole authoritative system of record for users, curriculum, questions, attempts, diagnosis runs, and study plans | Persistent disk storage (WAL mode, foreign keys ON, busy timeout); no ephemeral serverless disks |
| **Vector Index** | ChromaDB (local persistent) | Derived, rebuildable semantic retrieval index for approved learning chunks | Derived only; never the source of truth for user state; strict curriculum metadata filters |
| **Agent Orchestration** | LangGraph | Deterministic multi-step diagnosis & mark recovery state machine | Bounded graph; max 2 probes; structured output validation; no unbounded loops |
| **LLM Provider** | Google Gemini (via provider adapter) | Hypothesis formulation, probe selection, and recovery explanation | Provider logic isolated behind adapter; test doubles used for offline/ci |
| **HTTP Client** | HTTPX | External service communication | Strict timeouts, retries, error mapping |
| **Observability** | Structured JSON logging (optional Langfuse) | Diagnostic traces, audit events, timing | Safe trace summaries; never block startup or tests if Langfuse is absent |
| **Testing** | pytest, pytest-asyncio | Unit, integration, schema, migration tests | 100% test passing requirement before promotion |

## 3. Data Ownership & Storage Boundaries

### A. Authoritative Relational Store: SQLite
- **Authoritative for**:
  - User identity & local/mock authentication profiles.
  - Curricular taxonomy (Subjects, Chapters, Concepts, Prerequisites).
  - Question bank, multilingual variants (Odia / English), and hidden server-only answer keys/rubrics.
  - Assessment attempts, question responses, calculated marks, and interaction signals.
  - Diagnostic runs, hypotheses, probe outcomes, evidence links, and safe trace summaries.
  - Mark Recovery reports, generated study plans, and intervention tasks.
  - Content provenance records, ingestion manifests, and sync receipts.
- **Connection Configuration**:
  - Environment variable: `SQLITE_DATABASE_URL` (default: `sqlite:///./data/nidana.db`).
  - PRAGMAs: `foreign_keys = ON`, `journal_mode = WAL`, `busy_timeout = 5000`.

### B. Derived Vector Store: ChromaDB
- **Role**: Rebuildable semantic search index over approved curriculum content chunks.
- **Boundary**:
  - Rebuilt on demand from SQLite `content_chunks` and source manifests.
  - Never stores user attempts, student data, or active assessment state.
  - All queries enforce pre-filtering by Class Level, Subject, Chapter, and Language (`or` / `en`).

### C. Client Storage: Browser IndexedDB (Dexie)
- **Role**: Offline client cache for downloaded syllabus packs, offline question packs, and queued attempt events.
- **Boundary**:
  - Completely decoupled from backend SQLite.
  - Submits idempotent events to the `/api/v1/sync` endpoint upon network restoration.
  - Does not execute LLMs locally; relies on deterministic pre-packaged rules when offline.

## 4. Decommissioned Technologies (Historical Only)
- **Supabase / Hosted PostgreSQL / pgvector**: Decommissioned from the active stack. Existing migration files are retained for historical audit, but active runtime configuration exclusively targets SQLite and local ChromaDB.
