# PreMan Hackathon API

A production-shaped FastAPI backend built to demonstrate PreMan's promise: developers ship API code, while autonomous testing continuously discovers endpoints, learns their schemas, and verifies them.

The repository intentionally exposes a compact but realistic product domain—token auth, profiles, projects, and tasks—through exactly **22 versioned API operations**. The resource APIs cover the common REST method surface: `GET`, `POST`, complete replacement with `PUT`, partial updates with `PATCH`, deletion with `DELETE`, and CORS preflight with `OPTIONS`. It includes deterministic seed data, interactive OpenAPI documentation, isolated contract tests, and a live agent matrix that exercises both success paths and edge cases.

## Demo access

| Item | Value |
| --- | --- |
| Public API | `https://xixoo2yundjxsbdwl3iw2eg5hi0ckwfu.lambda-url.us-east-1.on.aws` |
| Public Swagger UI | `https://xixoo2yundjxsbdwl3iw2eg5hi0ckwfu.lambda-url.us-east-1.on.aws/docs` |
| Public OpenAPI JSON | `https://xixoo2yundjxsbdwl3iw2eg5hi0ckwfu.lambda-url.us-east-1.on.aws/openapi.json` |
| Local API | `http://127.0.0.1:8000` |
| Swagger UI | `http://127.0.0.1:8000/docs` |
| OpenAPI JSON | `http://127.0.0.1:8000/openapi.json` |
| Demo email | `demo@preman.live` |
| Demo password | `PremanDemo123!` |

Run all 22 operations and the agent edge matrix against either local or public infrastructure with:

```bash
BASE_URL=https://xixoo2yundjxsbdwl3iw2eg5hi0ckwfu.lambda-url.us-east-1.on.aws \
  uv run python scripts/live_smoke.py
```

> The demo credentials are public by design and must never be reused for a production system.

## The 22-operation contract

Operational routes such as `/`, `/ready`, `/docs`, and `/openapi.json` are useful at runtime but do not count toward the 22 demo operations.

| # | Method | Path | Purpose | Auth |
| ---: | --- | --- | --- | --- |
| 1 | `GET` | `/health` | Liveness and version metadata | No |
| 2 | `POST` | `/api/v1/auth/register` | Create an account | No |
| 3 | `POST` | `/api/v1/auth/login` | Exchange credentials for access and refresh tokens | No |
| 4 | `POST` | `/api/v1/auth/refresh` | Rotate a refresh token | No |
| 5 | `POST` | `/api/v1/auth/logout` | Revoke a refresh token | No |
| 6 | `GET` | `/api/v1/auth/me` | Read the current profile | Bearer |
| 7 | `PATCH` | `/api/v1/auth/me` | Update the current profile | Bearer |
| 8 | `POST` | `/api/v1/auth/forgot-password` | Request a short-lived reset token | No |
| 9 | `POST` | `/api/v1/auth/reset-password` | Set a password using a reset token | No |
| 10 | `POST` | `/api/v1/auth/change-password` | Change the signed-in user's password | Bearer |
| 11 | `GET` | `/api/v1/projects` | List owned projects | Bearer |
| 12 | `POST` | `/api/v1/projects` | Create a project | Bearer |
| 13 | `GET` | `/api/v1/projects/{project_id}` | Read a project | Bearer |
| 14 | `PUT` | `/api/v1/projects/{project_id}` | Completely replace a project | Bearer |
| 15 | `PATCH` | `/api/v1/projects/{project_id}` | Partially update a project | Bearer |
| 16 | `DELETE` | `/api/v1/projects/{project_id}` | Delete a project and its tasks | Bearer |
| 17 | `GET` | `/api/v1/projects/{project_id}/tasks` | List a project's tasks | Bearer |
| 18 | `POST` | `/api/v1/projects/{project_id}/tasks` | Create a task | Bearer |
| 19 | `GET` | `/api/v1/tasks/{task_id}` | Read a task | Bearer |
| 20 | `PUT` | `/api/v1/tasks/{task_id}` | Completely replace a task | Bearer |
| 21 | `PATCH` | `/api/v1/tasks/{task_id}` | Partially update a task | Bearer |
| 22 | `DELETE` | `/api/v1/tasks/{task_id}` | Delete a task | Bearer |

