# Coordinate-Based Vector Search in Qdrant

This document explains the coordinate retrieval functionality that has been added to the Qdrant vector database integration.

## Overview

The system now supports storing and searching for documents based on their spatial coordinates within a page, in addition to the existing semantic search capabilities. This allows for more precise document retrieval based on the physical location of content.

## Key Features

### Multi-Vector Storage

Documents are now stored using a multi-vector approach:

1. **Semantic Vector (`embed`)**: Captures the meaning of the text content
2. **Coordinate Vector (`cord`)**: Stores the spatial position as a 4D vector [x1, y1, x2, y2]

### Search Types

The system supports three types of search:

1. **Semantic Search**: Find documents with similar meaning (existing functionality)
2. **Coordinate Search**: Find documents at similar positions on a page (new)
3. **Hybrid Search**: Combine semantic and coordinate searches with weighted scoring (new)

## Implementation Details

### Collection Setup

Text collections now use a multi-vector configuration:

```python
client.create_collection(
    collection_name=collection_name,
    vectors_config={
        "embed": models.VectorParams(size=1024, distance=models.Distance.COSINE),
        "cord": models.VectorParams(size=4, distance=models.Distance.EUCLID),
    }
)
```

### Document Storage

Documents are stored with both vector types:

```python
models.PointStruct(
    id=i,
    vector={
        "embed": embedding_vector,  # Semantic vector
        "cord": coordinate_vector   # Spatial vector [x1, y1, x2, y2]
    },
    payload={...}  # Document metadata and content
)
```

### Search Functions

#### Coordinate Search

```python
from src.core.utils.qdrant_search import qdrant_coordinate_search

results = qdrant_coordinate_search(
    collection_name="my_collection_texts",
    coordinate_vector=[0.2, 0.3, 0.7, 0.8],  # [x1, y1, x2, y2]
    limit=10
)
```

#### Hybrid Search

```python
from src.core.utils.qdrant_search import qdrant_hybrid_search

results = qdrant_hybrid_search(
    collection_name="my_collection_texts",
    text_query="important information",
    coordinate_vector=[0.2, 0.3, 0.7, 0.8],
    semantic_weight=0.6,
    coordinate_weight=0.4,
    limit=10
)
```

### Search Conditions in Embedding Module

The `embedding.py` module provides helper functions for constructing search conditions:

1. `add_coord_cond(condition, coordinates)`: Add coordinate search condition
2. `add_hybrid_cond(condition, text_query, coordinates, semantic_weight, coordinate_weight)`: Add hybrid search condition

## Testing

A test function `test_coordinate_search()` has been added to `qdrant_test.py` to verify the coordinate search functionality.

## Usage Notes

1. Coordinate search only works with text collections (names ending with `_texts`)
2. Coordinates are stored in the format [x1, y1, x2, y2] representing a bounding box
3. Euclidean distance is used for coordinate vector similarity
4. Hybrid search results include scores for both semantic and coordinate similarity
