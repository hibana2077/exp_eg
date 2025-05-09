# Data Engine

## Hardware Requirements

- CPU: 16 cores
- RAM: 32 GB

## Database Configuration

The system supports two database options:
1. Local MongoDB (for development/testing)
2. MongoDB Atlas (for production/cloud deployment)

You can use both simultaneously and switch between them as needed.

### Local MongoDB Configuration

Local MongoDB is configured by default with the following environment variables:
- `MONGO_SERVER`: MongoDB server URL (default: "mongodb://db_mongo:27017")
- `MONGO_INITDB_ROOT_USERNAME`: MongoDB username
- `MONGO_INITDB_ROOT_PASSWORD`: MongoDB password

### MongoDB Atlas Configuration

To use MongoDB Atlas:

1. Create a MongoDB Atlas account and cluster
2. Configure the following environment variables:
   - `MONGO_ATLAS_URI`: MongoDB connection string
   - `MONGO_ATLAS_USERNAME`: MongoDB Atlas username
   - `MONGO_ATLAS_PASSWORD`: MongoDB Atlas password
   - `MONGO_ATLAS_ENABLED`: Set to "true" to use Atlas (default: "false")

### Vector Search

Vector search is implemented using MongoDB Atlas Vector Search capabilities. For optimal performance:

1. Create vector indexes through the MongoDB Atlas UI or API using the configuration in `src/core/cfg/atlas_indexes.json`
2. Configure vector dimension to match your embedding model (default: 512)
3. Use cosine similarity for embedding comparison

### Switching Between Databases

Use the provided utility script to switch between local MongoDB and MongoDB Atlas:

```bash
cd src/core/scripts
chmod +x mongo_config.sh

# Show current configuration
./mongo_config.sh --action show

# Switch to MongoDB Atlas
./mongo_config.sh --action use-atlas

# Switch to local MongoDB
./mongo_config.sh --action use-local
```

### Data Migration

To migrate data between local MongoDB and MongoDB Atlas, use the mongo_migration.py utility:

```bash
python -m utils.mongo_migration to_atlas --databases mydb1 mydb2 --overwrite
python -m utils.mongo_migration from_atlas --databases mydb1 mydb2
```
