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

### Procese file

- POST {core}/process_file
    - Request Body:
    ```json
    {
        "kb_name": "my_kb",
        "task_queue": [
            {
                "kb_name": "my_kb",
                "file_name": "my_file.txt",
            },
            ...
        ]
    }
    ```
    - Response:
    ```json
    {
        "status": "success",
        "message": "File processed and indexed successfully"
    }
    ```

### List (embedding) tables

- GET {core}/list_tables/{kb_name}
    - Response:
    ```json
    {
        "status": "success",
        "tables":[
            {
                "table_name": "my_table",
                "table_type": "embedding",
                "description": "my table description",
                "owner": "string(user name or user id)",
            }
        ]
    }
    ```

### Search

- POST {core}/search
    - Request Body:
    ```json
    {
        "kb_name": "my_kb",
        "tables": [
            ["texts_table_name", "images_table_name", "tables_table_name"],
            ...
        ],
        "select_cols": ["*"],
        "conditions": { //for all tables
            "text": [
                {"field": "text", "query": "query_text", "topn": 10}
            ]
        },
        "do_image_search": true,
        "limit": 10,
        "return_format": "pd"
    }
    ```
    - Response:
    ```json
    {
        "status": "success",
        "tables": [
            df1.json,
            df2.json,
            df3.json,
            ...
        ]
    }
    ```