## Run locally

Python 3.12 or newer is required.

```bash
cp .env.example .env
make install
make dev
```

The app initializes its selected storage backend and deterministic demo records on startup. A fresh checkout is immediately usable; no manual migrations or seed command is required for the hackathon path.

Run the complete test suite in another terminal:

```bash
make test
make contract
make smoke
```

## Quick demo

Log in and copy the access token:

```bash
curl -s http://127.0.0.1:8000/api/v1/auth/login \
  -H 'content-type: application/json' \
  -d '{"email":"demo@preman.live","password":"PremanDemo123!"}'
```

List the seeded projects:

```bash
curl -s http://127.0.0.1:8000/api/v1/projects \
  -H "authorization: Bearer $ACCESS_TOKEN"
```

Create a task, then let PreMan discover its schema and test it:

```bash
curl -s http://127.0.0.1:8000/api/v1/projects/$PROJECT_ID/tasks \
  -X POST \
  -H "authorization: Bearer $ACCESS_TOKEN" \
  -H 'content-type: application/json' \
  -d '{"title":"Ship the hackathon demo","description":"Exercise the full lifecycle","status":"todo","priority":"high"}'
```

## Authentication model

- Passwords are hashed; plaintext credentials are never stored.
- Access tokens are short-lived bearer JWTs.
- Refresh tokens rotate and become invalid after logout.
- Password-reset tokens are single-use and short-lived.
- Project and task reads and mutations are owner-scoped.
- The reset token is returned in development/demo responses so the full recovery flow can be tested without an email provider. Production integrations should deliver it out of band.

## Seed data

On first startup, the service creates the public demo account plus a representative project with tasks across common statuses and priorities. The live smoke runner creates its own uniquely named user, project, and task, then cleans up its project and task. It does not mutate the seeded demo records.

## Testing strategy

`tests/` verifies:

- the OpenAPI document contains the exact 22-operation contract;
- success and validation schemas for auth, profile, project, and task lifecycles;
- token rotation, revocation, password reset, and password changes;
- complete `PUT` replacement versus partial `PATCH` semantics;
- ownership boundaries, validation limits, filtering, pagination, replay, and missing-resource behavior;
- seeded demo data remains queryable; and
- health, readiness, and documentation routes stay operational.

`scripts/live_smoke.py` makes the same checks through real HTTP. Point it at the stable public URL before the presentation to catch DNS, TLS, platform, or database regressions that an in-process test cannot see.

GitHub Actions also checks the public service every 15 minutes without mutating demo
data. It verifies liveness, readiness, and that the deployed OpenAPI document still
contains exactly 22 product operations.

## PreMan demo flow

1. Connect this repository and the public base URL to PreMan.
2. Let PreMan ingest `/openapi.json` and discover all 22 operations.
3. Make an API change and push it—without writing a manual request collection.
4. Show PreMan updating schemas and exercising the affected endpoint.
5. Use the public demo credential when an authenticated call is required.

The backend is deliberately conventional. That is the point of the demo: PreMan should make a normal development workflow feel like testing is already taken care of.

## Deploy the stable AWS demo URL

The included CloudFormation stack runs FastAPI behind a public Lambda Function URL and stores state in encrypted, on-demand DynamoDB. It does not rely on a laptop staying awake and has no idle-service sleep timer.

Prerequisites are `uv`, `zip`, the AWS CLI, and an authenticated AWS account. The
deployment script builds an AWS Lambda-compatible ARM64 package without requiring
Docker. Then run:

```bash
export AWS_REGION=us-east-1
./infra/deploy.sh
```

The final line is the stable public base URL. CloudFormation retains both the
DynamoDB table and an AWS-managed signing secret across stack updates, so data and
issued tokens are not invalidated by a routine deploy. Application startup safely
upserts the deterministic seed records. Validate the deployed stack immediately:

```bash
BASE_URL="$(aws cloudformation describe-stacks \
  --region "$AWS_REGION" \
  --stack-name greptile-codex-backend-demo \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)" \
  python scripts/live_smoke.py
```
