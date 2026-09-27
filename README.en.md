# MultiWeb

A DevOps learning project that practices monitoring, load testing and data analysis against a second-hand marketplace API (Application Programming Interface).

**English** | [한국어](README.md)

![Logging in with the demo account in Swagger UI and listing products](docs/images/login-flow.gif)

## Screenshots

| API docs (Swagger UI) | Product list response |
|---|---|
| ![API docs](docs/images/api-docs.png) | ![Product list response](docs/images/products-list.png) |

Output of `scripts/test-api.sh`:

![test-api.sh output](docs/images/test-api-terminal.png)

All screens above come from running this repository's code against a local PostgreSQL and Redis. The data is the demo account and sample listings.

## Features

**Marketplace API** (`app/`)
- Sign-up, login, JWT (JSON Web Token; JSON = JavaScript Object Notation) access and refresh tokens
- Product create / read / update / delete (soft delete), pagination, category and status filters, title/description search
- Create and read transactions (visible only to the buyer and the seller)
- Send and list messages between users
- Health checks: `/health`, `/health/ready` (checks DB (database) and Redis connections), `/health/live`
- Prometheus metrics at `/metrics`
- Structured JSON logs via structlog

**Infrastructure files**
- Docker Compose: API, PostgreSQL, Redis, Prometheus, Grafana, Loki, Promtail, Tempo, Nginx (`docker-compose.yml`)
- Nginx rate limits: API 10 r/s, login 5 r/m (`docker/nginx.conf`)
- Kubernetes manifests: API Deployment with HPA (Horizontal Pod Autoscaler), PostgreSQL, Redis, Ingress, Prometheus, Grafana, Loki, Promtail, Tempo (`k8s/`)
- Local Kind/Minikube cluster setup script (`scripts/setup-k8s.sh`)

**Testing and analysis tools**
- Locust load-test scenarios (`tests/locust/marketplace_load.py`)
- Attack simulations: HTTP (HyperText Transfer Protocol) flood, Slowloris, SQL (Structured Query Language) injection, XSS (Cross-Site Scripting), login brute force (`tests/attacks/simulate_attacks.py`)
- Prometheus metric collector and a Jupyter analysis notebook (`analytics/`)

Per-feature status and unfinished items are listed in the [progress record](docs/PROGRESS.en.md).

## Usage

### 1. Run locally (without Docker; how the screenshots were made)

PostgreSQL 16 and Redis must be running locally. The defaults are user `multiweb`, password `multiweb_password`, database `multiweb` (`app/core/config.py`).

```bash
# 1) Install dependencies (Python 3.12)
python -m venv .venv && source .venv/bin/activate
pip install -r app/requirements.txt

# 2) Point the app at local services
export POSTGRES_SERVER=localhost REDIS_HOST=localhost DEBUG=true

# 3) Create tables, categories and the demo account (drops existing tables first)
PYTHONPATH=. python scripts/init_db.py

# 4) Start the API server
uvicorn app.main:app --port 8000
```

`/docs` (Swagger UI) and `/redoc` are served only when `DEBUG=true`.

### 2. Basic flow

1. Open `http://localhost:8000/docs` in a browser.
2. Call `POST /api/v1/auth/login` with the demo account:
   ```json
   { "email": "demo@multiweb.com", "password": "demo123!" }
   ```
3. Paste the returned `access_token` into **Authorize** (top right).
4. List products with `GET /api/v1/products/`, then try the endpoints marked with a lock (create product, transactions, messages).

From the command line:

```bash
./scripts/test-api.sh http://localhost:8000
```

### 3. Docker Compose

```bash
docker-compose up -d
# or the interactive script
./scripts/quickstart.sh
```

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| Grafana | http://localhost:3000 (admin/admin) |
| Prometheus | http://localhost:9090 |
| Nginx | http://localhost:80 |

No Docker daemon was available while writing this, so the Compose stack was not run. Known issues, such as the API container's module path, are listed in the [progress record](docs/PROGRESS.en.md).

### 4. Kubernetes

```bash
cd scripts && ./setup-k8s.sh
```

See the [deployment guide](docs/DEPLOYMENT.md) (Korean) for details.

### 5. Load tests and attack simulation

```bash
pip install -r tests/locust/requirements.txt
cd tests/locust
locust -f marketplace_load.py --host=http://localhost:8000
```

```bash
pip install -r tests/attacks/requirements.txt
python tests/attacks/simulate_attacks.py
```

Run the attack simulations only against a local environment you own.

### 6. Data analysis

```bash
pip install -r analytics/collectors/requirements.txt
python analytics/collectors/collect_metrics.py   # reads Prometheus at localhost:9090
jupyter lab analytics/notebooks/metrics_analysis.ipynb
```

## Tech stack

| Area | Technology (versions pinned in the repo) |
|---|---|
| Language | Python 3.12 (`app/Dockerfile`) |
| Web framework | FastAPI 0.115.0, Uvicorn 0.30.6, Pydantic 2.9.0, pydantic-settings 2.5.0 |
| Database / ORM (Object-Relational Mapping) | PostgreSQL 16, SQLAlchemy 2.0.35 (asyncio), asyncpg 0.29.0 |
| Cache | Redis 7.2, redis-py 5.1.0 |
| Auth | python-jose 3.3.0 (JWT), passlib 1.7.4 + bcrypt 4.2.0 |
| Observability | prometheus-fastapi-instrumentator 7.0.0, structlog 24.4.0, Prometheus v2.53.0, Grafana 11.0.0, Loki/Promtail 3.0.0, Tempo 2.5.0 |
| Infrastructure | Docker Compose, Nginx, Kubernetes (Deployment, HPA, Ingress, DaemonSet) |
| Testing / analysis | Locust 2.31.0, httpx 0.27.2, Faker 30.3.0, pandas 2.2.3, NumPy 2.1.3, Matplotlib 3.9.2, seaborn 0.13.2 |

## Documentation

- [Progress record (final goal, status, history)](docs/PROGRESS.en.md)
- [Architecture](docs/ARCHITECTURE.md) (Korean)
- [Deployment guide](docs/DEPLOYMENT.md) (Korean)
- [Monitoring guide](docs/MONITORING.md) (Korean)
- [Review report, 2025-11-23](docs/REVIEW.md) (Korean)

## License

MIT License. This is a learning project. The passwords and keys in `k8s/base/secret.yaml` and `app/core/config.py` are local development defaults; override them with environment variables anywhere else.
