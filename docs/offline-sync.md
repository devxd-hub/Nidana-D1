# NIDANA Offline Content Packs & Synchronization

## 1. Architectural Boundaries

- **Client-Side Offline Engine:**
  - Browser IndexedDB (managed via Dexie.js) stores downloaded curriculum packs, cached questions, and the local event sync queue.
  - Client timestamps and correctness calculations are strictly non-authoritative.
  - **No local LLM:** Deep AI reasoning (Gemini) requires connectivity. When offline, the client executes deterministic rule-based probes included in the preloaded content pack.
  - **ChromaDB Separation:** ChromaDB runs exclusively on the backend as a derived index. It does not run inside the browser.

- **Server-Side Authoritative Sync:**
  - SQLite maintains the system of record for all verified attempts, diagnostic runs, and `sync_receipts`.
  - The server evaluates all submitted responses authoritatively against trusted answer keys upon network reconnection.

---

## 2. Content Pack Lifecycle

1. **Manifest Inspection (`GET /api/v1/sync/packs`):**
   - Returns available packages with versions, content hashes, and item counts.
2. **Pack Download (`GET /api/v1/sync/packs/{pack_id}`):**
   - Returns a bounded `ContentPackBundle` containing syllabus chapters, concepts, approved `QuestionPublic` objects (with answer keys concealed), textbook learning chunks, and offline deterministic diagnostic rules.

---

## 3. Idempotent Batch Event Sync

### `POST /api/v1/sync/batch`

When network connectivity is restored, the client replays its queued events in a single batch.

#### Request Format:
```json
{
  "events": [
    {
      "client_event_id": "evt_client_uuid_101",
      "event_type": "ATTEMPT_SUBMIT",
      "payload_schema_version": "1.0.0",
      "client_timestamp": "2026-10-12T16:30:00Z",
      "device_id": "dev_samsung_a12",
      "payload": {
        "question_id": "q_c10_rxn_01",
        "selected_option": "A",
        "time_taken_seconds": 38,
        "learning_signals": {"confidence_rating": 4}
      }
    }
  ]
}
```

#### Server Processing & Conflict Policy:
1. **Idempotency Check:** The backend searches `sync_receipts` for `client_event_id`.
   - If found: returns status `"DUPLICATE"` alongside the previously recorded attempt details. No duplicate database records or scores are generated.
2. **Authoritative Grading:** The server computes correctness and marks against trusted database records.
3. **Receipt Emission:** Emits a permanent `SyncReceipt` in SQLite with status `"ACCEPTED"`, linking client event ID to server attempt ID.

#### Response Format:
```json
{
  "batch_id": "batch_98a7b6c5d4e3",
  "accepted_count": 1,
  "duplicate_count": 0,
  "rejected_count": 0,
  "event_results": [
    {
      "client_event_id": "evt_client_uuid_101",
      "status": "ACCEPTED",
      "server_receipt_id": "rcpt_78e6d5c4b3a2",
      "message": "Attempt processed and saved authoritatively.",
      "processed_data": {
        "attempt_id": "att_sync_evt_client_uuid_101",
        "is_correct": true,
        "marks_obtained": 4.0
      }
    }
  ]
}
```
