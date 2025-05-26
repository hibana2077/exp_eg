import os
import datetime
import pprint
import numpy as np
import polars as pl
import pandas as pd
from typing import List, Dict, Any, Optional, Union, Tuple
from qdrant_client import QdrantClient
from qdrant_client.http import models
from .math_transform import calculate_centroid

def qdrant_search(
    db_name: str,
    collection_name: str,
    select_cols: List[str],
    conditions: Dict[str, Any] = None,
    limit: int = 10,
    return_format: str = "pl"  # Options: "pl" (polars), "pd" (pandas), "arrow" (pyarrow), "raw" (list)
) -> Any:
    """
    Performs a flexible search in a Qdrant collection.

    Supports dense vector search, text search, and filtering.

    - **db_name**: Name of the database (for compatibility, not directly used by Qdrant).
    - **collection_name**: The Qdrant collection to search within.
    - **select_cols**: A list of column names to include in the results.
    - **conditions**: A dictionary specifying search conditions.
        - Example:
          ```json
          {
            "dense": [
              {"field": "embedding", "query": [0.1, 0.2, ...], "element_type": "float", "metric": "cosine", "topn": 3}
            ],
            "text": [
              {"field": "text_content", "query": "search query text", "topn": 3}
            ],
            "filter": ["year < 2024", "category == \\"electronics\\""]
          }
          ```
    - **limit**: The maximum number of results to return.
    - **return_format**: The desired format for the results ("pl", "pd", "arrow", "raw").
    """
    QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
    
    # Initialize connection
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    # Check if collection exists
    try:
        client.get_collection(collection_name=collection_name)
    except Exception as e:
        print(f"Collection {collection_name} does not exist: {e}")
        if return_format == "pl":
            return [pl.DataFrame()]
        elif return_format == "pd":
            return [pd.DataFrame()]
        else:
            return [{}]
    
    # Set up search parameters
    search_vector = None
    search_params = {}
    
    # Parse conditions
    filter_conditions = None
    if conditions:
        # Handle dense vector search
        if 'dense' in conditions:
            for dense_match in conditions['dense']:
                search_vector = dense_match['query']
                # Handle non-array vectors
                if hasattr(search_vector, 'tolist'):
                    search_vector = search_vector.tolist()
                
                # Set search parameters based on metric
                if dense_match.get('metric', 'cosine') == 'cosine':
                    search_params['score_threshold'] = 0.0  # Cosine similarity threshold
                elif dense_match.get('metric', 'cosine') == 'l2':
                    search_params['score_threshold'] = 0.0  # L2 distance threshold (lower is better)
        
        # Handle filter conditions
        if 'filter' in conditions:
            must_conditions = []
            for filter_condition in conditions['filter']:
                # Parse filter conditions
                # Example: "year < 2024" -> field=year, op=<, value=2024
                parts = filter_condition.split()
                if len(parts) == 3:
                    field, op, value = parts
                    
                    # Convert value to appropriate type
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            # Keep as string
                            pass
                    
                    # Create condition based on operator
                    if op == "==":
                        must_conditions.append(
                            models.FieldCondition(
                                key=field, 
                                match=models.MatchValue(value=value)
                            )
                        )
                    elif op in ("<", ">", "<=", ">="):
                        range_params = {}
                        if op == "<":
                            range_params["lt"] = value
                        elif op == ">":
                            range_params["gt"] = value
                        elif op == "<=":
                            range_params["lte"] = value
                        elif op == ">=":
                            range_params["gte"] = value
                        
                        must_conditions.append(
                            models.FieldCondition(
                                key=field, 
                                range=models.Range(**range_params)
                            )
                        )
            
            if must_conditions:
                filter_conditions = models.Filter(must=must_conditions)
    
    # If no vector query but we have text query, use text for search
    if not search_vector and conditions and 'text' in conditions:
        from fastembed import TextEmbedding
        from cfg.emb_settings import EMB_MODEL
        
        embedding_model = TextEmbedding(model_name=EMB_MODEL)
        text_query = conditions['text'][0]['query']
        search_vector = list(embedding_model.embed([text_query]))[0]
        if hasattr(search_vector, 'tolist'):
            search_vector = search_vector.tolist()
    
    # Perform search
    if search_vector:
        # Check if this is a text collection that supports multi-vector search
        if collection_name.endswith("_texts"):
            # Use SearchRequest for multi-vector search on text collections
            search_results = client.search(
                collection_name=collection_name,
                query_vector=("embed", search_vector),  # Specify the vector name for multi-vector collections
                query_filter=filter_conditions,
                limit=limit,
                **search_params
            )
        else:
            # Use regular search for single-vector collections (images, tables)
            search_results = client.search(
                collection_name=collection_name,
                query_vector=search_vector,
                query_filter=filter_conditions,
                limit=limit,
                **search_params
            )
    else:
        # If no vector, perform scroll operation with filter
        search_results = client.scroll(
            collection_name=collection_name,
            limit=limit,
            filter=filter_conditions
        )[0]  # scroll returns (points, offset)
    
    # Convert results to desired format
    if not search_results:
        # Return empty result in requested format
        if return_format == "pl":
            return [pl.DataFrame()]
        elif return_format == "pd":
            return [pd.DataFrame()]
        elif return_format == "arrow":
            return [pl.DataFrame().to_arrow()]
        else:
            return [{}]
    
    # Extract payloads
    result_data = []
    for res in search_results:
        # Add score if it exists
        data = res.payload.copy()
        if hasattr(res, 'score'):
            data['score'] = res.score
        
        # Filter columns if select_cols is not "*"
        if select_cols != ["*"]:
            data = {k: v for k, v in data.items() if k in select_cols}
        
        result_data.append(data)
    
    # Convert to requested format
    if return_format == "pl":
        return [pl.DataFrame(result_data)]
    elif return_format == "pd":
        return [pd.DataFrame(result_data)]
    elif return_format == "arrow":
        return [pl.DataFrame(result_data).to_arrow()]
    else:
        return [result_data]


