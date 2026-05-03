FROM apache/airflow:2.7.3

# Install pip packages as airflow user
USER airflow
RUN pip install --no-cache-dir requests python-dotenv dbt-core==1.7.0 dbt-postgres==1.7.0

# Install Docker CLI as root
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends docker.io \
    && rm -rf /var/lib/apt/lists/*

# Ensure root can find airflow and all packages installed by airflow user
ENV PATH="/home/airflow/.local/bin:${PATH}"
ENV PYTHONPATH="/home/airflow/.local/lib/python3.8/site-packages:${PYTHONPATH}"
