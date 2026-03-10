# Multi-Tenant Organization Manager

A secure, async, multi-tenant backend service built with FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, JWT authentication, RBAC, and an AI-powered chatbot for audit log analysis.

---

## Quick Start

### Prerequisites

- Docker and Docker Compose

### Run with Docker

```bash
cp .env.example .env          # edit JWT_SECRET_KEY and GEMINI_API_KEY
docker compose up --build
```

The API will be available at `http://localhost:8000`.
Interactive docs (OpenAPI UI): `http://localhost:8000/docs`

### Run Tests

```bash
pytest                  # full suite (unit + integration) with coverage
pytest tests/unit/      # unit tests only (no DB required)
```

---

## Architecture

### Pragmatic Onion Architecture

```
api/ → services/ → repositories/ → models/
```

Dependencies flow inward only. `core/` and `schemas/` are cross-cutting with no outward dependencies.

In strict Clean Architecture you would define repository interfaces (Protocols) in the domain layer and place concrete SQLAlchemy implementations in `infrastructure/`, using dependency injection to keep third-party dependencies out of inner layers entirely. You would also introduce domain entities, value objects, and contracts to fully isolate business logic from infrastructure concerns. This project deliberately skips all of that. There are no domain entities separate from SQLAlchemy models, no value objects, and no contracts — repositories depend on ORM models directly without ports or adapters sitting between them. The trade-off is pragmatic: fewer files, less indirection, and sufficient decoupling for the scope of ~6 features. The layer rule still holds; the only relaxation is that the repository abstraction is not formalized behind a Protocol.

