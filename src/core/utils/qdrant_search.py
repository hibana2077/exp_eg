import os
import datetime
import pprint
import numpy as np
import polars as pl
import pandas as pd
from typing import List, Dict, Any, Optional, Union, Tuple
from qdrant_client import QdrantClient
from qdrant_client.http import models


def qdrant_search(
    db_name: str,
    collection_name: str,
    select_cols: List[str],
    conditions: Dict[str, Any] = None,
    limit: int = 10,
    return_format: str = "pl"  # Options: "pl" (polars), "pd" (pandas), "arrow" (pyarrow), "raw" (list)
) -> Any:
    """
    Flexible search function for Qdrant that supports multiple search conditions.
    
    Parameters:
    -----------
    db_name : str
        Name of the database (not used in Qdrant, kept for compatibility)
    collection_name : str
        Name of the collection to search
    select_cols : List[str]
        Columns to return in the result (used for filtering response)
    conditions : Dict[str, Any], optional
        Dictionary of search conditions where:
        - Keys are condition types: 'dense', 'text', 'filter'
        Example:
        {
        'dense': [
            {'field': 'embedding', 'query': query_vector, 'element_type': 'float', 'metric': 'cosine', 'topn': 3}
        ],
        'text': [
            {'field': 'text', 'query': 'interest rate', 'topn': 3}
        ],
        'filter': ['year < 2024']
        }
    limit : int, optional
        Maximum number of results to return
    return_format : str, optional
        Format to return results in: "pl" (polars), "pd" (pandas), "arrow" (pyarrow), or "raw" (list)
        
    Returns:
    --------
    Search results in the specified format
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
    search_params = {
        "limit": limit,
    }
    assert type(limit) == int, "Limit must be an integer"
    
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
