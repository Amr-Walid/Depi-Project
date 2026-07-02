# ⚡ Spark-Apps Service Environment

This directory contains the custom Docker configuration used to build the **Apache Spark 3.5.0** cluster images. 

---

## 📂 Directory Structure

```
spark-apps/
├── Dockerfile.spark     # Multi-dependency Spark cluster image manifest
├── .env.example         # Template file for Spark-specific properties
└── bronze_consumer.py   # Ingestion driver reference script
```

---

## 🏗️ Preloaded Dependency Architecture

Using standard PySpark CLI arguments like `--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0` in a containerized environment causes Spark to attempt to download the dependencies from Maven Central on *every container startup*. This introduces:
1.  **Startup Delays**: Long wait times (~30-60s) before scripts begin executing.
2.  **Network Failure Points**: Builds fail if Maven Central is slow or offline.
3.  **Duplicate Storage**: Packages are downloaded multiple times across master and worker instances.

To solve this, this custom image **pre-downloads** all required JARs and caches them directly in `/opt/spark/jars/`. When `spark-submit` is invoked, the libraries are immediately available in the local classpaths, reducing startup latency to less than 2 seconds.

---

## 📦 Installed Packages & Driver Matrix

### 🐍 Python Packages
*   `python-dotenv==1.0.1` — Used to load configurations from `.env`.
*   `delta-spark==3.2.0` — Required for reading/writing Delta Tables.
*   `transformers` & `torch` (CPU) — Enables NLP sentiment analysis using FinBERT models directly inside PySpark UDFs.

### 🏛️ Pre-Cached JAR Libraries
The following dependencies are compiled directly into the image:

| Category | Library Name | Version | Maven Source |
| :--- | :--- | :---: | :--- |
| **Azure ADLS Gen2** | `hadoop-azure` | `3.3.4` | Apache Hadoop Azure Support |
| | `wildfly-openssl` | `1.1.3.Final` | Secure HTTP Handshakes |
| | `azure-storage-blob` | `12.25.1` | Azure Storage Core Client |
| | `azure-storage-common` | `12.24.1` | Storage Common Shared Lib |
| | `azure-core` | `1.45.1` | Azure Core SDK Utilities |
| | `azure-core-http-netty` | `1.14.0` | Netty-based HTTP Pipeline |
| | `azure-identity` | `1.11.1` | Entra ID / SP authentication |
| | `msal4j` | `1.14.0` | Microsoft Authentication Lib |
| **Kafka Event Streams**| `spark-sql-kafka-0-10_2.12`| `3.5.0` | Structured Streaming Kafka |
| | `kafka-clients` | `3.5.1` | Kafka Client Connections |
| | `spark-token-provider` | `3.5.0` | Token Handshake Manager |
| | `commons-pool2` | `2.11.1` | Apache Commons Pool |
| **Delta Lakehouse** | `delta-spark_2.12` | `3.2.0` | Delta Lake Core |
| | `delta-storage` | `3.2.0` | Delta Storage APIs |
| **PostgreSQL Database**| `postgresql` | `42.6.0` | Postgres JDBC Connection |
