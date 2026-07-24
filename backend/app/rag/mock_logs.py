"""
Static mock log corpus for the search_error_logs RAG tool. Two sources:
"cicd" (build/test/deploy logs) and "cloudwatch" (application runtime logs).

A few entries deliberately echo monitoring_client.py's mock incident history
(INC-142, INC-139, INC-131) so a question about one of those incidents has a
concrete supporting log line to retrieve, not just the incident summary.

This is a fixed, hand-authored corpus, not a live log stream — see
ingest.py for how it gets embedded and loaded into Postgres.
"""

MOCK_LOGS: list[dict] = [
    # --- cicd ---
    {
        "id": "cicd-001",
        "source": "cicd",
        "service": "payments",
        "content": (
            "FAILED tests/test_refund.py::test_partial_refund_rounding - "
            "AssertionError: expected Decimal('12.50') but got Decimal('12.49'). "
            "Rounding mode changed after switching to Decimal ROUND_HALF_UP in "
            "commit a1b2c3d."
        ),
    },
    {
        "id": "cicd-002",
        "source": "cicd",
        "service": "checkout",
        "content": (
            "docker build failed: failed to solve: process \"/bin/sh -c pip install "
            "-r requirements.txt\" did not complete successfully: exit code 1. "
            "ERROR: Could not find a version that satisfies the requirement "
            "httpx==0.28.0 (base image pinned to Python 3.9, httpx 0.28 requires >=3.10)."
        ),
    },
    {
        "id": "cicd-003",
        "source": "cicd",
        "service": "frontend",
        "content": (
            "npm ERR! ERESOLVE unable to resolve dependency tree. npm ERR! Found: "
            "react@18.3.1. npm ERR! Could not resolve dependency: peer react@\"^17.0.0\" "
            "from react-beautiful-dnd@13.1.1."
        ),
    },
    {
        "id": "cicd-004",
        "source": "cicd",
        "service": "checkout",
        "content": (
            "FAILED (flaky, retried 3x) tests/integration/test_checkout_flow.py::"
            "test_apply_promo_code - TimeoutError: waited 30s for element "
            "[data-testid=promo-applied] to appear, never did. Passed on local run."
        ),
    },
    {
        "id": "cicd-005",
        "source": "cicd",
        "service": "billing",
        "content": (
            "eslint: 14 problems (14 errors, 0 warnings). "
            "src/billing/invoiceCalculator.ts:42:7 - error no-unused-vars 'taxRateOverride' "
            "is assigned a value but never used. Merge blocked by required check."
        ),
    },
    {
        "id": "cicd-006",
        "source": "cicd",
        "service": "orders",
        "content": (
            "Deploy to production rolled back automatically: post-deploy health check "
            "GET /healthz returned 503 for 5 consecutive checks (30s). Reverting to "
            "previous revision orders-api:2024.11.3."
        ),
    },
    {
        "id": "cicd-007",
        "source": "cicd",
        "service": "infra",
        "content": (
            "terraform apply failed: Error: creating S3 Bucket (delivery-app-exports): "
            "BucketAlreadyOwnedByYou. Resource already exists outside of state — "
            "likely created manually, needs terraform import."
        ),
    },
    {
        "id": "cicd-008",
        "source": "cicd",
        "service": "orders",
        "content": (
            "Test suite killed: OOMKilled. CI runner (7GB limit) exceeded during "
            "tests/test_bulk_import.py — loading full 500k-row fixture into memory "
            "instead of streaming. Consider chunked fixture loading."
        ),
    },
    {
        "id": "cicd-009",
        "source": "cicd",
        "service": "infra",
        "content": (
            "docker push failed: unauthorized: authentication required. Registry token "
            "for ghcr.io expired (30-day rotation policy) — pipeline secret "
            "GHCR_TOKEN needs manual refresh, auto-rotation not yet configured."
        ),
    },
    {
        "id": "cicd-010",
        "source": "cicd",
        "service": "orders",
        "content": (
            "alembic upgrade failed: sqlalchemy.exc.ProgrammingError: column "
            "\"fulfillment_status\" of relation \"orders\" already exists. Migration "
            "0032 was partially applied in a previous failed deploy and not rolled back."
        ),
    },
    {
        "id": "cicd-011",
        "source": "cicd",
        "service": "checkout",
        "content": (
            "Deploy succeeded but staging smoke test failed: POST /api/checkout "
            "returned 422 'currency field required' — new required field shipped "
            "without a default, frontend not yet updated to send it."
        ),
    },
    {
        "id": "cicd-012",
        "source": "cicd",
        "service": "infra",
        "content": (
            "GitHub Actions job cancelled: workflow exceeded the 6h job timeout "
            "running tests/e2e/ — suspected infinite retry loop in the new "
            "WebSocket reconnect test, no backoff cap configured."
        ),
    },
    {
        "id": "cicd-013",
        "source": "cicd",
        "service": "frontend",
        "content": (
            "Cypress: 1 of 42 failing — checkout.cy.ts > 'shows order summary' — "
            "CypressError: Timed out retrying: Expected to find element: "
            "[data-testid=order-summary], but never found it. Selector renamed "
            "in OrderSummary.tsx refactor, test not updated."
        ),
    },
    {
        "id": "cicd-014",
        "source": "cicd",
        "service": "infra",
        "content": (
            "Build cache restore produced stale node_modules — lockfile hash "
            "matched an old cache key after a force-push rewrote history. Build "
            "installed react-router@5 instead of the pinned v6, 23 type errors followed."
        ),
    },
    {
        "id": "cicd-015",
        "source": "cicd",
        "service": "orders",
        "content": (
            "Canary deployment aborted at 10% traffic: error rate 4.2% vs 0.3% "
            "baseline over 5min window, exceeded the 2% auto-rollback threshold. "
            "Canary revision orders-api:2024.11.5 not promoted."
        ),
    },
    # --- cloudwatch ---
    {
        "id": "cw-001",
        "source": "cloudwatch",
        "service": "orders",
        "content": (
            "ERROR [orders-api] Unhandled exception in OrderService.applyDiscount: "
            "TypeError: Cannot read properties of undefined (reading 'percentage') "
            "at applyDiscount (orderService.js:118). discount object was null for "
            "orders with no active promotion — missing null check."
        ),
    },
    {
        "id": "cw-002",
        "source": "cloudwatch",
        "service": "orders",
        "content": (
            "ERROR [orders-api] could not obtain connection from pool within 30000ms. "
            "Pool stats: active=20 idle=0 max=20. Sustained for 47 minutes starting "
            "14:02 UTC. Root cause: a batch export job held long-running transactions "
            "without releasing connections. Matches incident INC-142."
        ),
    },
    {
        "id": "cw-003",
        "source": "cloudwatch",
        "service": "auth",
        "content": (
            "WARN [api-gateway] 502 Bad Gateway rate spiked to 8.1% of requests to "
            "/api/auth/verify over 5min. Upstream auth-service p99 latency 29.8s "
            "(timeout 30s) — likely downstream IdP outage, not an auth-service bug."
        ),
    },
    {
        "id": "cw-004",
        "source": "cloudwatch",
        "service": "notifications",
        "content": (
            "WARN [notifications-worker] heap usage climbed from 180MB to 1.9GB over "
            "6h with no corresponding traffic increase. Container OOMKilled at 14:55 "
            "UTC. Suspect: EventEmitter listeners added per-request in "
            "subscribeToOrderEvents() and never removed."
        ),
    },
    {
        "id": "cw-005",
        "source": "cloudwatch",
        "service": "payments",
        "content": (
            "ERROR [payments-api] StripeRateLimitError: Too many requests hit the "
            "API too quickly. 429 responses on 61 of the last 200 charge attempts. "
            "No client-side backoff/retry implemented. Matches incident INC-131."
        ),
    },
    {
        "id": "cw-006",
        "source": "cloudwatch",
        "service": "orders",
        "content": (
            "WARN [orders-api] slow query: SELECT * FROM orders WHERE "
            "customer_id = $1 AND status = $2 took 4200ms (usually <20ms). "
            "EXPLAIN shows sequential scan — composite index on "
            "(customer_id, status) missing after last schema migration."
        ),
    },
    {
        "id": "cw-007",
        "source": "cloudwatch",
        "service": "orders",
        "content": (
            "ERROR [orders-api] Redis connection refused at cache.internal:6379. "
            "ECONNREFUSED. Falling back to direct DB reads — latency up 6x, DB CPU "
            "at 91%. Cache node was terminated by an unrelated autoscaling event."
        ),
    },
    {
        "id": "cw-008",
        "source": "cloudwatch",
        "service": "auth",
        "content": (
            "ERROR [auth-service] JWT validation failed: token used before issued "
            "(iat is in the future). Client clock skew of +94s detected. Affected "
            "~2% of requests from one region's edge nodes with unsynced NTP."
        ),
    },
    {
        "id": "cw-009",
        "source": "cloudwatch",
        "service": "infra",
        "content": (
            "WARN [log-shipper] disk usage on /var/log at 89%, projected to hit "
            "100% in ~6h at current ingest rate. Application log volume for "
            "orders-api tripled after debug-level logging was left enabled post-incident."
        ),
    },
    {
        "id": "cw-010",
        "source": "cloudwatch",
        "service": "notifications",
        "content": (
            "ERROR [notifications-worker] UnhandledPromiseRejectionWarning: "
            "Error: connect ETIMEDOUT sending push notification via FCM. Promise "
            "from sendPushBatch() had no .catch(), crashed the worker process, "
            "PM2 restarted it 40 times in an hour."
        ),
    },
    {
        "id": "cw-011",
        "source": "cloudwatch",
        "service": "checkout",
        "content": (
            "ERROR [checkout-api] 500 error rate jumped from 0.1% to 6.4% "
            "immediately following deploy of checkout-api:2024.11.2 at 09:14 UTC. "
            "Bad deploy, rolled back at 09:26 UTC. Matches incident INC-139."
        ),
    },
    {
        "id": "cw-012",
        "source": "cloudwatch",
        "service": "inventory",
        "content": (
            "WARN [orders-api] circuit breaker OPEN for inventory-service after "
            "5 consecutive failures (threshold: 5, window: 60s). All "
            "reserveInventory() calls short-circuiting to cached availability for "
            "the next 30s cooldown."
        ),
    },
    {
        "id": "cw-013",
        "source": "cloudwatch",
        "service": "orders",
        "content": (
            "ERROR [orders-api] deadlock detected. Process 4021 waits for "
            "ShareLock on transaction 88213; blocked by process 4033. Two "
            "concurrent order-fulfillment jobs updated the same order row in "
            "opposite column order — classic lock-ordering bug."
        ),
    },
    {
        "id": "cw-014",
        "source": "cloudwatch",
        "service": "orders",
        "content": (
            "WARN [k8s] Pod orders-api-7d9f8c-x2n4p evicted: memory pressure. "
            "Node had 1.2GB available, pod requested 512Mi but was observed using "
            "1.4GB — no memory limit set, allowing unbounded growth under load."
        ),
    },
    {
        "id": "cw-015",
        "source": "cloudwatch",
        "service": "checkout",
        "content": (
            "WARN [checkout-api] p99 latency on POST /api/checkout hit 12.3s "
            "during Black Friday traffic spike (baseline p99: 340ms). Correlates "
            "with the orders DB connection pool exhaustion — same root cause as INC-142."
        ),
    },
]
