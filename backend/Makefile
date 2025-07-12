# FluxNews Backend Makefile

.PHONY: help install dev test clean run migrate lint format

# 기본 타겟
help:
	@echo "사용 가능한 명령어:"
	@echo "  make install    - 의존성 설치"
	@echo "  make dev        - 개발 환경 설정"
	@echo "  make test       - 테스트 실행"
	@echo "  make test-unit  - 유닛 테스트만 실행"
	@echo "  make test-api   - API 테스트만 실행"
	@echo "  make coverage   - 테스트 커버리지 리포트"
	@echo "  make lint       - 코드 린팅"
	@echo "  make format     - 코드 포맷팅"
	@echo "  make run        - 개발 서버 실행"
	@echo "  make clean      - 캐시 및 임시 파일 정리"

# 의존성 설치
install:
	pip install -r requirements.txt

# 개발 환경 설정
dev:
	pip install -r requirements-dev.txt
	pre-commit install

# 전체 테스트 실행
test:
	pytest

# 유닛 테스트만 실행
test-unit:
	pytest -m unit

# API 테스트만 실행
test-api:
	pytest -m api

# 서비스 테스트만 실행
test-service:
	pytest -m service

# 성능 테스트 실행
test-performance:
	pytest -m performance -v

# 특정 파일 테스트
test-file:
	@read -p "테스트 파일 경로: " file; \
	pytest $$file -v

# 테스트 커버리지
coverage:
	pytest --cov=app --cov-report=html --cov-report=term
	@echo "HTML 커버리지 리포트: htmlcov/index.html"

# 린팅
lint:
	flake8 app tests
	mypy app
	pylint app

# 코드 포맷팅
format:
	black app tests
	isort app tests

# 포맷 체크
format-check:
	black --check app tests
	isort --check-only app tests

# 개발 서버 실행
run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 서버 실행
run-prod:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Redis 시작 (macOS)
redis-start:
	brew services start redis

# Redis 중지 (macOS)
redis-stop:
	brew services stop redis

# 데이터베이스 마이그레이션
migrate:
	alembic upgrade head

# 마이그레이션 생성
migrate-create:
	@read -p "마이그레이션 이름: " name; \
	alembic revision --autogenerate -m "$$name"

# 캐시 및 임시 파일 정리
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

# 보안 검사
security:
	bandit -r app
	safety check

# 의존성 업데이트 확인
deps-check:
	pip list --outdated

# 도커 빌드
docker-build:
	docker build -t fluxnews-backend .

# 도커 실행
docker-run:
	docker run -p 8000:8000 --env-file .env fluxnews-backend

# 전체 검증 (CI/CD용)
ci: format-check lint test security