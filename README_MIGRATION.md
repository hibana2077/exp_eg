# Infinity to Qdrant Migration

## Overview

This migration replaces Infinity DB with Qdrant as the vector database in the application. This document provides information on the migration process and how to use the new functionality.

## Why Migrate to Qdrant?

Qdrant offers several advantages over Infinity DB:

1. **Mature Ecosystem**: Qdrant is a production-ready vector database with a growing ecosystem
2. **Performance**: Better performance for vector search operations
3. **Scalability**: Designed to handle large-scale vector search applications
4. **Active Development**: Regular updates and improvements
5. **Advanced Features**: Filtering, payload indexing, and other advanced features

## Migration Components

The migration includes:

1. New implementation files:
   - `core/utils/qdrant_store.py`: Qdrant-based vector storage
   - `core/utils/qdrant_search.py`: Search functionality using Qdrant
   - `core/utils/qdrant_indexing.py`: Indexing functions for Qdrant
   - `core/utils/migration_helper.py`: Helper script for migrating data

2. Updated configuration:
   - `docker-compose.yaml`: Updated with proper Qdrant configuration
   - Environment variables for Qdrant host and port

3. Migration tools:
   - `migrate_to_qdrant.sh`: Migration script to help with the transition

## How to Migrate

### Option 1: Automated Migration

Run the migration script:

```bash
cd src
./migrate_to_qdrant.sh
```

The script provides options to:
1. Update `main.py` to use Qdrant
2. Migrate existing data from Infinity to Qdrant
3. Run both steps together

### Option 2: Manual Migration

1. Update the main file:
   ```bash
   cp ./core/main_with_qdrant.py ./core/main.py
   ```

2. Edit `main.py` to set `USE_QDRANT = True`

3. Rebuild the core container:
   ```bash
   docker-compose up -d --build core
   ```

4. Run the migration script in the core container:
   ```bash
   docker-compose exec core python -c "from utils.migration_helper import migrate_all_kbs; migrate_all_kbs()"
   ```

## Verifying Migration

After migrating, you should:

1. Test uploading a new file to ensure it stores data in Qdrant
2. Test searching to ensure results are as expected
3. Check performance metrics

## Rollback Procedure

If issues occur, you can rollback to Infinity:

1. Restore the original main file:
   ```bash
   cp ./core/main.py.infinity.bak ./core/main.py
   ```

2. Rebuild the core container:
   ```bash
   docker-compose up -d --build core
   ```

## Technical Details

### Qdrant Configuration

The Qdrant container is configured with:
- Port 6333 for HTTP API
- Port 6334 for gRPC API (if needed)
- Persistent storage volume at `/data/qdrant-data`
- Health check mechanism

### Data Structure Differences

The migration maps Infinity concepts to Qdrant:
- Infinity "database" → Qdrant (no equivalent, uses collections)
- Infinity "table" → Qdrant "collection"
- Infinity "row" → Qdrant "point"

### Search Capability Differences

Qdrant has some differences in search capabilities:
- Different filtering syntax
- Different approach to payload indexing
- Different result scoring mechanism

The implementation adapts these differences to maintain the same API interface.

## Contributing

If you encounter issues or have suggestions for improving the migration, please submit an issue or pull request to the repository.
