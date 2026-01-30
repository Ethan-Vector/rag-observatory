.PHONY: dev test lint fmt

dev:
	uvicorn rag_observatory.api:app --host 0.0.0.0 --port 8090 --reload

test:
	pytest -q

lint:
	ruff check .
	mypy src

fmt:
	ruff format .
