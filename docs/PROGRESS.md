# 진행 기록

[English](PROGRESS.en.md) | **한국어**

## 최종 목표

중고거래 마켓플레이스 API(Application Programming Interface)를 직접 만들고, 그 위에 실제 운영 환경과 비슷한 DevOps 스택을 올려 다음을 연습하는 것이 목표입니다.

- 메트릭·로그·분산 트레이싱을 모으는 관측(observability) 스택 구성
- Kubernetes에서 자동 확장과 롤링 업데이트 운영
- 부하 테스트와 공격 시뮬레이션으로 병목과 방어 동작 확인
- 수집한 운영 데이터를 Jupyter로 분석

## 현재 구현 상태

2026-09-27에 코드를 직접 읽고, 로컬 PostgreSQL 16·Redis에 연결해 API를 실행하며 확인했습니다. 기존 문서나 커밋 메시지의 설명이 아니라 코드와 실행 결과를 근거로 적었습니다.

| 기능 | 상태 | 근거 코드 | 확인 내용 |
|---|---|---|---|
| 회원가입·로그인, JWT(JSON Web Token) 발급 | 구현됨 | `app/api/endpoints/auth.py`, `app/core/security.py` | 실행해서 가입·로그인·토큰 발급 확인 |
| 토큰 갱신(refresh) API | 미구현 | `app/core/security.py` | 리프레시 토큰은 발급하지만 갱신 엔드포인트가 없음 |
| 내 정보 조회·수정 API | 미구현 | `app/schemas/user.py` | `UserUpdate` 스키마만 있고 엔드포인트 없음 |
| 상품 목록·검색·필터·페이지 나누기 | 구현됨 | `app/api/endpoints/products.py` `list_products` | 실행해서 확인 |
| 상품 상세 조회(조회수 증가) | 구현됨 | `products.py` `get_product` | 실행해서 확인 |
| 상품 등록·수정 | 부분 구현 | `products.py` `create_product`, `update_product` | DB(Database)에는 저장되지만 응답 직렬화에서 `DetachedInstanceError`가 나서 HTTP(HyperText Transfer Protocol) 500을 반환 |
| 상품 삭제(소프트 삭제, 판매자만) | 구현됨 | `products.py` `delete_product` | 다른 사용자의 삭제 요청이 403인 것 확인 |
| 이미지 업로드 | 미구현 | `app/core/config.py` (`UPLOAD_DIR` 설정만 존재) | 업로드 엔드포인트 없음. 상품 등록 시 이미지 URL(Uniform Resource Locator)만 받음 |
| 거래 생성·조회 | 구현됨 | `app/api/endpoints/transactions.py` | 실행해서 확인 |
| 거래 상태 변경(확정·완료·취소) | 미구현 | `app/models/transaction.py` | 상태 값은 모델에 있으나 변경 API 없음 |
| 메시지 보내기·목록 | 구현됨 | `app/api/endpoints/messages.py` | 실행해서 확인 |
| 실시간 채팅(WebSocket) | 미구현 | `app/requirements.txt` | `websockets` 패키지만 있고 WebSocket 라우트 없음 |
| 리뷰 | 부분 구현 | `app/models/transaction.py` `Review` | 테이블 모델만 있고 API 없음 |
| 결제 시뮬레이션 | 미구현 | - | 결제 처리 코드 없음 (`payment_method` 필드만 존재) |
| 헬스 체크(`/health`, `/health/ready`, `/health/live`) | 구현됨 | `app/api/endpoints/health.py` | 실행해서 확인 |
| Prometheus 메트릭 `/metrics` | 구현됨 | `app/main.py` (Instrumentator) | 실행해서 확인 |
| 비즈니스 메트릭(`multiweb_products_created_total` 등) | 미구현 | `analytics/collectors/collect_metrics.py` | 수집기는 조회하지만 앱에서 해당 메트릭을 만들지 않음 |
| 구조화 로그(structlog JSON) | 구현됨 | `app/main.py` | 실행 로그에서 확인 |
| OpenTelemetry 분산 트레이싱 | 미구현 | `app/core/config.py` (`OTEL_*` 설정만 존재) | 앱에 계측 코드 없음. Tempo 배포 파일만 있음 |
| 앱 내부 요청 속도 제한 | 미구현 | `app/core/config.py` (`RATE_LIMIT_*` 설정만 존재) | 앱에서 사용하지 않음 |
| Nginx 요청 속도 제한 | 구현됨 (실행 미확인) | `docker/nginx.conf` | 설정 파일로만 확인 |
| DB 초기화·데모 데이터 | 구현됨 | `scripts/init_db.py` | `PYTHONPATH=.`로 실행해서 확인 |
| DB 마이그레이션(Alembic) | 미구현 | `app/requirements.txt` | 패키지만 있고 마이그레이션 디렉터리 없음 |
| Docker Compose 스택 | 부분 구현 (실행 미확인) | `docker-compose.yml`, `app/Dockerfile` | 아래 "알려진 문제" 참고 |
| Kubernetes 매니페스트(Deployment, HPA(Horizontal Pod Autoscaler), Ingress, 모니터링·로깅) | 구현됨 (실행 미확인) | `k8s/` | 클러스터가 없어 적용해 보지 못함 |
| Helm 차트 | 미구현 | - | `helm/` 디렉터리 없음 |
| Grafana 대시보드 | 미구현 | `docker-compose.yml` | `analytics/dashboards`를 마운트하지만 디렉터리가 없음 |
| Locust 부하 테스트 | 구현됨 | `tests/locust/marketplace_load.py` | 5명·12초 헤드리스 실행, 123건 요청 실패 0건 |
| 공격 시뮬레이션 | 구현됨 (실행 미확인) | `tests/attacks/simulate_attacks.py` | 코드로만 확인 |
| 메트릭 수집·분석 노트북 | 구현됨 (실행 미확인) | `analytics/collectors/collect_metrics.py`, `analytics/notebooks/metrics_analysis.ipynb` | Prometheus가 없어 실행하지 못함 |
| 자동 테스트(단위·통합) | 미구현 | `tests/` | pytest 테스트 파일 없음 |

