.PHONY: up down logs restart rebuild-backend test test-local shell-backend spark-submit db-reset

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

restart:
	docker compose down && docker compose up -d

rebuild-backend:
	docker compose up -d --build backend

test:
	docker compose exec backend pytest /app/tests/ -v

test-local:
	cd backend && python -m pytest tests/ -v --tb=short

shell-backend:
	docker compose exec backend bash

spark-submit:
	docker compose exec spark-master spark-submit /opt/spark-apps/bronze_consumer.py

db-reset:
	docker compose exec postgres psql -U admin -d cryptopulse -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	@echo "Database reset complete. Restart backend to re-create tables."

db-init:
	docker compose exec postgres psql -U admin -d cryptopulse -c "CREATE SCHEMA IF NOT EXISTS silver; CREATE SCHEMA IF NOT EXISTS gold;"
	@echo "Database schemas (silver, gold) initialized successfully."
