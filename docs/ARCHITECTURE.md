# MultiWeb 아키텍처 문서

## 개요

MultiWeb은 당근마켓과 같은 중고거래 플랫폼을 모델로 한 엔터프라이즈급 마이크로서비스 아키텍처입니다. 이 프로젝트는 DevOps 학습을 위해 설계되었으며, 실제 프로덕션 환경에서 사용되는 최신 기술 스택과 모범 사례를 포함합니다.

## 시스템 아키텍처

### 전체 구조

```
┌─────────────────────────────────────────────────────────────┐
│                         Internet                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Nginx Ingress Controller                        │
│  - Rate Limiting                                             │
│  - SSL/TLS Termination                                       │
│  - Request Routing                                           │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  FastAPI     │  │  FastAPI     │  │  FastAPI     │
│  Instance 1  │  │  Instance 2  │  │  Instance 3  │
│              │  │              │  │              │
│ - Auth       │  │ - Auth       │  │ - Auth       │
│ - Products   │  │ - Products   │  │ - Products   │
│ - Transactions│ │ - Transactions│ │ - Transactions│
│ - Messages   │  │ - Messages   │  │ - Messages   │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └────────┬────────┴────────┬────────┘
                │                 │
        ┌───────▼────────┐ ┌─────▼──────┐
        │  PostgreSQL 16 │ │  Redis 7.2 │
        │                │ │            │
        │ - Users        │ │ - Sessions │
        │ - Products     │ │ - Cache    │
        │ - Transactions │ │ - Counters │
        └────────────────┘ └────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  Observability Stack                         │
├────────────┬────────────┬────────────┬─────────────────────┤
│ Prometheus │  Grafana   │    Loki    │  Tempo (OpenTelemetry)│
│            │            │            │                      │
│ - Metrics  │ - Dashboards│ - Logs    │ - Traces            │
│ - Alerts   │ - Analytics│ - Query    │ - Distributed       │
└────────────┴────────────┴────────────┴─────────────────────┘
```

## 기술 스택

### 애플리케이션 계층

#### FastAPI Backend (Python 3.12)
- **비동기 처리**: asyncio + asyncpg for PostgreSQL
- **ORM**: SQLAlchemy 2.0 (async mode)
- **검증**: Pydantic v2
- **인증**: JWT (python-jose)
- **비밀번호**: bcrypt
- **API 문서**: OpenAPI/Swagger 자동 생성

**주요 특징:**
- RESTful API 설계
- 비동기 I/O로 높은 처리량
- 타입 힌트 및 자동 검증
- 의존성 주입 패턴

#### 데이터베이스

**PostgreSQL 16**
- Primary 데이터 저장소
- ACID 트랜잭션 보장
- 복잡한 쿼리 및 관계 처리
- Full-text search 지원

**스키마 구조:**
```sql
users
  ├─ products (1:N)
  ├─ transactions_as_buyer (1:N)
  ├─ transactions_as_seller (1:N)
  └─ messages (1:N)

products
  ├─ images (1:N)
  ├─ category (N:1)
  └─ transactions (1:N)

transactions
  ├─ buyer (N:1)
  ├─ seller (N:1)
  └─ product (N:1)
```

**Redis 7.2**
- 세션 관리
- API 응답 캐싱
- Rate limiting 카운터
- 실시간 기능 (WebSocket state)

### 인프라 계층

#### Kubernetes 1.29+
- **컨테이너 오케스트레이션**: Pod 관리, 스케일링
- **서비스 디스커버리**: Internal DNS
- **로드 밸런싱**: Service abstractions
- **자동 복구**: Liveness/Readiness probes
- **리소스 관리**: Requests & Limits

**리소스 구성:**
```yaml
Namespaces:
  - multiweb (애플리케이션)
  - ingress-nginx (Ingress)
  - monitoring (Prometheus, Grafana)

Deployments:
  - multiweb-api (Replicas: 3, HPA enabled)
  - postgres (Replicas: 1, StatefulSet 권장)
  - redis (Replicas: 1)
  - prometheus (Replicas: 1)
  - grafana (Replicas: 1)
  - loki (Replicas: 1)
  - tempo (Replicas: 1)

Services:
  - ClusterIP: Internal communication
  - LoadBalancer/Ingress: External access

HPA (Horizontal Pod Autoscaler):
  - Min replicas: 2
  - Max replicas: 10
  - CPU threshold: 70%
  - Memory threshold: 80%
```

#### Nginx Ingress Controller
- HTTP/HTTPS 트래픽 라우팅
- SSL/TLS termination
- Rate limiting
- Request buffering
- WebSocket support

**Rate Limiting 전략:**
```nginx
Login endpoint:   5 req/min
Register:        10 req/min
General API:    100 req/min
Static assets:  No limit
```

### 관찰성 (Observability)

