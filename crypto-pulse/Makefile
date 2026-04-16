.PHONY: up down logs restart

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

shell-backend:
	docker compose exec backend bash

spark-submit:
	docker compose exec spark-master spark-submit /opt/spark-apps/bronze_consumer.py
