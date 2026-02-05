# Legartis – Contract Clause Tracker (Case Study)

## Goal
Build a small system that:
- Stores uploaded contracts (text/markdown)
- Detects presence of clause types using patterns (keywords and regex)
- Allows user confirmation/override (hybrid workflow)
- Shows an overview matrix (contracts × clause types)

---

## Ubiquitous language

- **Clause Type**: a clause category (e.g., “Termination”). Unique name.
- **Clause Pattern**: a rule for detecting a clause type (keyword or regex).
- **Contract**: an uploaded file; file is stored in storage, DB stores metadata.
- **System decision (`detected`)**: scanner output per clause in a contract.
- **Human decision (`confirmed`)**: nullable override per clause in a contract.
- **Effective**: final per-clause result:
  `effective = confirmed if confirmed != null else detected`

---

## Domain model

**Clause Library context**
- `ClauseType` (aggregate root)
  - owns many `ClausePattern`

**Contract Review context**
- `Contract` (aggregate root)
  - owns many `ContractClause` (matrix row per clause type)

Key invariant:
- one matrix row per `(contract_id, clause_type_id)`.

---

## Database model (normalized)

Tables:
- `clause_types` (unique clause names)
- `clause_patterns` (1:N patterns per clause type)
- `contracts` (file metadata + storage reference, not file content)
- `contract_clauses` (matrix: per contract + per clause decisions)

Why normalized:
- Clause library is reused across contracts
- Avoids duplication (i.e: avoids repeating clause type names per contract)
- Supports rescanning system output without touching human overrides
- Clause types and patterns can be updated independently
- `contract_clauses` is queryable and enforceable with a unique constraint:
  - `(contract_id, clause_type_id)` unique

Storage:
Contracts are stored in local file storage (not in the database).  
The database stores metadata + keys to the storage location.

Why:
- Large files don’t belong in Postgres rows
- Makes it easy to switch to object storage later (S3/MinIO/etc.)

---

## Backend structure (pragmatic layering)

- `app/model.py`: SQLAlchemy models + timestamp mixin
- `app/api/*`: Flask routes (use-cases)
- `app/storage_local.py`: local storage adapter (save/open)
- `alembic/`: migrations

---

This repository is implemented as a Docker Compose stack: Postgres + Flask API + SPA.

---

## Current Features (MVP so far)

### 1) Clause library (clause types + patterns)
- Create clause types with one or more patterns
- Each pattern is either a simple keyword match or regex

API:
- `POST /api/clause-types`
- `GET /api/clause-types`

### 2) Contract upload (text/markdown only)
- Upload `.txt`, `.md`, `.markdown`
- Guardrails:
  - extension whitelist
  - rejects binary files (null byte check)
  - requires UTF-8
  - optional max upload size

API:
- `POST /api/contracts`

### 3) Detection on upload + per-clause results
After upload:
- A `contracts` row is created
- The system scans the stored file text and computes a system decision per clause type
- Results are persisted into the matrix table `contract_clauses`

Contract processing status:
- `processing` → `processed`
- If scanning fails: `failed` + error message stored

### 4) Review workflow: system vs human decision (per clause)
For each uploaded contract and each clause type:
- `detected` (boolean) = system decision
- `confirmed` (nullable boolean) = human decision override
- **effective** final ruling:
  `effective = confirmed if confirmed != null else detected`

### 5) Contract APIs for SPA
- List contracts
- Get contract details with matrix rows
- Override human decision for a specific clause

APIs:
- `GET /api/contracts`
- `GET /api/contracts/<id>`
- `PATCH /api/contracts/<id>/clauses/<clause_type_id>` with `{ "confirmed": true|false|null }`

---

## How to run

### Prerequisites
- Docker + Docker Compose
- Ports:
  - Backend: `8000`
  - Postgres: `5432` (inside docker)

### Start the stack
From the repo root:

```bash
docker-compose up --build
```

Backend base URL:
- `http://localhost:8000`

### Apply migrations (if needed)
If schema is behind:

```bash
docker-compose exec backend uv run alembic -c alembic.ini upgrade head
```

### Stop / clean up

Stop containers:
```bash
docker-compose down
```

Remove volumes (destroys DB data):
```bash
docker-compose down -v
```

---

## API Endpoints

Base URL: `http://localhost:8000`

