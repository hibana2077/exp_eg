#!/usr/bin/env python3
# Test script for Qdrant connection

import os
from qdrant_client import QdrantClient
from qdrant_client.http import models

def test_qdrant_connection():
    """Test connection to Qdrant server"""
    print("Testing Qdrant connection...")
    
    # Get configuration from environment variables
    host = os.getenv("QDRANT_HOST", "db_qdrant")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    
    # Initialize client
    client = QdrantClient(host=host, port=port)
    
    # Get cluster info to test connection
    try:
        info = client.get_cluster_info()
        print(f"Successfully connected to Qdrant!")
        print(f"Cluster info: {info}")
        return True
    except Exception as e:
        print(f"Failed to connect to Qdrant: {e}")
        return False

def list_collections():
    """List all collections in Qdrant"""
    print("\nListing collections...")
    
    # Get configuration from environment variables
    host = os.getenv("QDRANT_HOST", "db_qdrant")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    
    # Initialize client
    client = QdrantClient(host=host, port=port)
    
    try:
        collections = client.get_collections()
        print(f"Collections: {collections}")
        return collections
    except Exception as e:
        print(f"Failed to list collections: {e}")
        return None

if __name__ == "__main__":
    if test_qdrant_connection():
        list_collections()
