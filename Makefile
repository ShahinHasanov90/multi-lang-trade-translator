.PHONY: install run test lint clean docker-build docker-run

install:
	pip install -r requirements.txt

run:
	uvicorn src.translator.api:app --reload --host 0.0.0.0 --port 8000

test:
	python -m pytest tests/ -v

lint:
	python -m flake8 src/ tests/
	python -m mypy src/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache dist build *.egg-info

docker-build:
	docker build -t trade-translator .

docker-run:
	docker run -p 8000:8000 trade-translator
