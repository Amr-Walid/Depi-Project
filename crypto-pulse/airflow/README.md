# Apache Airflow Service Configuration

This directory contains the custom Dockerfile used to build the orchestration runner image for **Apache Airflow** (v2.7.3). 

---

## Directory Structure

```
airflow/
└── Dockerfile       # Custom Dockerfile with Docker CLI and dbt-core
```

---

## Architecture Design

Running Apache Spark and PySpark libraries directly within Airflow would require a massive container image (~2GB+) and heavy JVM resource usage. To keep Airflow lightweight and highly responsive, this project uses a **Docker-in-Docker socket-sharing architecture**:

```
┌─────────────────────────────────┐
│     Airflow Scheduler Container │
│ ┌─────────────────────────────┐ │
│ │ Docker CLI (Static Binary)  │ │
│ └──────────────┬──────────────┘ │
└────────────────┼────────────────┘
                 │
      Calls docker commands via
    /var/run/docker.sock mount
                 │
                 ▼
┌─────────────────────────────────┐
│     Docker Daemon (Host OS)     │
└────────────────┬────────────────┘
                 │
   Triggers command execution inside
                 ▼
┌─────────────────────────────────┐
│        spark-master Container   │
│ ┌─────────────────────────────┐ │
│ │ spark-submit jobs/sync_...  │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

1.  **Shared Socket**: The Airflow Scheduler container mounts the host's `/var/run/docker.sock`.
2.  **Docker CLI**: The Docker CLI is installed inside the Airflow image.
3.  **Command Delegation**: When a DAG task needs to execute a Spark job, it runs a command like:
    ```bash
    docker exec spark-master spark-submit /opt/spark/jobs/some_job.py
    ```
4.  **No JVM Overhead**: Airflow operates purely as a scheduling brain; the actual heavy lifting is done in the dedicated `spark-master` and `spark-worker` containers.

---

## Dockerfile Specifications

### Base Image
*   `apache/airflow:2.7.3`

### Installed Python Packages (under `airflow` user)
Installed to support dbt execution and metadata queries:
*   `requests` — For REST API calls.
*   `python-dotenv` — For managing environment credentials.
*   `dbt-core==1.7.0` — To run analytic transformation pipelines.
*   `dbt-postgres==1.7.0` — DBT adapter to connect and sync with PostgreSQL/Supabase.

### System Additions (under `root` user)
*   **Docker CLI `27.4.1` (Static Binary)**: Fetched from Docker's official static releases and placed in `/usr/local/bin`.
*   **PATH Adjustments**: Sets environment variables `PATH` and `PYTHONPATH` so the container system can locate python packages installed under the `airflow` user's home directory.
