# Infinity to Qdrant Migration Implementation Guide

This guide provides step-by-step instructions to migrate from Infinity DB to Qdrant in your project.

## Step 1: Update Environment Configuration

1. Update the docker-compose.yaml file to include Qdrant environment variables:
   - Added `QDRANT_HOST` and `QDRANT_PORT` to the core service
   - Enhanced Qdrant container configuration with healthcheck and additional port

## Step 2: Implement New Qdrant Components

The following files have been implemented to handle Qdrant functionality:

1. `/core/utils/qdrant_store.py`: Vector storage implementation with Qdrant
2. `/core/utils/qdrant_search.py`: Search functionality using Qdrant
3. `/core/utils/qdrant_indexing.py`: Indexing operations for Qdrant
4. `/core/main_with_qdrant.py`: An updated main file that supports both Infinity and Qdrant

## Step 3: Migration Procedure

### Testing Phase

1. **Test in Development Environment**:
   ```bash
   cp /core/main_with_qdrant.py /core/main.py
   ```

   This replaces the main file with the version that supports both backends.

2. **Enable Qdrant**:
   In the new `main.py`, ensure the `USE_QDRANT` variable is set to `True`:
   ```python
   USE_QDRANT = True
   ```

3. **Start Services**:
   ```bash
   docker-compose up -d
   ```

4. **Verify Qdrant Operation**:
   Test the system by uploading a file and running search operations.

### Production Migration

1. **Backup Data**:
   ```bash
   # Backup MongoDB data
   docker exec -it db_mongo mongodump --out /data/backup
   
   # Backup MinIO data
   # (MinIO data is stored in volumes and doesn't need manual backup)
   ```

2. **Deploy Updated Code**:
   ```bash
   cp /core/main_with_qdrant.py /core/main.py
   docker-compose up -d --build
   ```

3. **Reprocess Data**:
   - If needed, reprocess existing files to create Qdrant collections
   - This can be done through the web interface or API

4. **Verify System**:
   - Test searches and verify results match expected behavior
   - Check performance and optimize if needed

## Step 4: Data Migration (Optional)

If you have significant data in Infinity DB that needs to be migrated:

1. Create a custom script to extract data from Infinity and load into Qdrant
2. For each knowledge base:
   - List all tables using `list_all_tables`
   - Extract data from each table
   - Insert into corresponding Qdrant collections

## Step 5: Cleanup (After Successful Migration)

1. **Remove Infinity Container**:
   Edit docker-compose.yaml to comment out the Infinity service block
   
2. **Remove Unused Dependencies**:
   Update requirements.txt to remove:
   ```
   infinity-sdk==0.6.0.dev3
   ```
   
3. **Remove Legacy Code**:
   After a successful migration and testing, you can remove Infinity-specific code:
   ```bash
   rm /core/utils/vec_store.py
   rm /core/utils/search.py
   rm /core/utils/indexing.py
   ```

4. **Rebuild Application**:
   ```bash
   docker-compose up -d --build
   ```

## Technical Notes

### Key Differences Between Infinity and Qdrant

1. **Data Organization**:
   - Infinity: Databases and tables
   - Qdrant: Collections and points

2. **Indexing**:
   - Infinity: Requires explicit indexes for text search
   - Qdrant: Has built-in payload indexing capabilities

3. **Query Structure**:
   - Infinity: Custom query syntax with chaining
   - Qdrant: Uses SearchRequest with filters

4. **Performance Considerations**:
   - Qdrant scales better for production workloads
   - Proper collection design is important for performance

## Troubleshooting

### Common Issues and Solutions

1. **Connection Issues**:
   - Verify Qdrant container is running: `docker ps | grep qdrant`
   - Check logs: `docker logs qdrant`
   - Ensure correct host/port in environment variables

2. **Missing Results**:
   - Check collection names in Qdrant
   - Verify data was properly loaded
   - Inspect search parameters and payloads

3. **Performance Issues**:
   - Consider adding more indexes for frequently queried fields
   - Check vector size and distance metrics
   - Review collection configuration

For more help, consult the [Qdrant documentation](https://qdrant.tech/documentation/) or open an issue in the project repository.
