# Qdrant Vector Database Notes

## Overview

This project uses Qdrant for vector storage and search operations. It leverages Qdrant client version 1.14.2 for all vector database operations.

## API Usage

### Import Structure

```python
from qdrant_client import QdrantClient
from qdrant_client.http import models
```

### Common Models

- `models.VectorParams` - Used to define vector parameters
- `models.Distance.COSINE` - Used for similarity measurement
- `models.PointStruct` - Used for storing points in collections
- `models.TextIndexParams` - Used for text indexing
- `models.TokenizerType.WORD` - Used for text tokenization

### Configuration

- Qdrant server host and port are configured via environment variables:
  - `QDRANT_HOST` (default: "db_qdrant")
  - `QDRANT_PORT` (default: "6333")

## Database Operations

### Vector Storage

Vectors are stored in collections with the naming pattern:

- `file_{timestamp}_texts` - For text data
- `file_{timestamp}_images` - For image data
- `file_{timestamp}_tables` - For table data

### Searching

The search function supports multiple modes:

- Dense vector search (by embedding)
- Filter-based search
- Text search

## Docker Configuration

The Qdrant container is configured in `docker-compose.yaml` with:

- Ports: 6333 (HTTP) and 6334 (GRPC)
- Volume: `/data/qdrant-data:/qdrant/storage`
- Health check: Tests HTTP endpoint `/healthz`
