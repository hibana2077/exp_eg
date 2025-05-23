"""
Embedding utilities for vector search

This module provides functions for embedding-based search conditions including:
1. Semantic search using text embeddings
2. Coordinate-based search for spatial queries
3. Hybrid search combining semantic and coordinate vectors

The coordinate search functionality allows for retrieving documents based on their 
spatial location within a page, using a 4-dimensional vector [x1, y1, x2, y2] 
that represents the bounding box coordinates.
"""

from fastembed import TextEmbedding
from cfg.emb_settings import EMB_MODEL, EMB_SEARCH_METRIC

def add_emb_cond(condition: dict) -> dict:
    """
    Add embedding condition to the existing condition.
    """
    embedding_model = TextEmbedding(model_name=EMB_MODEL)
    embeddings_list = list(embedding_model.embed(condition["text"][0]['query']))
    
    # Add embedding to the condition
    if 'dense' not in condition:
        condition['dense'] = []
        
        # Check if the collection name ends with _texts (indicating multi-vector format)
        if condition.get('collection_name', '').endswith('_texts'):
            # For text collections, use multi-vector format with named vectors
            condition['dense'].append({
                'field': 'embed',  # Using 'embed' as the named vector for semantic similarity
                'query': embeddings_list[0],
                'element_type': 'float',
                'metric': EMB_SEARCH_METRIC,
                'topn': condition["text"][0]['topn']
            })
        else:
            # For other collections, use the traditional single vector format
            condition['dense'].append({
                'field': 'embedding',
                'query': embeddings_list[0],
                'element_type': 'float',
                'metric': EMB_SEARCH_METRIC,
                'topn': condition["text"][0]['topn']
            })
    else:
        # If dense is already present, append the new condition
        if condition.get('collection_name', '').endswith('_texts'):
            condition['dense'].append({
                'field': 'embed',
                'query': embeddings_list[0],
                'element_type': 'float',
                'metric': EMB_SEARCH_METRIC,
                'topn': condition["text"][0]['topn']
            })
        else:
            condition['dense'].append({
                'field': 'embedding',
                'query': embeddings_list[0],
                'element_type': 'float',
                'metric': EMB_SEARCH_METRIC,
                'topn': condition["text"][0]['topn']
            })
    
    return condition

def add_coord_cond(condition: dict, coordinates: list) -> dict:
    """
    Add coordinate-based search condition to the existing condition.
    
    Parameters:
    -----------
    condition : dict
        The existing search condition dictionary
    coordinates : list
        A list of 4 float values representing the coordinate vector [x1, y1, x2, y2]
        
    Returns:
    --------
    dict
        The updated condition with coordinate search added
    """
    if not condition.get('collection_name', '').endswith('_texts'):
        raise ValueError("Coordinate search is only supported for text collections")
        
    if len(coordinates) != 4:
        raise ValueError("Coordinates must be a list of 4 float values [x1, y1, x2, y2]")
    
    # Add coordinate search condition
    if 'dense' not in condition:
        condition['dense'] = []
    
    condition['dense'].append({
        'field': 'cord',  # Using 'cord' as the named vector for coordinate similarity
        'query': coordinates,
        'element_type': 'float',
        'metric': 'euclid',  # Euclidean distance for spatial coordinates
        'topn': condition.get("text", [{"topn": 10}])[0].get('topn', 10)
    })
    
    return condition


def add_hybrid_cond(condition: dict, text_query: str, coordinates: list, 
                   semantic_weight: float = 0.7, coordinate_weight: float = 0.3) -> dict:
    """
    Add hybrid search condition combining both semantic and coordinate vectors.
    
    Parameters:
    -----------
    condition : dict
        The existing search condition dictionary
    text_query : str
        The text query for semantic search
    coordinates : list
        A list of 4 float values representing the coordinate vector [x1, y1, x2, y2]
    semantic_weight : float
        Weight for semantic similarity (default: 0.7)
    coordinate_weight : float
        Weight for coordinate similarity (default: 0.3)
        
    Returns:
    --------
    dict
        The updated condition with hybrid search added
    """
    if not condition.get('collection_name', '').endswith('_texts'):
        raise ValueError("Hybrid search is only supported for text collections")
        
    # Add text to condition if not present
    if 'text' not in condition:
        condition['text'] = [{'query': text_query, 'topn': 10}]
    
    # Add semantic condition
    condition = add_emb_cond(condition)
    
    # Add coordinate condition
    condition = add_coord_cond(condition, coordinates)
    
    # Add weights for fusion
    condition['fusion'] = {
        'weights': {
            'embed': semantic_weight,
            'cord': coordinate_weight
        }
    }
    
    return condition