# Deployment

## TL;DR

```bash
cp .env-template .env
bash ./install_everything.sh # or sudo bash ./install_everything.sh
bash ./setup.sh # or sudo bash ./setup.sh
docker-compose up -d --build
```

## Environment Variables

Please copy `.env-template` to `.env` and change the values accordingly.
Also, make sure to modify the `minio-config.json` file to match your MinIO configuration.

## Vector Database Configuration

This system uses Qdrant as the vector database. The database is automatically configured through the docker-compose setup.

Key configuration points:
- Host: `db_qdrant`
- Port: `6333`
- Storage path: `/data/qdrant-data`

## Auto Script

After setting up the environment variables, you can run the following commands to set up the system:

```bash
bash ./setup.sh
```

This will:
1. Create necessary data directories
2. Set up environment variables if not already done
3. Start all services with Docker Compose

## Services

The system consists of the following services:
- `core` - Backend API for vector operations
- `web` - Frontend web interface
- `backend` - Backend API for business logic
- `db_mongo` - MongoDB for metadata storage
- `db_qdrant` - Qdrant vector database
- `minio` - Object storage for files