#### Prometheus
- **메트릭 수집**: Pull-based model
- **저장소**: Time-series database
- **보존 기간**: 15일
- **스크랩 간격**: 15초

**수집 메트릭:**
- HTTP request metrics (rate, duration, status)
- System metrics (CPU, memory, disk)
- Database metrics (connections, queries)
- Redis metrics (commands, memory)
- Business metrics (users, products, transactions)

#### Grafana
- 시각화 대시보드
- 알림 관리
- 다중 데이터 소스 통합

**사전 구성 대시보드:**
1. Application Overview
2. API Performance
3. Database Metrics
4. Redis Metrics
5. Business Metrics
6. Attack Detection

#### Loki
- 로그 aggregation
- LogQL 쿼리 언어
- Grafana 통합

**로그 소스:**
- Application logs (JSON format)
- Nginx access logs
- System logs
- Container stdout/stderr

#### Tempo + OpenTelemetry
- 분산 트레이싱
- 요청 경로 추적
- 성능 병목 식별

**계측 포인트:**
- HTTP handlers
- Database queries
- Redis operations
- External API calls

## 데이터 플로우

### 사용자 요청 처리

```
1. User Request
   │
   ▼
2. Nginx Ingress
   ├─ Rate limit check
   ├─ SSL termination
   └─ Route to service
   │
   ▼
3. FastAPI Pod
   ├─ Authentication (JWT)
   ├─ Request validation (Pydantic)
   └─ Business logic
   │
   ├─ Check Redis cache
   │  ├─ Hit → Return cached response
   │  └─ Miss → Continue
   │
   ├─ Database query (PostgreSQL)
   │  └─ Async connection pool
   │
   ├─ Cache result (Redis)
   │
   └─ Return response
   │
   ▼
4. Response
   ├─ Metrics recorded (Prometheus)
   ├─ Logs emitted (Loki)
   └─ Trace completed (Tempo)
```

### 인증 플로우

```
1. Register/Login
   │
   ▼
2. Validate credentials
   ├─ Hash password (bcrypt)
   └─ Verify against DB
   │
   ▼
3. Generate JWT
   ├─ Access token (30 min)
   └─ Refresh token (7 days)
   │
   ▼
4. Store session (Redis)
   │
   ▼
5. Return tokens

Subsequent requests:
   ├─ Extract JWT from header
   ├─ Verify signature
   ├─ Check expiration
   └─ Extract user_id
```

### 트랜잭션 처리

```
1. Create Transaction Request
   │
   ▼
2. Validate
   ├─ Product exists
   ├─ Product available
   ├─ Buyer != Seller
   └─ Amount > 0
   │
   ▼
3. Database Transaction (BEGIN)
   ├─ Insert transaction record
   ├─ Update product status
   └─ Create notification
   │
   ▼
4. COMMIT
   │
   ▼
5. Send notifications
   ├─ WebSocket (real-time)
   └─ Email (async task)
   │
   ▼
6. Update metrics
   └─ Business counters
```

## 보안 아키텍처

### 계층별 보안

#### 1. Network Layer
- **Ingress**: TLS 1.3, HTTPS only
- **Network Policies**: Pod-to-Pod 통신 제한
- **Firewall**: Port filtering

#### 2. Application Layer
- **Authentication**: JWT with RS256
- **Authorization**: Role-based access control (RBAC)
- **Input Validation**: Pydantic schemas
- **SQL Injection Prevention**: ORM, parameterized queries
- **XSS Prevention**: Output escaping
- **CSRF Protection**: Token-based

#### 3. Data Layer
- **Encryption at Rest**: Database encryption
- **Encryption in Transit**: TLS for all connections
- **Secrets Management**: Kubernetes Secrets
- **Password Hashing**: bcrypt (cost=12)

#### 4. API Security
- **Rate Limiting**: Nginx + Redis
- **CORS**: Whitelist origins
- **API Keys**: For service-to-service
- **Request Size Limits**: 10MB max

### 공격 방어 메커니즘

#### DDoS Protection
```
Layer 7 DDoS:
  ├─ Rate limiting (Nginx)
  ├─ Connection limits
  └─ Request queuing

Layer 4 DDoS:
  ├─ SYN flood protection
  └─ Connection tracking
```

#### Brute Force Protection
```
Login attempts:
  ├─ Rate limit: 5 attempts/min
  ├─ Account lockout: 15 min
  └─ CAPTCHA after 3 failures
```

#### SQL Injection
```
Prevention:
  ├─ SQLAlchemy ORM
  ├─ Parameterized queries
  ├─ Input validation
  └─ Principle of least privilege
```

## 확장성 설계

### Horizontal Scaling

**애플리케이션 Pod:**
- Stateless design
- Auto-scaling (HPA)
- Session in Redis (shared state)

