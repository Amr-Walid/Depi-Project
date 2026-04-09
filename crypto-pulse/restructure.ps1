# Restructure Directories
New-Item -ItemType Directory -Force -Path ".github\workflows", "backend\app\routers", "backend\app\models", "backend\tests", "dags", "docs", "notebooks", "processing\spark", "processing\dbt\models\gold", "processing\dbt\tests", "data\historical"

# Move ingestion components
Move-Item -Path "ingestion\historical\historical_fetcher.py" -Destination "ingestion\" -Force
Move-Item -Path "ingestion\producers\producer_binance.py" -Destination "ingestion\" -Force
Move-Item -Path "ingestion\producers\producer_coingecko.py" -Destination "ingestion\" -Force

# Delete flattened old spaces
Remove-Item -Path "ingestion\historical" -Recurse -Force
Remove-Item -Path "ingestion\producers" -Recurse -Force

# Move the infra stuff
Move-Item -Path "infra\docker-compose.yml" -Destination "." -Force
Move-Item -Path "infra\Makefile" -Destination "." -Force
Remove-Item -Path "infra" -Recurse -Force

# Create Placeholders
$files = @(".github\workflows\ci-cd.yml", "backend\app\__init__.py", "backend\app\main.py", "dags\etl_pipeline_dag.py", "docs\architecture.png", "docs\project_proposal.pdf", "ingestion\producer_news.py", "notebooks\01-data-exploration.ipynb", "processing\spark\bronze_consumer.py", "processing\spark\silver_processor.py", "processing\dbt\dbt_project.yml", ".dockerignore", ".env.example", "data\historical\.gitkeep")
foreach ($file in $files) {
    New-Item -ItemType File -Force -Path $file
}
