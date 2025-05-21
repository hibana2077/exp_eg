# Data Engine

This system provides document vectorization, storage, and semantic search capabilities using Qdrant vector database.

## Architecture

The system consists of several components:

- **Web Interface**: Streamlit-based UI for interacting with the system
- **Core API**: Handles document processing, embedding, and vector operations
- **Backend API**: Manages business logic and application state
- **Qdrant**: Vector database for storing and searching document embeddings
- **MongoDB**: Database for storing metadata
- **MinIO**: Object storage for raw document files

## Hardware Requirements

- CPU: 16 cores
- RAM: 32 GB
- Storage: At least 50GB available space

## Installation

Refer to the installation instructions in the [src/README.md](src/README.md) file.

## Vector Database

The system uses Qdrant for vector storage and retrieval. Qdrant is a vector similarity search engine that provides:]

- Fast vector search with various distance metrics
- Filtering support during search operations
- Text indexing for hybrid search
- High performance for large-scale deployments

For more details about the Qdrant configuration, see [QDRANT_NOTES.md](QDRANT_NOTES.md).
