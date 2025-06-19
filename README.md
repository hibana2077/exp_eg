# Data Engine

This system provides document vectorization, storage, and semantic retrieval capabilities, based on the Qdrant vector database. It supports multi-format documents, hybrid queries, and a modern web interface.

---

## System Architecture

- **Web Interface**: Streamlit frontend, supporting login/registration, knowledge base management, document uploading, and querying.
- **Core API**: FastAPI, responsible for document processing, embedding generation, and vector operations.
- **Backend API**: FastAPI, responsible for business logic, user management, and knowledge base management.
- **Qdrant**: Vector database, supporting efficient retrieval and hybrid queries.
- **MongoDB**: Stores knowledge base and document metadata.
- **MinIO**: Object storage, stores original documents.

For the architecture diagram and detailed technology stack, please refer to `docs/techstack.md` and `/docs/assets/arch.png`.

---

## Hardware Requirements

- CPU: 16 cores
- RAM: 32 GB
- Storage: 50GB or more recommended

---

## Installation and Startup

1. **Install Docker and Docker Compose**
    - It is recommended to execute `src/install_everything.sh` to automatically install all dependencies.
    - macOS users can manually install Docker Desktop.

2. **Create Environment Variable File**
    ```bash
    cp src/.env-template src/.env
    # And modify the content according to requirements
    ```

3. **Create Data Directory**
    ```bash
    sudo mkdir -p /data/qdrant-data /data/minio-data /data/mongo-data
    sudo chmod -R 777 /data
    ```

4. **Start Services**
    ```bash
    cd src
    bash setup.sh
    # Or manually execute docker-compose up -d --build
    ```

5. **Frontend Entry Point**
    - Default URL: http://localhost:4321

---

## Main Service Description

- `core`: Vectorization and retrieval API (`src/core`)
- `backend`: Business logic API (`src/backend`)
- `web`: Streamlit frontend (`src/web`)
- `db_qdrant`, `db_mongo`, `minio`: Database and object storage

---

## Advanced Settings

- `.env`: Please adjust account passwords, API keys, etc. according to actual needs.
- `minio-config.json`: MinIO settings can be customized.
- Qdrant, MongoDB, and MinIO are all automatically deployed by Docker Compose.

---

## API Documentation

For complete API specifications, please refer to `docs/api.md`.

---

## Reference Documents

- [QDRANT_NOTES.md](QDRANT_NOTES.md)
- [docs/techstack.md](docs/techstack.md)
- [docs/api.md](docs/api.md)

If you have any questions, please refer to `DEVELOPER_GUIDE.md` or contact the project maintainers.
