# API docking

## intro

This system have two main api servers:

- `core`: The core server mainly handles knowledge base and retrieval tasks.
- `backend`: This server used for the knowledge base's indexing.

## API spec

### Create a Knowledge Base

- POST {backend}/new_kb
    - Request Body:
    ```json
    {
        "name": "my_kb", // No less than 3 characters
        "description": "my knowledge base",
        "icon": "string or 🐱",
        "owner": "string(user name or user id)",
    }
    ```
    - Response:
    ```json
    {
        "status": "success",
        "message": "Knowledge base entry and MinIO bucket created"
    }
    ```

### List all knowledge bases

- GET {backend}/list_all_kb/{owner}
    - Response:
    ```json
    {
        "status": "success",
        "count": 1,
        "data": [
            {
                "name": "my_kb",
                "description": "my knowledge base",
                "icon": "string or 🐱",
                "owner": "string(user name or user id)",
            }
        ]
    }
    ```

### Get specific knowledge base

- GET {backend}/get_kb/{owner}/{kb_name}
    - Response:
    ```json
    {
        "status": "success",
        "data": {
            "name": "my_kb",
            "description": "my knowledge base",
            "icon": "string or 🐱",
            "owner": "string(user name or user id)",
        }
    }
    ```

### 