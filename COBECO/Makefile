.PHONY: run seed test lint
run:
	python -m uvicorn backend.main:create_app --factory --host 0.0.0.0 --port 8000
seed:
	python -m backend.seed
test:
	python -m pytest --cov --cov-report=term-missing --cov-report=xml
lint:
	python -m ruff check backend
