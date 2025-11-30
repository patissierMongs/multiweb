# MultiWeb 배포 가이드

이 문서는 MultiWeb 마켓플레이스 애플리케이션을 로컬 및 클러스터 환경에 배포하는 방법을 설명합니다.

## 목차

1. [사전 요구사항](#사전-요구사항)
2. [로컬 개발 환경 (Docker Compose)](#로컬-개발-환경-docker-compose)
3. [Kubernetes 클러스터 배포](#kubernetes-클러스터-배포)
4. [모니터링 설정](#모니터링-설정)
5. [부하 테스트 실행](#부하-테스트-실행)
6. [트러블슈팅](#트러블슈팅)

## 사전 요구사항

### 필수 도구

- **Docker**: 20.10 이상
- **Docker Compose**: 2.0 이상
- **Python**: 3.12 이상
- **kubectl**: 1.28 이상 (Kubernetes 배포 시)
- **Kind** 또는 **Minikube**: 로컬 Kubernetes 클러스터용
- **Helm**: 3.0 이상 (선택사항)

### 설치 확인

```bash
docker --version
docker-compose --version
python --version
kubectl version --client
```

## 로컬 개발 환경 (Docker Compose)

가장 빠르게 시작하는 방법입니다. 모든 서비스가 Docker Compose로 실행됩니다.

### 1. 환경 변수 설정

`.env` 파일을 생성합니다:

```bash
cp app/.env.example app/.env
# 필요한 경우 값을 수정합니다
```

### 2. 전체 스택 시작

```bash
docker-compose up -d
```

이 명령은 다음 서비스를 시작합니다:
- PostgreSQL (포트 5432)
- Redis (포트 6379)
- FastAPI 애플리케이션 (포트 8000)
- Prometheus (포트 9090)
- Grafana (포트 3000)
- Loki (포트 3100)
- Tempo (포트 3200, 4317, 4318)
- Nginx (포트 80, 443)

### 3. 서비스 확인

```bash
# 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f api

# 헬스 체크
curl http://localhost:8000/health
```

### 4. 접속 정보

- **API 문서**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **API**: http://localhost:80 (Nginx를 통해)

### 5. 중지 및 정리

```bash
# 중지
docker-compose down

# 볼륨까지 삭제
docker-compose down -v
```

## Kubernetes 클러스터 배포

프로덕션과 유사한 환경에서 테스트하려면 Kubernetes를 사용합니다.

### 방법 1: 자동 설정 스크립트 사용

```bash
cd scripts
chmod +x setup-k8s.sh
./setup-k8s.sh
```

스크립트가 자동으로:
1. Kubernetes 클러스터 생성 (Kind 또는 Minikube)
2. Nginx Ingress Controller 설치
3. Metrics Server 설치
4. 애플리케이션 및 모든 의존성 배포
5. 모니터링 스택 배포

### 방법 2: 수동 배포

#### 1. Kubernetes 클러스터 생성

**Kind 사용:**

```bash
# Kind 설치 (macOS)
brew install kind

# 클러스터 생성
kind create cluster --name multiweb --config - <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
  - containerPort: 443
    hostPort: 443
- role: worker
- role: worker
EOF
```

**Minikube 사용:**

```bash
# Minikube 설치 (macOS)
brew install minikube

# 클러스터 시작
minikube start --cpus=4 --memory=8192 --disk-size=40g
```

#### 2. Nginx Ingress Controller 설치

**Kind:**

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
```

**Minikube:**

```bash
minikube addons enable ingress
```

#### 3. 네임스페이스 및 리소스 생성

```bash
# 기본 리소스
kubectl apply -f k8s/base/namespace.yaml
kubectl apply -f k8s/base/configmap.yaml
kubectl apply -f k8s/base/secret.yaml

# 데이터베이스
kubectl apply -f k8s/base/postgres.yaml
kubectl apply -f k8s/base/redis.yaml

# 데이터베이스가 준비될 때까지 대기
kubectl wait --for=condition=ready pod -l app=postgres -n multiweb --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n multiweb --timeout=300s
```

#### 4. 애플리케이션 빌드 및 배포

```bash
# Docker 이미지 빌드
cd app
docker build -t multiweb-api:latest .

# 이미지를 클러스터에 로드
# Kind:
kind load docker-image multiweb-api:latest --name multiweb

# Minikube:
minikube image load multiweb-api:latest

cd ..

# 애플리케이션 배포
kubectl apply -f k8s/base/api.yaml
kubectl apply -f k8s/ingress/ingress.yaml

# 준비될 때까지 대기
kubectl wait --for=condition=ready pod -l app=multiweb-api -n multiweb --timeout=300s
```

#### 5. 모니터링 스택 배포

```bash
# Prometheus
kubectl apply -f k8s/monitoring/prometheus.yaml

# Grafana
kubectl apply -f k8s/monitoring/grafana.yaml

# Loki
kubectl apply -f k8s/logging/loki.yaml

# Promtail
kubectl apply -f k8s/logging/promtail.yaml

# Tempo
kubectl apply -f k8s/monitoring/tempo.yaml
```

#### 6. 서비스 접속

```bash
# 포트 포워딩
kubectl port-forward svc/multiweb-api-service 8000:8000 -n multiweb &
kubectl port-forward svc/grafana 3000:3000 -n multiweb &
kubectl port-forward svc/prometheus 9090:9090 -n multiweb &

# 또는 Ingress 사용
# /etc/hosts에 추가:
# 127.0.0.1 multiweb.local

# 접속: http://multiweb.local
```

## 모니터링 설정

### Grafana 대시보드

1. Grafana 접속: http://localhost:3000
2. 로그인: admin/admin
3. 데이터 소스는 자동으로 프로비저닝됩니다:
   - Prometheus
   - Loki
   - Tempo

### 대시보드 가져오기

```bash
# 사전 구성된 대시보드 확인
ls analytics/dashboards/

# 수동으로 가져오기:
# Grafana UI > Dashboards > Import > Upload JSON file
```

### 주요 메트릭

- **HTTP 요청률**: `rate(http_requests_total[5m])`
- **에러율**: `rate(http_requests_total{status=~"5.."}[5m])`
- **응답 시간 (P95)**: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
- **활성 사용자**: `multiweb_active_users`

## 부하 테스트 실행

### Locust 부하 테스트

```bash
# 의존성 설치
cd tests/locust
pip install -r requirements.txt

# Locust 시작 (웹 UI)
locust -f marketplace_load.py --host=http://localhost:8000

# 브라우저에서 http://localhost:8089 접속

# 또는 CLI 모드로 실행
locust -f marketplace_load.py --host=http://localhost:8000 \
  --users 100 --spawn-rate 10 --run-time 5m --headless
```

### 공격 시뮬레이션

```bash
cd tests/attacks
pip install -r requirements.txt

# 모든 공격 시뮬레이션 실행
python simulate_attacks.py

# 특정 공격만 실행하려면 스크립트를 수정하세요
```

## 데이터 수집 및 분석

### 메트릭 수집

```bash
cd analytics/collectors
pip install -r requirements.txt

# 메트릭 수집
python collect_metrics.py

# 수집된 데이터는 analytics/data/ 디렉토리에 저장됩니다
```

### Jupyter Notebook 분석

```bash
cd analytics
pip install jupyterlab pandas numpy matplotlib seaborn

# Jupyter Lab 시작
jupyter lab

# notebooks/metrics_analysis.ipynb 열기
```

## 유용한 명령어

### Kubernetes

```bash
# Pod 상태 확인
kubectl get pods -n multiweb

# 로그 확인
kubectl logs -f deployment/multiweb-api -n multiweb

# Pod 내부 접속
kubectl exec -it deployment/multiweb-api -n multiweb -- /bin/bash

# 리소스 사용량 확인
kubectl top pods -n multiweb
kubectl top nodes

# HPA 상태 확인
kubectl get hpa -n multiweb

# 이벤트 확인
kubectl get events -n multiweb --sort-by='.lastTimestamp'
```

### Docker Compose

```bash
# 특정 서비스 재시작
docker-compose restart api

# 특정 서비스 로그
docker-compose logs -f api

# 리소스 사용량
docker stats

# 네트워크 확인
docker-compose exec api ping postgres
```

## 트러블슈팅

### 문제: Pod가 Pending 상태

```bash
# 원인 확인
kubectl describe pod <pod-name> -n multiweb

# 주로 리소스 부족이 원인
# 해결: 노드 추가 또는 리소스 요청 줄이기
```

### 문제: 이미지 Pull 실패

```bash
# 로컬 이미지를 클러스터에 다시 로드
docker build -t multiweb-api:latest app/
kind load docker-image multiweb-api:latest --name multiweb
```

### 문제: 데이터베이스 연결 실패

```bash
# PostgreSQL Pod 확인
kubectl get pods -l app=postgres -n multiweb

# 로그 확인
kubectl logs -l app=postgres -n multiweb

# 연결 테스트
kubectl exec -it deployment/multiweb-api -n multiweb -- \
  python -c "from app.core.database import engine; print('OK')"
```

### 문제: Prometheus가 메트릭을 수집하지 않음

```bash
# Service Discovery 확인
kubectl get servicemonitors -n multiweb

# Prometheus targets 확인
kubectl port-forward svc/prometheus 9090:9090 -n multiweb
# 브라우저: http://localhost:9090/targets

# Pod annotations 확인
kubectl get pods -n multiweb -o jsonpath='{.items[*].metadata.annotations}'
```

### 문제: Grafana에 데이터가 없음

```bash
# 데이터 소스 확인
# Grafana UI > Configuration > Data Sources

# Prometheus 연결 테스트
kubectl exec -it deployment/grafana -n multiweb -- \
  curl http://prometheus:9090/api/v1/query?query=up
```

## 보안 고려사항

### 프로덕션 배포 전 체크리스트

- [ ] `k8s/base/secret.yaml`의 모든 비밀 값 변경
- [ ] HTTPS/TLS 인증서 설정
- [ ] Rate limiting 설정 검토
- [ ] Network Policies 적용
- [ ] RBAC 권한 최소화
- [ ] Pod Security Standards 적용
- [ ] 이미지 취약점 스캔
- [ ] Secrets를 환경 변수 대신 Vault 사용 고려

## 다음 단계

1. **모니터링 대시보드 커스터마이징**
   - 비즈니스 메트릭 추가
   - 알림 규칙 설정

2. **CI/CD 파이프라인 구축**
   - GitHub Actions
   - ArgoCD for GitOps

3. **고급 기능 추가**
   - Service Mesh (Istio/Linkerd)
   - Distributed Tracing 강화
   - Log aggregation 개선

4. **성능 최적화**
   - 데이터베이스 튜닝
   - 캐싱 전략 개선
   - CDN 통합

## 참고 자료

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Grafana Tutorials](https://grafana.com/tutorials/)