def qdrant_coordinate_search(
    collection_name: str,
    coordinate_vector: List[float],
    limit: int = 10,
    return_format: str = "pl"
) -> Any:
    """
    Performs coordinate-based search in Qdrant text collections.
    
    This function searches for documents with similar spatial locations based on their
    coordinate vectors. It's useful for finding content at specific positions on a page.
    
    Parameters:
    -----------
    collection_name : str
        Name of the text collection to search (should end with '_texts')
    coordinate_vector : List[float]
        4-element coordinate vector [x1, y1, x2, y2] for bounding box search
    limit : int
        Maximum number of results to return
    return_format : str
        Format to return results in: "pl" (polars), "pd" (pandas), "arrow" (pyarrow), or "raw" (list)
        
    Returns:
    --------
    Search results in the specified format
    
    Notes:
    ------
    - This function only works with text collections that use the multi-vector format
    - The coordinate vector should represent a bounding box as [x1, y1, x2, y2]
    - Uses Euclidean distance for spatial similarity
    """
    QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
    coordinate_vector = calculate_centroid(coordinate_vector)
    # Initialize connection
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    # Check if collection exists and is a text collection
    try:
        client.get_collection(collection_name=collection_name)
        if not collection_name.endswith("_texts"):
            raise ValueError("Coordinate search is only supported for text collections")
    except Exception as e:
        print(f"Collection {collection_name} does not exist or is not accessible: {e}")
        if return_format == "pl":
            return [pl.DataFrame()]
        elif return_format == "pd":
            return [pd.DataFrame()]
        else:
            return [{}]
    
    # Perform coordinate-based search using the 'cord' vector
    try:
        search_results = client.search(
            collection_name=collection_name,
            query_vector=("cord", coordinate_vector),  # Use the coordinate vector
            limit=limit
        )
    except Exception as e:
        print(f"Coordinate search failed: {e}")
        if return_format == "pl":
            return [pl.DataFrame()]
        elif return_format == "pd":
            return [pd.DataFrame()]
        else:
            return [{}]
    
    # Convert results to desired format
    if not search_results:
        if return_format == "pl":
            return [pl.DataFrame()]
        elif return_format == "pd":
            return [pd.DataFrame()]
        elif return_format == "arrow":
            return [pl.DataFrame().to_arrow()]
        else:
            return [{}]
    
    # Extract payloads
    result_data = []
    for res in search_results:
        data = res.payload.copy()
        if hasattr(res, 'score'):
            data['score'] = res.score
        result_data.append(data)
    
    # Convert to requested format
    if return_format == "pl":
        return [pl.DataFrame(result_data)]
    elif return_format == "pd":
        return [pd.DataFrame(result_data)]
    elif return_format == "arrow":
        return [pl.DataFrame(result_data).to_arrow()]
    else:
        return [result_data]


