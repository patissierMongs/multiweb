# MultiWeb 모니터링 가이드

이 문서는 MultiWeb 마켓플레이스의 모니터링 시스템 사용 방법과 데이터 분석 방법을 설명합니다.

## 목차

1. [모니터링 스택 개요](#모니터링-스택-개요)
2. [Prometheus 메트릭](#prometheus-메트릭)
3. [Grafana 대시보드](#grafana-대시보드)
4. [로그 분석 (Loki)](#로그-분석-loki)
5. [분산 트레이싱 (Tempo)](#분산-트레이싱-tempo)
6. [알림 설정](#알림-설정)
7. [데이터 수집 및 분석](#데이터-수집-및-분석)

## 모니터링 스택 개요

MultiWeb은 포괄적인 관찰성(Observability)을 위해 다음 도구들을 사용합니다:

```
┌─────────────────────────────────────────────┐
│           Grafana (시각화)                   │
└──────┬──────────┬──────────┬───────────────┘
       │          │          │
   ┌───▼───┐  ┌──▼───┐  ┌───▼────┐
   │Prometheus│ │ Loki │  │ Tempo  │
   │(Metrics) │ │(Logs)│  │(Traces)│
   └────┬────┘  └──┬───┘  └───┬────┘
        │          │          │
   ┌────▼──────────▼──────────▼─────┐
   │      MultiWeb Application       │
   └─────────────────────────────────┘
```

### 접속 정보

**Docker Compose:**
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- Loki: http://localhost:3100

**Kubernetes:**
```bash
# 포트 포워딩
kubectl port-forward svc/prometheus 9090:9090 -n multiweb
kubectl port-forward svc/grafana 3000:3000 -n multiweb
kubectl port-forward svc/loki 3100:3100 -n multiweb
```

## Prometheus 메트릭

### 주요 메트릭 카테고리

#### 1. HTTP 메트릭

**요청률 (Request Rate)**
```promql
# 초당 요청 수
rate(http_requests_total[5m])

# 엔드포인트별 요청률
sum(rate(http_requests_total[5m])) by (path)

# 상태 코드별 요청률
sum(rate(http_requests_total[5m])) by (status)
```

**에러율 (Error Rate)**
```promql
# 5xx 에러율
rate(http_requests_total{status=~"5.."}[5m])

# 전체 에러율 (%)
100 * sum(rate(http_requests_total{status=~"[45].."}[5m]))
    / sum(rate(http_requests_total[5m]))
```

**응답 시간 (Latency)**
```promql
# P50 (중앙값)
histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))

# P95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# P99
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
```

#### 2. 시스템 메트릭

**CPU 사용률**
```promql
# CPU 사용률 (%)
100 * rate(process_cpu_seconds_total[5m])

# Pod별 CPU 사용률
sum(rate(container_cpu_usage_seconds_total[5m])) by (pod)
```

**메모리 사용률**
```promql
# 메모리 사용량 (bytes)
process_resident_memory_bytes

# 메모리 사용률 (%)
100 * process_resident_memory_bytes / node_memory_MemTotal_bytes
```

**디스크 I/O**
```promql
# 디스크 읽기 속도
rate(node_disk_read_bytes_total[5m])

# 디스크 쓰기 속도
rate(node_disk_written_bytes_total[5m])
```

#### 3. 데이터베이스 메트릭

**PostgreSQL**
```promql
# 활성 연결 수
pg_stat_database_numbackends

# 트랜잭션률
rate(pg_stat_database_xact_commit[5m])

# 쿼리 실행 시간
pg_stat_statements_mean_exec_time_seconds
```

**Redis**
```promql
# 명령 처리율
rate(redis_commands_processed_total[5m])

# 메모리 사용량
redis_memory_used_bytes

# Hit rate
rate(redis_keyspace_hits_total[5m])
/ (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m]))
```

#### 4. 비즈니스 메트릭

이러한 메트릭은 애플리케이션에서 커스텀으로 노출해야 합니다:

```python
# app/api/endpoints/products.py
from prometheus_client import Counter, Histogram

# 카운터
products_created = Counter(
    'multiweb_products_created_total',
    'Total number of products created'
)

transactions_completed = Counter(
    'multiweb_transactions_completed_total',
    'Total number of completed transactions'
)

# 게이지
active_users = Gauge(
    'multiweb_active_users',
    'Number of currently active users'
)
```

**쿼리 예제:**
```promql
# 시간당 생성된 상품 수
sum(increase(multiweb_products_created_total[1h]))

# 시간당 완료된 거래 수
sum(increase(multiweb_transactions_completed_total[1h]))

# 활성 사용자 수
multiweb_active_users
```

### 유용한 PromQL 쿼리

**트래픽 패턴 분석**
```promql
# 시간대별 평균 요청률
avg_over_time(rate(http_requests_total[5m])[1h:5m])

# 피크 시간 식별
topk(10, rate(http_requests_total[5m]))
```

**성능 이상 탐지**
```promql
# 응답 시간이 평균보다 2배 이상 느린 엔드포인트
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
> 2 * avg_over_time(
    histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))[1h:]
  )
```

**리소스 포화도**
```promql
# CPU 포화도 (> 80% 경고)
100 * rate(process_cpu_seconds_total[5m]) > 80

# 메모리 포화도 (> 90% 경고)
100 * process_resident_memory_bytes / node_memory_MemTotal_bytes > 90
```

## Grafana 대시보드

### 사전 구성된 대시보드

#### 1. Application Overview

**패널:**
- 총 요청 수 (Total Requests)
- 평균 응답 시간 (Avg Response Time)
- 에러율 (Error Rate)
- 활성 사용자 (Active Users)
- 요청률 시계열 (Request Rate Timeline)
- 상태 코드 분포 (Status Code Distribution)

#### 2. API Performance

**패널:**
- 엔드포인트별 요청률
- 엔드포인트별 응답 시간 (P50, P95, P99)
- 느린 엔드포인트 Top 10
- 에러가 많은 엔드포인트 Top 10

#### 3. Database Metrics

**패널:**
- PostgreSQL 연결 수
- 트랜잭션률 (Commits vs Rollbacks)
- 쿼리 실행 시간
- 데이터베이스 크기
- 테이블별 I/O 통계

#### 4. Business Metrics

**패널:**
- 신규 사용자 등록 (시간별)
- 생성된 상품 수 (시간별)
- 완료된 거래 수 (시간별)
- 전송된 메시지 수 (시간별)
- 매출 추이 (시간별)

### 커스텀 대시보드 만들기

1. Grafana UI 접속
2. Create > Dashboard
3. Add Panel 클릭
4. Query 작성:
   ```promql
   rate(http_requests_total{path="/api/v1/products/"}[5m])
   ```
5. 시각화 옵션 선택 (Time series, Bar chart, etc.)
6. Panel 저장

### 변수 사용하기

대시보드에 동적 변수 추가:

```
Settings > Variables > Add variable

Name: namespace
Label: Namespace
Type: Query
Data source: Prometheus
Query: label_values(kube_pod_info, namespace)
```

패널에서 사용:
```promql
rate(http_requests_total{namespace="$namespace"}[5m])
```

## 로그 분석 (Loki)

### LogQL 쿼리 언어

**기본 구문:**
```logql
# 모든 로그
{app="multiweb-api"}

# 특정 레벨의 로그
{app="multiweb-api"} |= "ERROR"

# JSON 파싱
{app="multiweb-api"} | json | level="error"

# 정규식 필터
{app="multiweb-api"} |~ "status=[45][0-9]{2}"
```

### 유용한 쿼리

**에러 로그 검색**
```logql
{app="multiweb-api"} | json | level="error" | line_format "{{.timestamp}} {{.message}}"
```

**특정 사용자 활동 추적**
```logql
{app="multiweb-api"} | json | user_id="123" | line_format "{{.method}} {{.path}} {{.status}}"
```

**느린 요청 찾기**
```logql
{app="multiweb-api"} | json | duration > 1.0 | line_format "{{.path}} took {{.duration}}s"
```

**요청률 계산**
```logql
sum(rate({app="multiweb-api"} | json | status=~"2.." [5m]))
```

### Grafana에서 로그 보기

1. Explore 메뉴
2. Data source: Loki 선택
3. 쿼리 입력
4. Run Query

**실시간 로그 스트리밍:**
- Live 버튼 클릭
- 로그가 실시간으로 업데이트됨

## 분산 트레이싱 (Tempo)

### 트레이스 수집

애플리케이션에서 OpenTelemetry 계측:

```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# 트레이서 설정
provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="tempo:4317"))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

# 트레이스 사용
@app.get("/api/v1/products/")
async def list_products():
    with tracer.start_as_current_span("list_products"):
        # 비즈니스 로직
        products = await fetch_products_from_db()
        return products
```

### Grafana에서 트레이스 보기

1. Explore 메뉴
2. Data source: Tempo 선택
3. Trace ID로 검색 또는 Query Builder 사용
4. 트레이스 시각화 확인

**트레이스에서 확인할 수 있는 정보:**
- 요청 전체 경로
- 각 서비스별 처리 시간
- 데이터베이스 쿼리 시간
- 외부 API 호출 시간
- 에러 발생 위치

## 알림 설정

### Prometheus Alerting Rules

`k8s/monitoring/alerts.yaml` 생성:

```yaml
groups:
- name: multiweb_alerts
  interval: 30s
  rules:
  # High error rate
  - alert: HighErrorRate
    expr: |
      100 * sum(rate(http_requests_total{status=~"5.."}[5m]))
      / sum(rate(http_requests_total[5m])) > 1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }}%"

  # High latency
  - alert: HighLatency
    expr: |
      histogram_quantile(0.95,
        rate(http_request_duration_seconds_bucket[5m])
      ) > 0.5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High API latency"
      description: "P95 latency is {{ $value }}s"

  # Database connection pool exhaustion
  - alert: DatabaseConnectionPoolHigh
    expr: pg_stat_database_numbackends > 80
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "Database connection pool is nearly exhausted"
```

### Grafana Alerts

1. Dashboard panel 설정
2. Alert 탭 클릭
3. Create Alert 클릭
4. 조건 설정:
   ```
   WHEN avg() OF query(A, 5m, now) IS ABOVE 0.5
   ```
5. 알림 채널 설정 (Email, Slack, etc.)

### 알림 채널 설정

**Slack 통합:**

1. Grafana > Alerting > Notification channels
2. Add channel
3. Type: Slack
4. Webhook URL 입력
5. Test 클릭

## 데이터 수집 및 분석

### Python 스크립트로 메트릭 수집

```bash
cd analytics/collectors
python collect_metrics.py
```

수집된 데이터:
- `analytics/data/http_metrics_YYYYMMDD_HHMMSS.csv`
- `analytics/data/system_metrics_YYYYMMDD_HHMMSS.csv`
- `analytics/data/business_metrics_YYYYMMDD_HHMMSS.csv`

### Jupyter Notebook 분석

```bash
cd analytics
jupyter lab
```

`notebooks/metrics_analysis.ipynb` 열기:

**분석 예제:**

1. **트래픽 패턴 분석**
   - 시간대별 요청 분포
   - 피크 시간 식별
   - 주중/주말 패턴

2. **성능 분석**
   - 응답 시간 분포
   - 느린 엔드포인트 식별
   - 병목 지점 분석

3. **에러 분석**
   - 에러 타입별 분포
   - 에러 발생 패턴
   - 상관관계 분석

4. **비즈니스 분석**
   - 사용자 성장 추세
   - 거래 패턴
   - 매출 분석

### Pandas 데이터 분석 예제

```python
import pandas as pd
import matplotlib.pyplot as plt

# 데이터 로드
df = pd.read_csv('analytics/data/http_metrics_20250122_120000.csv',
                 parse_dates=['timestamp'])

# 요청률 시계열
request_rate = df[df['metric'] == 'request_rate']
plt.figure(figsize=(15, 5))
plt.plot(request_rate['timestamp'], request_rate['value'])
plt.title('Request Rate Over Time')
plt.xlabel('Time')
plt.ylabel('Requests/sec')
plt.show()

# 통계 요약
print(request_rate['value'].describe())

# 이상치 탐지 (Z-score)
from scipy import stats
z_scores = stats.zscore(request_rate['value'])
anomalies = request_rate[abs(z_scores) > 3]
print(f"Anomalies detected: {len(anomalies)}")
```

## 모니터링 모범 사례

### 1. 메트릭 명명 규칙

```
<namespace>_<name>_<unit>_<suffix>

예시:
multiweb_http_requests_total
multiweb_product_creation_duration_seconds
multiweb_active_users_count
```

### 2. 적절한 메트릭 타입 선택

- **Counter**: 증가만 하는 값 (총 요청 수)
- **Gauge**: 증감하는 값 (활성 사용자 수)
- **Histogram**: 분포 (응답 시간)
- **Summary**: 요약 통계 (중앙값, 백분위수)

### 3. 카디널리티 관리

```python
# 나쁜 예: 높은 카디널리티
http_requests_total{user_id="12345"}  # 수백만 개의 라벨

# 좋은 예: 낮은 카디널리티
http_requests_total{path="/api/v1/products", status="200"}
```

### 4. 샘플링 전략

- 모든 요청 추적하지 말기
- 에러 요청은 100% 샘플링
- 정상 요청은 1-10% 샘플링

## 문제 해결 시나리오

### 시나리오 1: API 응답 시간 증가

**단계:**
1. Grafana에서 latency 대시보드 확인
2. 느린 엔드포인트 식별
3. Tempo에서 해당 트레이스 확인
4. 병목 지점 파악 (DB 쿼리? 외부 API?)
5. 로그에서 추가 정보 수집
6. 최적화 적용

**쿼리:**
```promql
# 느린 엔드포인트 찾기
topk(5,
  histogram_quantile(0.95,
    rate(http_request_duration_seconds_bucket[5m])
  )
) by (path)
```

### 시나리오 2: 에러율 급증

**단계:**
1. 알림 수신
2. Prometheus에서 에러율 확인
3. Loki에서 에러 로그 검색
4. 에러 패턴 분석 (특정 엔드포인트? 특정 시간?)
5. 트레이스에서 에러 위치 확인
6. 수정 및 배포

**쿼리:**
```logql
# 에러 로그 검색
{app="multiweb-api"} | json | level="error" | line_format "{{.timestamp}} {{.path}} {{.error}}"
```

### 시나리오 3: 리소스 부족

**단계:**
1. 메트릭에서 리소스 사용률 확인
2. HPA 동작 확인
3. Pod 로그 확인 (OOM killer?)
4. 리소스 limit 조정 또는 최적화

**쿼리:**
```promql
# 메모리 사용률
100 * container_memory_working_set_bytes{pod=~"multiweb-api.*"}
/ container_spec_memory_limit_bytes
```

## 결론

효과적인 모니터링은 시스템의 안정성과 성능을 보장하는 핵심입니다. 이 가이드를 활용하여:

1. 시스템 상태를 실시간으로 파악
2. 문제를 조기에 발견하고 대응
3. 데이터 기반 의사결정
4. 지속적인 성능 개선

모니터링 데이터를 정기적으로 분석하고, 알림 규칙을 지속적으로 개선하며, 팀과 인사이트를 공유하세요.
