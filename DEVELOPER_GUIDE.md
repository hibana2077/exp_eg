# Developer Documentation

This document is for developers of this project, describing the architecture, development environment, startup process, directory structure, common problems, and contribution methods.

---

## System Architecture

This system adopts a microservices architecture, with the following main components:

- **Web**: Streamlit frontend, providing a knowledge base operation interface.
- **Core**: FastAPI, responsible for vectorization, retrieval, and Qdrant operations.
- **Backend**: FastAPI, responsible for business logic, user management, and knowledge base management.
- **Qdrant**: Vector database.
- **MongoDB**: Stores knowledge base and document metadata.
- **MinIO**: Object storage, storing original documents.

Refer to `/docs/assets/arch.png` for the architecture diagram.

---

## Directory Structure Description

- `src/`: Main code and deployment scripts
   - `core/`: Vectorization and retrieval API
   - `backend/`: Business logic API
   - `web/`: Streamlit frontend
   - `docker-compose.yaml`: Multi-service collaborative startup
   - `install_everything.sh`, `setup.sh`: Installation and initialization scripts
- `docs/`: Technical documents, API documents, architecture diagrams
- `test_file/`: Test PDF documents

---

## Development Environment Installation

1. **Install Docker and Docker Compose**
    - It is recommended to execute `src/install_everything.sh` to automatically install all dependencies.
    - macOS users can manually install Docker Desktop.

2. **Create Environment Variable File**

    ```bash
    cp src/.env-template src/.env
    # And modify the content as needed
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

5. **Frontend Entry**
    - Default URL: <http://localhost:4321>

---

## Main Component Description

- **Web** (`src/web/`)
   - Streamlit implementation, supports login/registration, knowledge base management, document upload and query.
- **Core** (`src/core/`)
   - FastAPI, responsible for document vectorization, Qdrant retrieval, and hybrid query.
- **Backend** (`src/backend/`)
   - FastAPI, responsible for user management, knowledge base CRUD, MinIO/MongoDB operations.
- **Qdrant**
   - Vector database, supports efficient vector retrieval and hybrid query.
- **MongoDB**
   - Stores knowledge base and document metadata.
- **MinIO**
   - Object storage, storing original documents.

---

## API Documentation

Please refer to `/docs/api.md`, which contains complete API specifications and examples.

---

## Common Problems

- If the startup fails, check whether Docker is installed, folder permissions, and environment variables are correct.
- If you need to reset the environment, delete the `/data` directory and re-execute `setup.sh`.

---

## Contribution Method

1. Fork this project and create a new branch.
2. Develop and test.
3. Submit a Pull Request, explaining the changes.

---

If you have any questions, please contact the project maintainers.