### Clause Types & Patterns
- **POST** `/api/clause-types` — create clause type (optionally with patterns)
- **GET** `/api/clause-types` — list clause types (including patterns)

> Full CRUD for clause types and patterns (update/delete) is planned next.

### Contracts
- **POST** `/api/contracts` — upload contract (runs detection + persists `contract_clauses`)
- **GET** `/api/contracts` — list contracts
- **GET** `/api/contracts/<contract_id>` — contract details + per-clause matrix (`detected`, `confirmed`, `effective`)
- **PATCH** `/api/contracts/<contract_id>/clauses/<clause_type_id>` — set/clear human override per clause  
  Body: `{ "confirmed": true | false | null }`

---

## How to test each endpoint (manual)

### 0) (Optional) Reset DB for deterministic tests
```bash
docker-compose exec db psql -U postgres -d legartis -c \
"TRUNCATE TABLE contract_clauses, clause_patterns, clause_types, contracts RESTART IDENTITY CASCADE;"
```

---

### 1) POST `/api/clause-types` — create clause type (with patterns)

Create:
```bash
curl -i -X POST http://localhost:8000/api/clause-types \
  -H 'Content-Type: application/json' \
  -d '{
    "name":"Termination",
    "patterns":[{"pattern":"terminate this agreement","is_regex":false}]
  }'
```

Expected:
- `201 Created`

Duplicate name:
```bash
curl -i -X POST http://localhost:8000/api/clause-types \
  -H 'Content-Type: application/json' \
  -d '{
    "name":"Termination",
    "patterns":[{"pattern":"another pattern","is_regex":false}]
  }'
```

Expected:
- `409 Conflict` and error like `clause_type_name_exists`

---

### 2) GET `/api/clause-types` — list clause types

```bash
curl -i http://localhost:8000/api/clause-types
```

Expected:
- `200 OK`
- JSON list with clause types and patterns

---

### 3) POST `/api/contracts` — upload contract (runs detection + persists matrix)

Prepare a matching file:
```bash
printf "We may terminate this agreement at any time.\n" > sample.md
```

Upload:
```bash
curl -i -X POST http://localhost:8000/api/contracts -F "file=@sample.md"
```

Expected:
- `201 Created`
- `processing_status = processed`

Verify DB matrix:
```bash
docker-compose exec db psql -U postgres -d legartis -c \
"select contract_id, clause_type_id, detected, confirmed from contract_clauses order by 1,2;"
```

Expected:
- row exists with `detected = true` for the matching clause type
- `confirmed = NULL`

Negative: unsupported extension
```bash
printf "hello\n" > bad.pdf
curl -i -X POST http://localhost:8000/api/contracts -F "file=@bad.pdf"
```

Expected:
- `415 Unsupported Media Type`

---

### 4) GET `/api/contracts` — list contracts

```bash
curl -i http://localhost:8000/api/contracts
```

Expected:
- `200 OK`

---

### 5) GET `/api/contracts/<contract_id>` — contract detail + matrix

```bash
curl -i http://localhost:8000/api/contracts/1
```

Expected:
- `200 OK`
- JSON includes `matrix` rows with `detected`, `confirmed`, `effective`

---

### 6) PATCH `/api/contracts/<contract_id>/clauses/<clause_type_id>` — override per clause

Set Yes:
```bash
curl -i -X PATCH http://localhost:8000/api/contracts/1/clauses/1 \
  -H 'Content-Type: application/json' \
  -d '{"confirmed": true}'
```

Set No:
```bash
curl -i -X PATCH http://localhost:8000/api/contracts/1/clauses/1 \
  -H 'Content-Type: application/json' \
  -d '{"confirmed": false}'
```

Clear override (Auto):
```bash
curl -i -X PATCH http://localhost:8000/api/contracts/1/clauses/1 \
  -H 'Content-Type: application/json' \
  -d '{"confirmed": null}'
```

Verify changes:
```bash
curl -s http://localhost:8000/api/contracts/1
```

---

## What’s next
- Evidence (“matched string/snippet”) per clause so UI can show why it matched
- Full CRUD for clause types and patterns (update/delete)
- Rescan contract using updated patterns without touching human overrides
- Complete SPA pages: clause library + contract matrix review
- Tests (smoke + unit tests)
