import infinity
import datetime
import os
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np

def search(
    db_name: str,
    table_name: str,
    select_cols: List[str],
    conditions: Dict[str, Any] = None,
    limit: int = 10,
    return_format: str = "pl"  # Options: "pl" (polars), "pd" (pandas), "arrow" (pyarrow), "raw" (list)
) -> Any:
       """
       Flexible search function for Infinity DB that supports multiple match conditions.
       
       Parameters:
       -----------
       db_name : str
              Name of the database to search
       table_name : str
              Name of the table to search
       select_cols : List[str]
              Columns to return in the result
       conditions : Dict[str, Any], optional
              Dictionary of search conditions where:
              - Keys are condition types: 'dense', 'text', 'sparse', 'filter', 'fusion'
              - Values are parameters for each condition type
              Example:
              {
              'dense': [
                     {'field': 'embedding', 'query': query_vector, 'element_type': 'float', 'metric': 'cosine', 'topn': 3}
              ],
              'text': [
                     {'field': 'text', 'query': '利率', 'topn': 3, 'options': {'index_name': 'idx_name'}}
              ],
              'filter': ['year < 2024'],
              'fusion': {
                     'method': 'match_tensor', 
                     'topn': 3,
                     'fusion_params': {
                     'field': 'tensor', 
                     'element_type': 'float',
                     'query_tensor': [[0.9, 0.0, 0.0, 0.0], [1.1, 0.0, 0.0, 0.0]]
                     }
              }
              }
       limit : int, optional
              Maximum number of results to return
       return_format : str, optional
              Format to return results in: "pl" (polars), "pd" (pandas), or "raw"
              
       Returns:
       --------
       Search results in the specified format
       """
       INFINITY_HOST = os.getenv("INFINITY_HOST", "localhost")
       INFINITY_PORT = os.getenv("INFINITY_PORT", 8080)
       # Initialize connection
       infinity_obj = infinity.connect(infinity.NetworkAddress(INFINITY_HOST, INFINITY_PORT))
       db_obj = infinity_obj.get_database(db_name)
       table_obj = db_obj.get_table(table_name)
       
       # Start query with output selection
       query = table_obj.output(select_cols)
       
       # Apply conditions if provided
       if conditions:
              # Apply dense vector matches
              if 'dense' in conditions:
                     for dense_match in conditions['dense']:
                            query = query.match_dense(
                            dense_match['field'],
                            dense_match['query'],
                            dense_match.get('element_type', 'float'),
                            dense_match.get('metric', 'cosine'),
                            dense_match.get('topn', limit)
                            )
              
              # Apply text matches
              if 'text' in conditions:
                     for text_match in conditions['text']:
                            query = query.match_text(
                            text_match['field'],
                            text_match['query'],
                            text_match.get('topn', limit),
                            text_match.get('options', {})
                            )
              
              # Apply sparse vector matches
              if 'sparse' in conditions:
                     for sparse_match in conditions['sparse']:
                            # Create SparseVector from indices and values
                            sparse_vector = infinity.common.SparseVector(
                            sparse_match['indices'],
                            sparse_match['values']
                            )
                            query = query.match_sparse(
                            sparse_match['field'],
                            sparse_vector,
                            sparse_match.get('metric', 'ip'),
                            sparse_match.get('topn', limit)
                            )
              
              # Apply filters
              if 'filter' in conditions:
                     for filter_condition in conditions['filter']:
                            query = query.filter(filter_condition)
              
              # Apply fusion if needed
              if 'fusion' in conditions:
                     fusion_config = conditions['fusion']
                     query = query.fusion(
                            method=fusion_config['method'],
                            topn=fusion_config.get('topn', limit),
                            fusion_params=fusion_config.get('fusion_params', {})
                     )
       
       # Execute and return results in requested format
       if return_format == "pl":return query.to_pl()
       elif return_format == "pd":return query.to_pd()
       elif return_format == "arrow":return query.to_arrow()
       else:return query.to_result()