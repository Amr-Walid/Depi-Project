import os
import shutil

base_path = r"c:\Users\SMART HOME\Documents\فايلات رواد\project\crypto-pulse"
os.chdir(base_path)

dirs_to_create = [
    ".github/workflows", "backend/app/routers", "backend/app/models", "backend/tests", 
    "dags", "docs", "notebooks", "processing/spark", "processing/dbt/models/gold", 
    "processing/dbt/tests", "data/historical"
]

for d in dirs_to_create:
    os.makedirs(d, exist_ok=True)

moves = [
    ("ingestion/historical/historical_fetcher.py", "ingestion/historical_fetcher.py"),
    ("ingestion/producers/producer_binance.py", "ingestion/producer_binance.py"),
    ("ingestion/producers/producer_coingecko.py", "ingestion/producer_coingecko.py"),
    ("infra/docker-compose.yml", "docker-compose.yml"),
    ("infra/Makefile", "Makefile")
]

for src, dst in moves:
    if os.path.exists(src):
        if os.path.exists(dst):
            os.remove(dst)
        shutil.move(src, dst)

dirs_to_delete = ["ingestion/historical", "ingestion/producers", "infra"]
for d in dirs_to_delete:
    if os.path.exists(d):
        shutil.rmtree(d)

files_to_touch = [
    ".github/workflows/ci-cd.yml", "backend/app/__init__.py", "backend/app/main.py", 
    "dags/etl_pipeline_dag.py", "docs/architecture.png", "docs/project_proposal.pdf", 
    "ingestion/producer_news.py", "notebooks/01-data-exploration.ipynb", 
    "processing/spark/bronze_consumer.py", "processing/spark/silver_processor.py", 
    "processing/dbt/dbt_project.yml", ".dockerignore", ".env.example", 
    "data/historical/.gitkeep"
]

for f in files_to_touch:
    with open(f, 'a'): pass