def qdrant_hybrid_search(
    collection_name: str,
    text_query: str = None,
    coordinate_vector: List[float] = None,
    semantic_weight: float = 0.7,
    coordinate_weight: float = 0.3,
    limit: int = 10,
    return_format: str = "pl"
) -> Any:
    """
    Performs hybrid search combining semantic and coordinate vectors.
    
    This function combines the power of semantic search (finding content with similar meaning)
    and coordinate-based search (finding content in similar positions). It's particularly
    useful when you want to find content that is both relevant to a topic AND located in
    a specific region of a document.
    
    Parameters:
    -----------
    collection_name : str
        Name of the text collection to search (should end with '_texts')
    text_query : str, optional
        Text query for semantic search
    coordinate_vector : List[float], optional
        4-element coordinate vector [x1, y1, x2, y2] for spatial search
    semantic_weight : float
        Weight for semantic similarity (default: 0.7)
    coordinate_weight : float
        Weight for coordinate similarity (default: 0.3)
    limit : int
        Maximum number of results to return
    return_format : str
        Format to return results in: "pl" (polars), "pd" (pandas), "arrow" (pyarrow), or "raw" (list)
        
    Returns:
    --------
    Search results in the specified format
    
    Notes:
    ------
    - At least one of text_query or coordinate_vector must be provided
    - Results include additional fields: hybrid_score, semantic_score, and coordinate_score
    - The hybrid_score is calculated as: semantic_weight * semantic_score + coordinate_weight * coordinate_score
    """
    import numpy as np
    
    if not text_query and not coordinate_vector:
        raise ValueError("At least one of text_query or coordinate_vector must be provided")
    
    QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
    
    # Initialize connection
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    # Check if collection exists and is a text collection
    try:
        client.get_collection(collection_name=collection_name)
        if not collection_name.endswith("_texts"):
            raise ValueError("Hybrid search is only supported for text collections")
    except Exception as e:
        print(f"Collection {collection_name} does not exist or is not accessible: {e}")
        if return_format == "pl":
            return [pl.DataFrame()]
        elif return_format == "pd":
            return [pd.DataFrame()]
        else:
            return [{}]
    
    results = {}
    
    # Perform semantic search if text query is provided
    if text_query:
        try:
            # Generate embedding for text query
            from fastembed import TextEmbedding
            from cfg.emb_settings import EMB_MODEL
            
            embedding_model = TextEmbedding(model_name=EMB_MODEL)
            search_vector = list(embedding_model.embed([text_query]))[0]
            if hasattr(search_vector, 'tolist'):
                search_vector = search_vector.tolist()
            
            semantic_results = client.search(
                collection_name=collection_name,
                query_vector=("embed", search_vector),
                limit=limit * 2  # Get more results for fusion
            )
            
            for result in semantic_results:
                doc_id = result.id
                if doc_id not in results:
                    results[doc_id] = {
                        'payload': result.payload,
                        'semantic_score': result.score,
                        'coordinate_score': 0.0
                    }
                else:
                    results[doc_id]['semantic_score'] = result.score
                    
        except Exception as e:
            print(f"Semantic search failed: {e}")
    
    # Perform coordinate search if coordinate vector is provided
    if coordinate_vector:
        try:
            coordinate_results = client.search(
                collection_name=collection_name,
                query_vector=("cord", coordinate_vector),
                limit=limit * 2  # Get more results for fusion
            )
            
            for result in coordinate_results:
                doc_id = result.id
                if doc_id not in results:
                    results[doc_id] = {
                        'payload': result.payload,
                        'semantic_score': 0.0,
                        'coordinate_score': result.score
                    }
                else:
                    results[doc_id]['coordinate_score'] = result.score
                    
        except Exception as e:
            print(f"Coordinate search failed: {e}")
    
    # Calculate hybrid scores and rank results
    final_results = []
    for doc_id, data in results.items():
        hybrid_score = (data['semantic_score'] * semantic_weight + 
                       data['coordinate_score'] * coordinate_weight)
        
        result_data = data['payload'].copy()
        result_data.update({
            'id': doc_id,
            'hybrid_score': hybrid_score,
            'semantic_score': data['semantic_score'],
            'coordinate_score': data['coordinate_score']
        })
        final_results.append(result_data)
    
    # Sort by hybrid score and limit results
    final_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
    final_results = final_results[:limit]
    
    # Convert to requested format
    if return_format == "pl":
        return [pl.DataFrame(final_results)]
    elif return_format == "pd":
        return [pd.DataFrame(final_results)]
    elif return_format == "arrow":
        return [pl.DataFrame(final_results).to_arrow()]
    else:
        return [final_results]
