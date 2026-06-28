# EX3 Notes

## Service Orchestration Overview

This project runs as a four-service stack coordinated through Docker Compose:

- **api** provides the FastAPI backend and owns the application data model, authentication, and CRUD endpoints.
- **ui** provides the Streamlit dashboard used to manage courts, players, games, and the CSV export workflow.
- **redis** provides the shared cache and coordination layer used by the worker to track processed jobs.
- **worker** runs the background refresh job that polls the API, applies completion updates, and avoids duplicate processing.

The services are designed to work together as a single local deployment. The UI talks to the API over the compose network, the worker reads the same API and Redis services, and the API continues to use SQLite for persistence inside the container stack.

## Session 11 Security Baseline

Session 11 introduced the security baseline for the project:

- **JWT authentication** is used to represent logged-in users and protect privileged endpoints.
- **RBAC** is enforced through user roles, including an **admin** role for elevated actions.
- The seed script now creates a default admin account for local testing: **username:** `admin`, **password:** `adminpassword`.
- A standard user account is also seeded for normal login flows and non-admin testing.

This baseline makes it possible to validate login behavior, protected API routes, and admin-only functionality in the dashboard and backend.

### Key Rotation Steps

To rotate the JWT signing secret, generate a new key value such as:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Set the new value as the `SECRET_KEY` environment variable in the compose stack so the API and any related auth flows use the updated signing key.

When the secret key changes, all previously issued JWT tokens are invalidated immediately. Users will need to log in again to obtain fresh tokens.

## Session 09 Async Worker

Session 09 added the asynchronous worker that keeps game state in sync after scheduled matches finish.

- **httpx** is used to communicate with the API asynchronously.
- **tenacity** provides retry handling so transient network or startup failures do not immediately break the worker.
- **redis.asyncio** is used for idempotency tracking so a game is only processed once even if the worker runs repeatedly.
- The worker marks completed games through the API and stores a processed key in Redis to prevent duplicate updates.

This design allows the worker to be restarted safely while preserving reliable, repeatable background processing.

## Health Verification

After running `docker compose up`, confirm the stack is healthy by checking each service:

- Visit `http://localhost:8000/docs` to confirm the API is up and serving documentation.
- Visit `http://localhost:8501` to confirm the Streamlit UI is running.
- Run `docker compose exec redis redis-cli ping` and verify it returns `PONG` to confirm Redis is responding.
- Run `docker compose ps` and confirm the worker completed successfully by checking its exit code.

## Worker Trace Excerpt

an example for a real worker log excerpt here before submission:

```text
worker-1  | Processed 0 game(s).
```
