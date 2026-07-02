# 📖 Project Documentation Directory

This directory contains the central architectural assets, design documents, milestone guidelines, and engineering logs for **Crypto-Pulse**.

---

## 📂 Directory Structure

```
docs/
├── tasks/                       # Milestone checklists and task lists
├── architecture.png             # System architecture diagram (Lucidchart)
├── architecture_full_pipeline.png # Pipeline stages visualization
├── DEPLOYMENT_RESOLUTION_LOG.md # Production logs and resolution details
├── LINUX_QUICKSTART.md          # Quickstart guide for running on Linux/WSL
├── SPARK_PIPELINE_OPTIMIZATION.md # Tuning logs for Spark job memory usage
├── WALKTHROUGH.md               # End-to-end pipeline run guide
├── milestone3_backend.md        # Specs for FastAPI server integrations
└── project_proposal.pdf         # Initial project proposal document
```

---

## 📝 Document Index & Directory Reference

Here is a summary of the major documentation files and guides available:

| Document / Asset | Description | Format |
| :--- | :--- | :---: |
| [architecture_full_pipeline.png](file:///C:/Users/Kemosky/./.gemini/antigravity/scratch/Depi-Project-92cdc3272ac4d8d1cd4a8c199c95269eed3e43bc/crypto-pulse/docs/architecture_full_pipeline.png) | End-to-end visual flow showing Binance WS, Kafka, Spark, ADLS, Postgres, dbt, and the FastAPI backend. | Image |
| [SPARK_PIPELINE_OPTIMIZATION.md](file:///C:/Users/Kemosky/./.gemini/antigravity/scratch/Depi-Project-92cdc3272ac4d8d1cd4a8c199c95269eed3e43bc/crypto-pulse/docs/SPARK_PIPELINE_OPTIMIZATION.md) | Details how Spark streaming memory was tuned, driver/executor configurations, checkpointing, and Azure ADLS Gen2 speedup steps. | Markdown |
| [DEPLOYMENT_RESOLUTION_LOG.md](file:///C:/Users/Kemosky/./.gemini/antigravity/scratch/Depi-Project-92cdc3272ac4d8d1cd4a8c199c95269eed3e43bc/crypto-pulse/docs/DEPLOYMENT_RESOLUTION_LOG.md) | Documentation tracking database migration to Supabase Cloud, custom PySpark SSL JDBC integrations, and resolution of schema mismatches. | Markdown |
| [WALKTHROUGH.md](file:///C:/Users/Kemosky/./.gemini/antigravity/scratch/Depi-Project-92cdc3272ac4d8d1cd4a8c199c95269eed3e43bc/crypto-pulse/docs/WALKTHROUGH.md) | Explains the complete execution workflow sequence for testing, building, and verifying the ingestion and processing layers. | Markdown |
| [LINUX_QUICKSTART.md](file:///C:/Users/Kemosky/./.gemini/antigravity/scratch/Depi-Project-92cdc3272ac4d8d1cd4a8c199c95269eed3e43bc/crypto-pulse/docs/LINUX_QUICKSTART.md) | Quickstart steps for setting up WSL2 environments, starting Docker containers, and managing credentials. | Markdown |
| [milestone3_backend.md](file:///C:/Users/Kemosky/./.gemini/antigravity/scratch/Depi-Project-92cdc3272ac4d8d1cd4a8c199c95269eed3e43bc/crypto-pulse/docs/milestone3_backend.md) | Specific functional requirements, tables configurations, endpoints, and test coverage for the FastAPI server. | Markdown |
| [project_proposal.pdf](file:///C:/Users/Kemosky/./.gemini/antigravity/scratch/Depi-Project-92cdc3272ac4d8d1cd4a8c199c95269eed3e43bc/crypto-pulse/docs/project_proposal.pdf) | The official project submission outline, listing goals, timelines, data schemas, and team roles. | PDF |
