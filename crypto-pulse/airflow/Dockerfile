FROM apache/airflow:2.7.3

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends docker.io \
    && rm -rf /var/lib/apt/lists/*
# Allow airflow user to use docker
RUN usermod -aG docker airflow || true
USER airflow
