# Progress record

**English** | [한국어](PROGRESS.md)

## Final goal

Build a second-hand marketplace API (Application Programming Interface) and run a DevOps stack on top of it that resembles a real production setup, in order to practice:

- An observability stack that collects metrics, logs and distributed traces
- Autoscaling and rolling updates on Kubernetes
- Finding bottlenecks and checking defenses with load tests and attack simulations
- Analyzing the collected operational data in Jupyter

## Current implementation status

Verified on 2026-09-27 by reading the code and running the API against a local PostgreSQL 16 and Redis. Status is based on code and observed behavior, not on claims in earlier docs or commit messages.

| Feature | Status | Code | What was checked |
|---|---|---|---|
| Sign-up, login, JWT (JSON Web Token) issue | Implemented | `app/api/endpoints/auth.py`, `app/core/security.py` | Ran sign-up, login, token issue |
| Token refresh endpoint | Not started | `app/core/security.py` | Refresh tokens are issued but no endpoint accepts them |
| Current-user profile read/update | Not started | `app/schemas/user.py` | Only a `UserUpdate` schema exists |
| Product list, search, filters, pagination | Implemented | `app/api/endpoints/products.py` `list_products` | Ran it |
| Product detail (view counter) | Implemented | `products.py` `get_product` | Ran it |
| Product create / update | Partial | `products.py` `create_product`, `update_product` | Row is saved to the DB (database), but response serialization raises `DetachedInstanceError`, so the API returns HTTP (HyperText Transfer Protocol) 500 |
| Product delete (soft delete, seller only) | Implemented | `products.py` `delete_product` | Delete by another user returns 403 |
| Image upload | Not started | `app/core/config.py` (`UPLOAD_DIR` setting only) | No upload endpoint; product creation only accepts image URLs (Uniform Resource Locators) |
| Transaction create / read | Implemented | `app/api/endpoints/transactions.py` | Ran it |
| Transaction status changes (confirm, complete, cancel) | Not started | `app/models/transaction.py` | Status values exist in the model, no endpoint |
| Send / list messages | Implemented | `app/api/endpoints/messages.py` | Ran it |
| Real-time chat (WebSocket) | Not started | `app/requirements.txt` | `websockets` is a dependency, but no WebSocket route exists |
| Reviews | Partial | `app/models/transaction.py` `Review` | Table model only, no API |
| Payment simulation | Not started | - | No payment logic (only a `payment_method` field) |
| Health checks (`/health`, `/health/ready`, `/health/live`) | Implemented | `app/api/endpoints/health.py` | Ran them |
| Prometheus metrics `/metrics` | Implemented | `app/main.py` (Instrumentator) | Ran it |
| Business metrics (`multiweb_products_created_total`, ...) | Not started | `analytics/collectors/collect_metrics.py` | The collector queries them, but the app never emits them |
| Structured logging (structlog JSON) | Implemented | `app/main.py` | Seen in run logs |
| OpenTelemetry distributed tracing | Not started | `app/core/config.py` (`OTEL_*` settings only) | No instrumentation in the app; only Tempo deployment files |
| In-app rate limiting | Not started | `app/core/config.py` (`RATE_LIMIT_*` settings only) | Settings are unused |
| Nginx rate limiting | Implemented (not run) | `docker/nginx.conf` | Config file only |
| DB init and demo data | Implemented | `scripts/init_db.py` | Ran with `PYTHONPATH=.` |
| DB migrations (Alembic) | Not started | `app/requirements.txt` | Package listed, no migrations directory |
| Docker Compose stack | Partial (not run) | `docker-compose.yml`, `app/Dockerfile` | See "Known issues" |
| Kubernetes manifests (Deployment, HPA (Horizontal Pod Autoscaler), Ingress, monitoring, logging) | Implemented (not run) | `k8s/` | No cluster available to apply them |
| Helm chart | Not started | - | No `helm/` directory |
| Grafana dashboards | Not started | `docker-compose.yml` | Mounts `analytics/dashboards`, which does not exist |
| Locust load test | Implemented | `tests/locust/marketplace_load.py` | Headless run, 5 users for 12 s: 123 requests, 0 failures |
| Attack simulations | Implemented (not run) | `tests/attacks/simulate_attacks.py` | Code only |
| Metric collector and analysis notebook | Implemented (not run) | `analytics/collectors/collect_metrics.py`, `analytics/notebooks/metrics_analysis.ipynb` | No Prometheus available to run against |
| Automated tests (unit / integration) | Not started | `tests/` | No pytest test files |

### Known issues

- **API container module path**: `app/Dockerfile` copies the contents of `app/` into `/app` and runs `uvicorn app.main:app`. The code imports `from app.core ...`, which needs an `/app/app` package inside the container, and there is none. The `./app:/app` mount in `docker-compose.yml` has the same layout. Not run (no Docker daemon); concluded from reading the code.
- **Init path in `quickstart.sh`**: `docker-compose exec api python /app/../scripts/init_db.py` points to `/scripts`, which is not mounted in the container.
- **Product create/update returns 500**: see the table above.
- **passlib warning**: bcrypt 4.2.0 with passlib 1.7.4 prints `module 'bcrypt' has no attribute '__about__'`. Hashing and verification still work.
- **ruff**: `ruff check app scripts tests analytics` reports 12 unused imports.
- **Missing `email-validator`**: added to `app/requirements.txt` in this change. Without it the app fails to start because of `EmailStr`.

## Work history

Taken from `git log`, times converted to KST (Korea Standard Time, Asia/Seoul). Commits stored with a +0000 offset were shifted by 9 hours.

| Date (KST) | Commit | Summary |
|---|---|---|
| 2024-10-23 11:02 | `8fa38ba` | Repository created |
| 2025-11-22 23:20 | `3717990` | FastAPI app, Docker Compose, Kubernetes manifests, Locust and attack simulations, analytics collector and notebook, architecture/deployment/monitoring docs |
| 2025-11-23 12:06 | `3e19650` | Added missing `__init__.py` files, fixed Pydantic v2 settings, split Compose-specific Prometheus/Promtail configs, added `init_db.py`, `quickstart.sh`, `test-api.sh`, wrote the review report |
| 2025-11-30 22:49 | `639d09c` | Merged the work branch into main (PR (pull request) #1) |
| 2026-09-27 | this change | Added `email-validator`, split README into Korean/English with screenshots, added this progress record |
