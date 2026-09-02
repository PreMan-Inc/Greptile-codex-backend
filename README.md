# PreMan Test Backend

A production-shaped FastAPI backend for testing API discovery, schema learning, and
automated request generation. It now exposes two compatible API surfaces:

- an unauthenticated, JSON-backed mock catalog with exactly **30 CRUD operations** for
  customers, products, orders, support tickets, and product reviews; and
- the original authenticated **22-operation legacy API** for profiles, projects, tasks,
  and token lifecycle testing.

One operation means one unique HTTP method plus path template. Query-string variants do
not add operations. Operational and support routes such as `/`, `/ready`, `/docs`,
`/mock-docs`, `/openapi.json`, `/mock-openapi.json`, `/test-ui`, and the hidden mock reset
action are not part of either operation count.

## Demo access

The stable public base URL is:

`https://xixoo2yundjxsbdwl3iw2eg5hi0ckwfu.lambda-url.us-east-1.on.aws`

| Item | Public URL | Local URL |
| --- | --- | --- |
| API root | [Public API](https://xixoo2yundjxsbdwl3iw2eg5hi0ckwfu.lambda-url.us-east-1.on.aws/) | `http://127.0.0.1:8000/` |
| Mock test UI | [Open test UI](https://xixoo2yundjxsbdwl3iw2eg5hi0ckwfu.lambda-url.us-east-1.on.aws/test-ui) | `http://127.0.0.1:8000/test-ui` |
| Mock-only Swagger UI | [Open mock Swagger](https://xixoo2yundjxsbdwl3iw2eg5hi0ckwfu.lambda-url.us-east-1.on.aws/mock-docs) | `http://127.0.0.1:8000/mock-docs` |
| Mock-only OpenAPI JSON | [View mock specification](https://xixoo2yundjxsbdwl3iw2eg5hi0ckwfu.lambda-url.us-east-1.on.aws/mock-openapi.json) | `http://127.0.0.1:8000/mock-openapi.json` |
| Test schemas + fixtures | [View reusable JSON schemas](https://xixoo2yundjxsbdwl3iw2eg5hi0ckwfu.lambda-url.us-east-1.on.aws/mock-schemas.json) | `http://127.0.0.1:8000/mock-schemas.json` |
| Combined Swagger UI | [Open combined Swagger](https://xixoo2yundjxsbdwl3iw2eg5hi0ckwfu.lambda-url.us-east-1.on.aws/docs) | `http://127.0.0.1:8000/docs` |
| Combined OpenAPI JSON | [View combined specification](https://xixoo2yundjxsbdwl3iw2eg5hi0ckwfu.lambda-url.us-east-1.on.aws/openapi.json) | `http://127.0.0.1:8000/openapi.json` |
| Legacy demo email | `demo@preman.live` | `demo@preman.live` |
| Legacy demo password | `PremanDemo123!` | `PremanDemo123!` |

The test UI is the fastest way to exercise the mock service. It groups operations by
resource, provides editable request examples, sends calls to the current host, displays
formatted responses, and can run complete CRUD lifecycles. Swagger at `/docs` exposes
both the legacy and mock operations. `/mock-docs` and `/mock-openapi.json` expose only
the exact 30-operation mock contract.

> The mock service and legacy credentials are intentionally public. Never submit real
> personal, customer, payment, credential, or other sensitive data.

## The 30-operation mock contract

All mock operations are under `/api/v1/mock`, require no authentication, and use JSON.
Every resource has the same complete REST surface: list, create, retrieve, full `PUT`
replacement, partial `PATCH` update, and delete.

Customers are partitioned by region, so listing them requires a `region` of `emea`,
`apac` or `amer`. There is no cross-region view: omitting it is a `422` rather than a
silent read of everything. Records written before the partition existed carry no region
and are returned from every one of them, so the seed is visible whichever you ask for.
The other four collections are not partitioned.

| # | Method | Path | Label |
| ---: | --- | --- | --- |
| 1 | `GET` | `/api/v1/mock/customers` | List customers (requires `region`) |
| 2 | `POST` | `/api/v1/mock/customers` | Create customer |
| 3 | `GET` | `/api/v1/mock/customers/{item_id}` | Get customer |
| 4 | `PUT` | `/api/v1/mock/customers/{item_id}` | Replace customer |
| 5 | `PATCH` | `/api/v1/mock/customers/{item_id}` | Update customer |
| 6 | `DELETE` | `/api/v1/mock/customers/{item_id}` | Delete customer |
| 7 | `GET` | `/api/v1/mock/products` | List products |
| 8 | `POST` | `/api/v1/mock/products` | Create product |
| 9 | `GET` | `/api/v1/mock/products/{item_id}` | Get product |
| 10 | `PUT` | `/api/v1/mock/products/{item_id}` | Replace product |
| 11 | `PATCH` | `/api/v1/mock/products/{item_id}` | Update product |
| 12 | `DELETE` | `/api/v1/mock/products/{item_id}` | Delete product |
| 13 | `GET` | `/api/v1/mock/orders` | List orders |
| 14 | `POST` | `/api/v1/mock/orders` | Create order |
| 15 | `GET` | `/api/v1/mock/orders/{item_id}` | Get order |
| 16 | `PUT` | `/api/v1/mock/orders/{item_id}` | Replace order |
| 17 | `PATCH` | `/api/v1/mock/orders/{item_id}` | Update order |
| 18 | `DELETE` | `/api/v1/mock/orders/{item_id}` | Delete order |
| 19 | `GET` | `/api/v1/mock/tickets` | List support tickets |
| 20 | `POST` | `/api/v1/mock/tickets` | Create support ticket |
| 21 | `GET` | `/api/v1/mock/tickets/{item_id}` | Get support ticket |
| 22 | `PUT` | `/api/v1/mock/tickets/{item_id}` | Replace support ticket |
| 23 | `PATCH` | `/api/v1/mock/tickets/{item_id}` | Update support ticket |
| 24 | `DELETE` | `/api/v1/mock/tickets/{item_id}` | Delete support ticket |
| 25 | `GET` | `/api/v1/mock/reviews` | List product reviews |
| 26 | `POST` | `/api/v1/mock/reviews` | Create product review |
| 27 | `GET` | `/api/v1/mock/reviews/{item_id}` | Get product review |
| 28 | `PUT` | `/api/v1/mock/reviews/{item_id}` | Replace product review |
| 29 | `PATCH` | `/api/v1/mock/reviews/{item_id}` | Update product review |
| 30 | `DELETE` | `/api/v1/mock/reviews/{item_id}` | Delete product review |

### Resource shapes

The server generates `id`, `created_at`, and `updated_at` for every record. Request bodies
reject unknown fields. A `PUT` body must include the complete writable representation;
`PATCH` accepts a non-empty subset and leaves omitted fields unchanged.

| Resource | Writable fields |
| --- | --- |
| Customer | `name`, unique `email`, `phone`, `company`, `status` (`active`, `inactive`, or `lead`) |
| Product | unique `sku`, `name`, `description`, `category`, `price_cents`, `stock_quantity`, `active` |
| Order | `customer_id`, non-empty `items` (`product_id` and `quantity`), `status`, `shipping_address`, `notes`; the server computes `total_cents` |
| Support ticket | `customer_id`, `subject`, `description`, `status`, `priority`, `assignee` |
| Product review | `customer_id`, `product_id`, `rating` from 1–5, `title`, `body` |

Collection responses use a consistent pagination envelope:

```json
{
  "items": [],
  "total": 0,
  "limit": 20,
  "offset": 0
}
```

Successful creates return `201 Created` and a `Location` header. Reads, replacements,
and updates return `200 OK`; successful deletes return `204 No Content`. Missing records
return `404`, duplicate unique values return `409`, and invalid bodies, query values, or
resource references return `422` in the standard error envelope. Deleting a customer or
product that is still referenced also returns `409`; delete its dependent orders, tickets,
or reviews first. The shared service caps each collection at 250 records and the complete
JSON document at 2 MiB, returning `409` when either safety limit is reached.

### Quick mock request

No access token is needed:

```bash
curl -s 'https://xixoo2yundjxsbdwl3iw2eg5hi0ckwfu.lambda-url.us-east-1.on.aws/api/v1/mock/customers?region=emea'
```

Create a disposable customer with a unique email:

```bash
curl -s \
  -X POST \
  -H 'content-type: application/json' \
  -d '{"name":"API Tester","email":"api.tester.001@example.com","phone":"+1-555-0100","company":"Example Labs","status":"active"}' \
  https://xixoo2yundjxsbdwl3iw2eg5hi0ckwfu.lambda-url.us-east-1.on.aws/api/v1/mock/customers
```

The public dataset is shared. The test UI and live smoke runner use disposable records
and clean them up. A support-only `POST /api/v1/mock/reset` action restores the committed
seed for deterministic demos; it is intentionally omitted from the 30-operation mock
OpenAPI document and resets the shared mock dataset for every caller.

## JSON data and persistence

The deterministic source dataset is
[`app/data/mock_db.json`](app/data/mock_db.json). It contains a metadata object plus the
five top-level resource arrays: `customers`, `products`, `orders`, `tickets`, and
`reviews`.

Reusable request/response schemas and valid test bodies are committed in
[`app/data/mock_api_schemas.json`](app/data/mock_api_schemas.json). The file contains
JSON Schema definitions plus method, path, expected status, request example, and response
example entries for every mock CRUD operation. It is available from the hosted service at
`GET /mock-schemas.json`. Regenerate it after changing a Pydantic mock model or seed fixture:

```bash
uv run python scripts/export_mock_schemas.py
uv run python scripts/export_mock_schemas.py --check
```

The committed file is a seed, not a file that production requests rewrite:

- **Local default:** the mock repository is file-backed. On the first mock request it initializes the
  ignored writable runtime document `.mock-data/mock_db.json` from
  `app/data/mock_db.json`; CRUD calls update that runtime document, and reset restores it
  from the committed seed. Set `MOCK_DATA_FILE` to choose a different local path.
- **Hosted AWS environment:** `MOCK_STORAGE_BACKEND=s3` stores the same JSON document in
  a private, stack-managed S3 bucket. `MOCK_DATA_BUCKET` identifies that bucket and
  `MOCK_DATA_KEY=mock_db.json` identifies the object. Mutations therefore persist across
  Lambda cold starts and routine deployments. If the object does not exist, the app
  initializes it from the bundled seed; reset overwrites it with the seed. Conditional
  ETag writes retry concurrent changes so separate Lambda workers cannot silently overwrite
  one another, and old S3 object versions expire automatically after seven days.

This distinction matters because a Lambda deployment package is read-only and its
`/tmp` directory is instance-local and ephemeral. S3 is the durable hosted JSON file;
the bundled file remains the deterministic source for initialization and reset.

## Run locally

Python 3.12 or newer is required.

```bash
cp .env.example .env
make install
make dev
```

Then open `http://127.0.0.1:8000/test-ui`. The app initializes the legacy demo records at
startup and the local mock runtime document automatically on its first API request.

Run the test and contract suites in another terminal:

```bash
make test
make contract
make smoke
```

Exercise all 30 mock CRUD operations through real HTTP:

```bash
BASE_URL=http://127.0.0.1:8000 \
  uv run python scripts/mock_live_smoke.py
```

Point the same runner at the hosted environment by replacing `BASE_URL` with the public
base URL.

## The preserved 22-operation legacy API

The original authenticated API remains available without path or behavior changes. Its
contract count includes `/health` plus the auth, profile, project, and task operations
below. It explicitly excludes every `/api/v1/mock/...` operation.

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

Run the legacy live matrix with:

```bash
BASE_URL=https://xixoo2yundjxsbdwl3iw2eg5hi0ckwfu.lambda-url.us-east-1.on.aws \
  uv run python scripts/live_smoke.py
```

The legacy authentication model is unchanged: passwords are hashed, access tokens are
short-lived bearer JWTs, refresh tokens rotate, password-reset tokens are single-use,
and projects and tasks are owner-scoped. Demo reset tokens are exposed only to make the
public recovery flow testable.

## Testing strategy

The automated suite verifies both contracts independently:

- the mock-only specification exposes exactly 30 well-labeled CRUD operations with
  unique operation IDs;
- complete create, list, retrieve, `PUT`, `PATCH`, and delete lifecycles for every mock
  resource;
- mock validation, unique fields, foreign-key references, filters, pagination, computed
  order totals, and JSON reset behavior;
- the original API still exposes exactly 22 legacy operations after excluding
  `/api/v1/mock/...` paths;
- legacy auth, profile, project, task, ownership, and token edge cases; and
- health, readiness, CORS, test UI, both Swagger views, and both OpenAPI documents.

`scripts/mock_live_smoke.py` exercises all 30 mock operations against a real host with
disposable data. `scripts/live_smoke.py` exercises the legacy 22-operation matrix.
GitHub Actions performs non-mutating health and contract checks against the public
service every 15 minutes.

For PreMan or another schema-driven test system, ingest `/mock-openapi.json` to discover
only the 30 mock operations. Ingest `/openapi.json` when both the mock and legacy APIs
should be tested.

`app/routers/preman_probe.py` is the exception to all of the above: four routes under
`/api/v1/preman-probe/` that deliberately break the contract they publish, so a testing
system has something real to catch. `order-total` renames `total` to `total_cents`,
`refund-status` ships a documented number as a string, and `discount` accepts a
`percent_off` outside the 0–100 range it documents. Do not "fix" them without deleting
the fixture — a green run against these routes means the checks are not looking.

## Deploy the stable AWS demo URL

The included CloudFormation stack runs FastAPI behind a public Lambda Function URL. It
uses DynamoDB for the preserved legacy API and a private S3 JSON object for the mock API.
Both stores survive Lambda cold starts and routine code deployments.

Prerequisites are `uv`, `zip`, the AWS CLI, and an authenticated AWS account:

```bash
export AWS_REGION=us-east-1
./infra/deploy.sh
```

CloudFormation configures the hosted mock repository with:

```text
MOCK_STORAGE_BACKEND=s3
MOCK_DATA_BUCKET=<stack-managed bucket>
MOCK_DATA_KEY=mock_db.json
```

The deployment script prints the stable public base URL. Validate both public contracts
after deployment:

```bash
BASE_URL="$(aws cloudformation describe-stacks \
  --region "$AWS_REGION" \
  --stack-name greptile-codex-backend-demo \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)"

BASE_URL="$BASE_URL" python3 scripts/check_live.py
BASE_URL="$BASE_URL" python3 scripts/mock_live_smoke.py
```
