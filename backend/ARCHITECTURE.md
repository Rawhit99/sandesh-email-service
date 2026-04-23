# Backend Architecture Standards

This backend follows a layered structure to keep endpoints stable, code testable, and modules easy to debug.

## Layering Rules

- `routers/`:
  - HTTP transport only (route declaration, dependency injection, response typing).
  - No business logic, no direct data-shaping beyond trivial request parsing.
- `api/contracts/`:
  - External API request/response contracts for strict endpoint payloads.
  - Use these for public contract evolution without mixing with domain schema internals.
- `api/mappers/`:
  - Mapping between contract models and internal service input models.
  - Keep transformations deterministic and side-effect free.
- `services/`:
  - Business logic orchestration and validation rules.
  - DB interaction is allowed here; keep helper functions colocated or split by domain.
- `models/`:
  - `models.py`: ORM entities and DB session utilities.
  - `schemas.py`: shared internal API/service schemas (non-contract-specific).

## Endpoint Design Conventions

- Use `v1` paths for externally consumed APIs.
- Keep legacy compatibility routes only when required; favor strict contract routes.
- Route handlers should delegate to a single service entrypoint.

## Auth and Security

- JWT uses dedicated settings:
  - `JWT_SECRET_KEY`
  - `JWT_ALGORITHM`
  - `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- API keys and JWT secrets must never be coupled.
- Never commit live secrets in code or `.env` files.

## Error Handling

- Raise `HTTPException` for caller-facing validation and authorization errors.
- Let service functions express domain failures clearly (404, 409, 400).
- Avoid generic `except Exception` unless converting to stable API error boundaries.

## Code Size Guidance

- Prefer small service modules by domain (auth, notifications, templates, etc.).
- Extract repeated transformation logic into `api/mappers/` or focused helpers.
- Keep files cohesive; split once responsibilities diverge.
