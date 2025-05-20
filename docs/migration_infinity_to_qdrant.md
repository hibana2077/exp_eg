# Migration Plan: Infinity DB to Qdrant

## Overview

This document outlines the plan for migrating from Infinity DB to Qdrant as the vector database in the current system. The migration involves updating vector storage, search functionality, and indexing operations.

## Current System Analysis

### Components Using Infinity DB

1. **Vector Storage (`vec_store.py`)**
   - Handles storing and retrieving text, image, and table data
   - Embeds documents and stores them in Infinity DB
   - Uses multiple models from fastembed for different content types

2. **Search Operations (`search.py`)**
   - Performs vector searches and hybrid searches
   - Uses Infinity DB specific query syntax
   - Supports multiple filtering conditions

3. **Indexing (`indexing.py`)**
   - Creates full-text indexes for text content
   - Adds index information to search conditions

4. **Configuration**
   - Infinity DB connection settings in docker-compose.yaml
   - Infinity DB setup script in setup.sh

### Other Components

- MongoDB: Stores metadata about knowledge bases and files
- MinIO: Stores original files
- FastAPI: Backend API for the application

## Migration Steps

### 1. Update Docker Configuration

- Update `docker-compose.yaml` to properly configure Qdrant
- Remove Infinity container or keep it temporarily for transition
- Ensure environment variables are properly set

### 2. Vector Store Implementation

- Create a new implementation of `VecStore` class using Qdrant
- Use Qdrant collections instead of Infinity tables
- Update storage format to match Qdrant requirements
- Implement backward compatibility functions

### 3. Search Functionality

- Create a new search implementation using Qdrant client
- Adapt search parameters to Qdrant's query syntax
- Ensure similar filtering capabilities for hybrid search

### 4. Indexing Strategy

- Adapt or replace the indexing approach to fit Qdrant
- Update index naming conventions
- Map Infinity's indexing to Qdrant's approach

### 5. Environment Configuration

- Add Qdrant specific environment variables
- Update any service references to use Qdrant

### 6. Unit Testing

- Create tests to verify database operations
- Validate search results match previous behavior
- Test with various file types and content

### 7. Performance Testing

- Compare search performance between Infinity and Qdrant
- Optimize Qdrant configuration if needed

## Implementation Details

### Required Code Changes

1. `vec_store.py`:
   - Create a new `QdrantVecStore` class
   - Implement all methods from `VecStore` using Qdrant
   - Ensure same functionality but with Qdrant as backend

2. `search.py`:
   - Create a new search function using Qdrant client
   - Adapt search parameters and conditions
   - Ensure similar response format for compatibility

3. `indexing.py`:
   - Create new indexing functions for Qdrant
   - Map Infinity indexing concepts to Qdrant

4. `main.py`:
   - Update API endpoints to use new implementations
   - Ensure response formats remain consistent

5. Configuration files:
   - Update environment variables
   - Modify docker-compose.yaml

## Migration Strategy

The migration will follow these phases:

1. **Development**: Create new implementations alongside existing code
2. **Testing**: Verify functionality with test data
3. **Parallel Operation**: Run both systems to compare results
4. **Switchover**: Move to Qdrant completely once confidence is high
5. **Cleanup**: Remove Infinity code and dependencies

## Potential Challenges

1. **Data Format Differences**: Qdrant may require different data structures
2. **Query Syntax**: Adapting complex queries to Qdrant's API
3. **Performance Tuning**: Optimizing Qdrant for similar performance
4. **Backward Compatibility**: Ensuring existing data can be accessed

## Timeline

1. Development of Qdrant implementations: 2-3 days
2. Testing and validation: 1-2 days
3. Parallel operation and comparison: 1 day
4. Complete switchover: 1 day
5. Documentation and cleanup: 1 day

Total estimated time: 6-8 days
