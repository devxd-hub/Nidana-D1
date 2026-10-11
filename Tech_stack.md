# NIDANA Tech Stack

## 1. Stack principles

Choose the simplest reliable implementation of the core loop. Prefer deterministic code for grading, persistence, offline behavior, synchronization, and mark accounting. Use AI where adaptive language reasoning and selection between diagnostic actions provide value. Every dependency must earn its place and have a fallback story.

## 2. Recommended baseline

| Layer | Technology | Responsibility | Guardrail |
|---|---|---|---|
| Web app | Next.js, React, TypeScript | Mobile-first student UI and routing | Typed API contracts; no business-critical grading in UI |
| Server-state client | TanStack Query | Fetching, cache invalidation, mutation coordination | Cache is not the source of truth |
| PWA | Service worker / PWA tooling | Installability and offline app shell | Test real offline launch and cache updates |
| Local database | IndexedDB via Dexie.js | Cached packs, local attempts, sync queue | Version schemas; preserve pending evidence |
| API | Python, FastAPI | HTTP endpoints and service composition | Thin routes, explicit schemas, auth on every private route |
| Validation | Pydantic | Request/response and AI-output validation | Reject malformed or unsupported data |
| ORM | SQLAlchemy | Database models and queries | Enforce ownership and transactions |
| Migrations | Alembic | Versioned schema changes | Never rely on manual production schema edits |
| Database/auth | Supabase Postgres (and Supabase Auth if chosen) | Source of truth for users, attempts, content, diagnoses | Use least privilege, RLS where appropriate, and server-only privileged keys |
| Vector search | pgvector | Semantic retrieval of approved educational chunks | Filter by metadata/approval before similarity search |
| Agent orchestration | LangGraph | Bounded, observable diagnosis-and-repair state machine | No unbounded autonomous loops |
| LLM | Google Gemini API | Hypothesis/probe/intervention reasoning and candidate generation | All output typed, grounded, validated; remote calls require connectivity |
| HTTP client | httpx | Calls to model and optional language services | Timeouts, bounded retries, error mapping |
| Observability | Langfuse + structured application logs | Trace graph nodes, tool calls, retrieval, latency, failures | Redact secrets and unnecessary learner data |
| Tests | pytest; frontend test tooling already present in repo | Unit, API, integration, offline, and regression tests | Critical core-loop and sync tests block release |
| Deployment | One static/PWA frontend host + one Python API host + managed Postgres | Deploy app and API | Pin versions, health checks, migrations, secret management |

## 3. Optional language services

IndicTrans2, Bhashini, or Sarvam may be evaluated for translation or speech. They are optional integrations, not required dependencies for the MVP. Do not assume their availability, quality, pricing, latency, or offline behavior without testing. Keep a human-reviewed Odia-English glossary and use it for high-value technical terms.

## 4. Separation of responsibilities

### Frontend
- Rendering, navigation, forms, accessibility, local caching, local event capture, and presentation.
- Never hold server-only API keys.
- Never decide official correctness or recovery state.
- Show accurate local-save and sync status.
- Treat cached data as versioned and potentially stale.

### Backend
- Authentication/authorization, API validation, database access, authoritative grading, report calculations, sync acceptance, and audit records.
- Own the domain state machine and enforce invariants.
- Validate all AI outputs before persistence or display.
- Use explicit transactions and idempotency keys for retried operations.

### AI / LangGraph
- Propose hypotheses, choose among available probes, interpret evidence, select interventions, and draft grounded explanations.
- Must use only tools explicitly registered for the current workflow.
- Cannot directly bypass service-layer permissions or mutate arbitrary database rows.
- Returns typed proposals; deterministic services validate and apply approved state changes.

### RAG
- Ingest only approved educational content.
- Keep source and version metadata.
- Retrieve a small, relevant set of chunks.
- Return source IDs alongside content.
- Never index private learner data into the shared content corpus.

### Offline layer
- Package approved content, variants, rules, and schema versions.
- Persist answer events locally before confirming local save.
- Sync with stable IDs and server deduplication.
- Clearly distinguish deterministic offline diagnosis from connected AI reasoning.

## 5. Data flow

```text
Student UI
  ├─ Online API request → FastAPI → service → Postgres
  └─ Offline action → Dexie/IndexedDB → local rules/pack → sync queue
                                                ↓ reconnect
                                       idempotent sync endpoint
                                                ↓
                                       server validation/reconcile

Wrong answer → diagnosis service → LangGraph
                              ├─ learner/attempt tools
                              ├─ approved RAG retrieval (pgvector)
                              ├─ Gemini reasoning (online only)
                              └─ typed proposal
                                      ↓
                            deterministic validation/service
                                      ↓
                        diagnosis + task + trace persisted
                                      ↓
                         report and recovery follow-up
```

## 6. Environment and secrets

Use an `.env.example` containing names only, such as:

```dotenv
APP_ENV=development
DATABASE_URL=
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
GEMINI_API_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=
```

Only include variables actually used by the implementation. The service-role key and all provider secret keys must remain server-side and must never use a `NEXT_PUBLIC_` prefix. Validate required settings at startup and fail clearly when a required production secret is absent. Never commit real `.env` files.

## 7. Versioning and compatibility

- Pin dependencies using the project's lockfile.
- Version API routes and sync payload schemas.
- Version offline packs and question/test content.
- Store question version IDs with attempts so answer keys remain reproducible.
- Make database changes through Alembic migrations.
- Treat generated content and RAG embeddings as versioned derived artifacts that can be rebuilt.
- Keep frontend/backend types synchronized from an OpenAPI-generated client or a tested shared contract where practical.

## 8. Practical MVP cuts

To protect delivery, start with:
1. Next.js + TypeScript + FastAPI + Postgres.
2. 20–30 reviewed questions and deterministic grading.
3. Dexie offline persistence and idempotent event sync.
4. One bounded LangGraph diagnosis path with two probes.
5. Small approved RAG corpus with citations.
6. One validated intervention and follow-up recovery check.
7. Structured traces and tests.

Defer voice, on-device models, broad multilingual support, large-scale ingestion, and teacher analytics until the end-to-end loop is reliable.

## 9. Architecture decision rule

Before adding a library/service, answer:
- Which requirement does it satisfy?
- Can the current stack satisfy that requirement?
- What is the offline/failure behavior?
- How will the feature be tested?
- Does it introduce cost, secrets, privacy risk, or operational complexity?
- Can the team explain it clearly during the hackathon demo?

If these questions have no concrete answer, defer the dependency.