### 알려진 문제

- **API 컨테이너 모듈 경로**: `app/Dockerfile`은 `app/` 디렉터리 내용을 `/app`에 복사하고 `uvicorn app.main:app`을 실행합니다. 코드는 `from app.core ...` 형태로 가져오므로 컨테이너 안에는 `/app/app` 패키지가 필요한데 없습니다. `docker-compose.yml`의 `./app:/app` 마운트도 같은 구조입니다. Docker 데몬이 없어 실제 실행은 못 했고 코드를 읽어 판단했습니다.
- **`quickstart.sh`의 초기화 경로**: `docker-compose exec api python /app/../scripts/init_db.py`는 컨테이너에 마운트되지 않은 `/scripts`를 가리킵니다.
- **상품 등록·수정 500 오류**: 위 표 참고.
- **passlib 경고**: bcrypt 4.2.0과 passlib 1.7.4 조합에서 `module 'bcrypt' has no attribute '__about__'` 경고가 출력됩니다. 해시와 검증은 정상 동작합니다.
- **ruff**: `ruff check app scripts tests analytics` 결과 사용하지 않는 import 12건이 있습니다.
- **`email-validator` 누락**: 이번 작업에서 `app/requirements.txt`에 추가했습니다. 없으면 `EmailStr` 때문에 앱이 시작되지 않습니다.

## 작업 이력

`git log`에서 뽑았으며 시간은 한국 표준시(KST, Asia/Seoul)로 바꿔 적었습니다. 저장된 오프셋이 +0000인 커밋은 9시간을 더했습니다.

| 날짜 (KST) | 커밋 | 내용 |
|---|---|---|
| 2024-10-23 11:02 | `8fa38ba` | 저장소 생성 |
| 2025-11-22 23:20 | `3717990` | FastAPI 앱, Docker Compose, Kubernetes 매니페스트, Locust·공격 시뮬레이션, 분석 수집기·노트북, 아키텍처·배포·모니터링 문서 추가 |
| 2025-11-23 12:06 | `3e19650` | 누락된 `__init__.py` 추가, Pydantic v2 설정 수정, Compose용 Prometheus·Promtail 설정 분리, `init_db.py`·`quickstart.sh`·`test-api.sh` 추가, 검토 리포트 작성 |
| 2025-11-30 22:49 | `639d09c` | 위 작업 브랜치를 main에 병합 (PR(Pull Request) #1) |
| 2026-09-27 | 이번 작업 | `email-validator` 의존성 추가, README 한국어·영어 분리와 스크린샷 추가, 진행 기록 작성 |