**데이터베이스:**
- Read replicas (future)
- Connection pooling
- Query optimization

### Vertical Scaling

**리소스 limits:**
```yaml
API Pod:
  requests:
    memory: 256Mi
    cpu: 250m
  limits:
    memory: 1Gi
    cpu: 1000m
```

### Caching Strategy

**레벨 1: Application Cache**
- In-memory (LRU)
- 빠른 접근
- Pod별로 독립적

**레벨 2: Redis Cache**
- 공유 캐시
- TTL 기반
- 영구성 옵션

**캐싱 전략:**
```python
# Cache-aside pattern
def get_product(product_id):
    # Check cache
    cached = redis.get(f"product:{product_id}")
    if cached:
        return cached

    # Query database
    product = db.query(Product).get(product_id)

    # Update cache
    redis.set(f"product:{product_id}", product, ex=300)

    return product
```

## 성능 최적화

### Database Optimization

**인덱스 전략:**
```sql
-- Composite indexes for common queries
CREATE INDEX idx_product_status_created
  ON products(status, created_at);

CREATE INDEX idx_product_category_status
  ON products(category_id, status);

-- Partial indexes
CREATE INDEX idx_active_products
  ON products(created_at)
  WHERE status = 'available';
```

**Connection Pooling:**
```python
# SQLAlchemy async engine
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### API Optimization

**비동기 처리:**
```python
# Concurrent database queries
async def get_user_dashboard(user_id):
    products, transactions, messages = await asyncio.gather(
        get_user_products(user_id),
        get_user_transactions(user_id),
        get_user_messages(user_id)
    )
    return {
        "products": products,
        "transactions": transactions,
        "messages": messages
    }
```

**응답 압축:**
- GZip middleware
- 최소 크기: 1000 bytes

## 모니터링 전략

### Golden Signals

1. **Latency**: 요청 처리 시간
   - P50, P95, P99
   - Endpoint별 분석

2. **Traffic**: 요청 빈도
   - Requests per second
   - 패턴 분석

3. **Errors**: 에러율
   - 5xx errors
   - 4xx errors
   - Exception tracking

4. **Saturation**: 리소스 사용률
   - CPU, Memory
   - Database connections
   - Redis memory

### SLOs (Service Level Objectives)

```yaml
Availability: 99.9%
Latency (P95): < 200ms
Error Rate: < 0.1%
```

### 알림 규칙

```yaml
Critical:
  - API 5xx rate > 1%
  - Database connections > 90%
  - Pod crash loop

Warning:
  - API latency P95 > 500ms
  - Memory usage > 80%
  - Disk usage > 75%
```

## 재해 복구 (Disaster Recovery)

### 백업 전략

**데이터베이스:**
- 자동 백업: 매일 03:00
- 보존 기간: 30일
- Point-in-time recovery

**설정 파일:**
- Git repository
- GitOps (ArgoCD)

### 복구 절차

```bash
1. Identify issue
2. Check backups
3. Restore from backup
4. Verify data integrity
5. Resume operations
6. Post-mortem analysis
```

## 개발 워크플로우

### 로컬 개발

```bash
1. Clone repository
2. docker-compose up -d
3. Install dependencies
4. Run tests
5. Develop features
6. Create PR
```

### CI/CD Pipeline (Future)

```yaml
On Push:
  - Run tests
  - Lint code
  - Build Docker image
  - Push to registry

On Merge to Main:
  - Deploy to staging
  - Run integration tests
  - Deploy to production (manual approval)
```

## 모범 사례

### 코드 품질
- Type hints everywhere
- Unit tests (>80% coverage)
- Integration tests
- Code reviews

### 운영
- Structured logging (JSON)
- Distributed tracing
- Health checks
- Graceful shutdown

### 보안
- Least privilege principle
- Regular security audits
- Dependency updates
- Secret rotation

## 향후 개선 사항

1. **Service Mesh** (Istio/Linkerd)
   - Advanced traffic management
   - mTLS between services
   - Circuit breaking

2. **Message Queue** (RabbitMQ/Kafka)
   - Async task processing
   - Event-driven architecture
   - Decoupling services

3. **CDN Integration**
   - Static asset delivery
   - Image optimization
   - Global distribution

4. **Advanced Analytics**
   - Machine learning models
   - Fraud detection
   - Recommendation engine

5. **Multi-region Deployment**
   - Geographic distribution
   - Data replication
   - Disaster recovery

## 결론

MultiWeb은 현대적인 클라우드 네이티브 애플리케이션의 모범 사례를 구현합니다. 이 아키텍처는 확장 가능하고, 관찰 가능하며, 안전한 시스템을 구축하는 방법을 보여줍니다. DevOps 학습자는 이 프로젝트를 통해 실제 프로덕션 환경에서 사용되는 기술과 패턴을 익힐 수 있습니다.