For an example of one of my projects that does implement the full separation — domain entities, value objects, contracts, and dependency injection — see [github.com/melsayedx/zero_](https://github.com/melsayedx/zero_).

| Layer | Responsibility |
|---|---|
| `models/` | SQLAlchemy ORM entities — domain schema only, no business logic |
| `repositories/` | Typed async DB queries via SQLAlchemy sessions |
| `services/` | Business logic: validation, RBAC checks, audit log writes, orchestration |
| `api/` | Thin FastAPI route handlers — validate input, call services, return responses |
| `schemas/` | Pydantic DTOs for request validation and response serialization |
| `core/` | Pure utilities: JWT, password hashing, exceptions, `uuid7`, `utcnow` |
| `infrastructure/` | External integrations: async DB engine, LLM provider |

### Project Structure

```
app/
├── api/              # FastAPI routers
│   ├── auth.py
│   ├── organization.py
│   ├── item.py
│   ├── audit_log.py
│   └── dependencies.py   # get_current_user, require_membership, require_admin
├── core/
│   ├── exceptions.py     # HTTP exception classes
│   ├── security.py       # Argon2id hashing, JWT HS256
│   └── utils.py          # utcnow(), uuid7()
├── infrastructure/
│   ├── database.py       # Async engine + session factory
│   └── llm/
│       ├── protocol.py       # LLMProvider Protocol (structural subtyping)
│       └── gemini_provider.py
├── models/           # SQLAlchemy ORM models
├── repositories/     # Data access layer
├── schemas/          # Pydantic DTOs
└── services/         # Business logic layer
```

---

## API Endpoints

| Method | Path | Auth | Role | Description |
|---|---|---|---|---|
| POST | `/auth/register` | — | — | Register a new user |
| POST | `/auth/login` | — | — | Login, receive JWT |
| POST | `/organization` | JWT | any | Create org (creator becomes admin) |
| POST | `/organization/{id}/user` | JWT | admin | Invite user to org |
| GET | `/organizations/{id}/users` | JWT | admin | List org members (paginated) |
| GET | `/organizations/{id}/users/search` | JWT | admin | Full-text search members |
| POST | `/organizations/{id}/item` | JWT | member+ | Create item |
| GET | `/organizations/{id}/item` | JWT | member+ | List items (admin: all; member: own) |
| GET | `/organizations/{id}/audit-logs` | JWT | admin | List org audit log entries |
| POST | `/organizations/{id}/audit-logs/ask` | JWT | admin | Ask the AI chatbot about today's logs |
| GET | `/health` | — | — | Health check |

---

## Key Design Decisions

### PostgreSQL with asyncpg — async I/O

The application uses `asyncpg` as the PostgreSQL driver through SQLAlchemy's async engine. `asyncpg` supports asynchronous I/O natively, which means database queries do not block the event loop. Under concurrent load this translates to faster query throughput and better utilization of a single Python process, because the server can handle other requests while waiting on database I/O instead of sitting idle.

### Read/Write Session Separation

Two session factories are configured against the same async engine:

- **Write session** (`async_session`) — wraps every request in a transaction with explicit `commit()` / `rollback()`.
- **Read session** (`async_read_session`) — sets `autoflush=False` and skips the commit/rollback cycle entirely.

Read-only queries have no need for a flush or commit. Eliminating that overhead reduces round-trips to PostgreSQL for every read path. SQLAlchemy's async engine already maintains a connection pool by default (`pool_pre_ping=True` is enabled to validate stale connections), so sessions are cheap to acquire.

### UUID v7 for All Primary Keys

UUIDs are generated at the application layer using `uuid-utils` (Rust-backed). UUID v7 is time-ordered, which provides two concrete advantages over UUID v4:

1. **No index fragmentation.** UUID v4 values are random, so each insert lands at an arbitrary position in the B-tree index. This causes frequent page splits — the tree must merge and split nodes to accommodate out-of-order keys. UUID v7 values are monotonically increasing, so new rows always append to the end of the index, similar to an auto-incrementing integer.
2. **Natural chronological sorting.** Ordering by primary key implicitly orders by creation time, without requiring a separate `created_at` index for time-based queries.

**Trade-off:** The `pg_uuidv7` PostgreSQL extension would generate UUIDs at the database level, but requires a custom Docker image. Application-level generation is portable.

### Argon2id for Password Hashing

Argon2id is the winner of the Password Hashing Competition and is resistant to both GPU and side-channel attacks. `argon2-cffi` wraps the reference C implementation.

**Trade-off:** bcrypt is widely used but Argon2id has better memory-hardness properties.

### JWT HS256 — Stateless Authentication

Tokens are signed with a shared secret (HS256). The default expiration is 5 minutes. No refresh token rotation is implemented — users must re-authenticate after each token expires.

**Trade-off:** Production systems benefit from refresh token families and short-lived access tokens paired with a refresh flow. Without a refresh token the UX requires frequent re-login, which is acceptable for an assessment scope but not for a real product.

### RBAC — Two Roles, No Separate Table

Each user has exactly one role per organization: `admin` or `member`. The role is stored as a PostgreSQL enum directly on the `membership` row — there is no dedicated `roles` table.

- **Admins:** invite users, list/search members, view audit logs, use chatbot, see all items.
- **Members:** create items and list their own items only.

A separate roles/permissions table (many-to-many) enables fine-grained control but adds a JOIN on every authorization check. With only two roles that are unlikely to grow, an enum on the membership row avoids that JOIN entirely and keeps authorization queries simple.

### No GIN Index on Items JSONB

The `item_details` column uses PostgreSQL's JSONB type, but no GIN index is defined on it. A GIN index would be valuable if a search API existed over item details — it would allow indexed queries on arbitrary JSON keys and values. Since no such search endpoint exists, the index would consume write overhead and storage for zero benefit. If a search API is added later, a GIN index should be created alongside it.

### Synchronous Audit Log Writes

Audit logs are written in the same DB transaction as the triggering action. If the action rolls back, the log rolls back too — consistency is guaranteed.

**Trade-off:** An event-driven approach (domain events pushed to an async consumer) decouples writes and improves throughput, but adds infrastructure complexity beyond the scope of this project.

### Items — Heavy-Read Optimization Opportunity

Items are a read-heavy resource. A possible optimization is setting `synchronous_commit = off` at the session level for item writes. This allows PostgreSQL to acknowledge the commit immediately and flush the WAL (write-ahead log) to disk in the background. The transaction is durable against process crashes (PostgreSQL recovers from WAL on restart) but not against an OS-level crash during the brief window before the WAL flush completes. For non-critical item writes, that trade-off can be acceptable and noticeably reduces write latency.

This optimization is **not currently implemented**.

### FTS with PostgreSQL tsvector

User search uses a GIN-indexed `Computed` `tsvector` column over `full_name || ' ' || email`. `plainto_tsquery` provides natural-language query parsing.

**Trade-off:** A dedicated search engine (Elasticsearch, Typesense) handles typo tolerance and relevance ranking better, but adds infrastructure complexity.

### LLM Abstraction via Protocol

`GeminiProvider` satisfies `LLMProvider` via Python structural subtyping (`Protocol`) — no inheritance required. `ChatbotService` depends only on the protocol, making the provider swappable without changing any service code.

**Trade-off:** Multi-provider with fallback and circuit breaker would improve reliability. A single provider is sufficient here.

### UTC Everywhere

All timestamps are stored as `TIMESTAMP WITH TIME ZONE` in UTC. `utcnow()` in `app/core/utils.py` is the single source of truth.

This prevents a concrete problem: local time is broken for databases because of DST (Daylight Saving Time). Twice a year local time either jumps forward or repeats an hour. During the "fall back" hour, two events at different real moments can have identical local timestamps — sorting by `created_at` produces wrong results, and range queries like "everything in the last 24 hours" cross DST boundaries incorrectly. UTC has no DST. It never repeats and never skips.

Display conversion to local time is the client's responsibility.

### What Is Not Provided

- **No caching layer.** There is no Redis or in-memory cache. Every request hits PostgreSQL directly. For read-heavy endpoints (e.g., items listing), adding a cache with short TTL would reduce database load.
- **No rate limiting.** The API does not throttle requests. A production deployment should add rate limiting at the gateway or middleware level to prevent abuse.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | — | Async PostgreSQL URL (`postgresql+asyncpg://...`) |
| `JWT_SECRET_KEY` | Yes | — | HS256 signing key (min 32 chars in production) |
| `JWT_EXPIRATION_MINUTES` | No | `30` | Token TTL in minutes |
| `GEMINI_API_KEY` | Yes* | `""` | Google Gemini API key (*required for chatbot) |
| `POSTGRES_USER` | No | `orgmanager` | Used by docker-compose for DB init |
| `POSTGRES_PASSWORD` | No | `orgmanager` | Used by docker-compose for DB init |
| `POSTGRES_DB` | No | `orgmanager` | Used by docker-compose for DB init |

---

## Tests

Tests use `testcontainers` to spin up a real PostgreSQL container for integration tests — no mocking of the database layer.

```
tests/
├── unit/               # Pure unit tests — mock repositories, no DB
│   ├── test_auth_service.py
│   ├── test_organization_service.py
│   ├── test_item_service.py
│   ├── test_audit_service.py
│   └── test_security.py
└── integration/        # Real DB via testcontainers
    ├── test_auth_api.py
    ├── test_organization_api.py
    ├── test_item_api.py
    ├── test_audit_log_api.py
    └── test_rbac.py    # Cross-cutting RBAC + org isolation
```

**74 tests, 89% coverage.**
