FROM apache/airflow:2.7.3

# Install pip packages as airflow user
USER airflow
RUN pip install --no-cache-dir requests python-dotenv dbt-core==1.7.0 dbt-postgres==1.7.0

# Install latest Docker CLI binary (static build)
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-27.4.1.tgz \
       | tar xz --strip-components=1 -C /usr/local/bin docker/docker \
    && apt-get remove -y curl \
    && rm -rf /var/lib/apt/lists/*

# Ensure root can find airflow and all packages installed by airflow user
ENV PATH="/home/airflow/.local/bin:${PATH}"
ENV PYTHONPATH="/home/airflow/.local/lib/python3.8/site-packages:${PYTHONPATH}"
