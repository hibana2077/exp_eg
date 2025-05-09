import datetime
import pprint
import os
import pymongo
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np
import polars as pl
import pandas as pd
import pyarrow as pa
from .mongo_atlas_config import get_db_collection, MONGO_ATLAS_ENABLED

def search(
    db_name: str,
    table_name: str,
    select_cols: List[str],
    conditions: Dict[str, Any] = None,
    limit: int = 10,
    return_format: str = "pl",  # Options: "pl" (polars), "pd" (pandas), "arrow" (pyarrow), "raw" (list)
    use_atlas: Optional[bool] = None  # If None, uses the MONGO_ATLAS_ENABLED environment variable
) -> Any:
       """
       Flexible search function for MongoDB that supports multiple match conditions.
       Supports both MongoDB Atlas (cloud) and local MongoDB instances.
       
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
       use_atlas : bool, optional
              If True, forces the use of MongoDB Atlas.
              If False, forces the use of local MongoDB.
              If None (default), uses the MONGO_ATLAS_ENABLED environment variable.
              
       Returns:
       --------
       Search results in the specified format
       """
       # Get the database collection from either Atlas or local MongoDB
       collection, is_atlas = get_db_collection(db_name, table_name, use_atlas)
       
       # Debug information
       print(f"Processing query: {db_name}.{table_name}")
       print(f"Select columns: {select_cols}")
       
       # Initialize MongoDB query dictionary
       mongo_query = {}
       mongo_scoring = {}
       pipeline = []
       
       # Process all conditions
       if conditions:
           # Apply text search conditions
           if 'text' in conditions:
               for text_match in conditions['text']:
                   # MongoDB supports full-text search with $text and $search operators
                   if len(conditions['text']) == 1:  # If only one text condition
                       mongo_query["$text"] = {"$search": text_match['query']}
                       mongo_scoring["score"] = {"$meta": "textScore"}
                   else:
                       # Add to search pipeline for aggregation
                       pipeline.append({
                           "$match": {"$text": {"$search": text_match['query']}}
                       })
                       pipeline.append({
                           "$addFields": {"score": {"$meta": "textScore"}}
                       })

           # Apply vector search conditions for dense vectors
           if 'dense' in conditions:
               for dense_match in conditions['dense']:
                   # Convert this to MongoDB vector search using $vectorSearch
                   if 'query' in dense_match:
                       field = dense_match['field']
                       query_vector = dense_match['query']
                       # Use $vectorSearch for MongoDB Atlas vector search
                       search_stage = {
                           "$vectorSearch": {
                               "index": f"{field}_vector_index",
                               "path": field,
                               "queryVector": query_vector,
                               "numCandidates": dense_match.get('topn', limit) * 10,  # Increased candidates for better results
                               "limit": dense_match.get('topn', limit)
                           }
                       }
                       pipeline.append(search_stage)

           # Apply filter conditions
           if 'filter' in conditions:
               filter_conditions = {}
               for filter_condition in conditions['filter']:
                   # Parse the filter condition (simplified for now)
                   if "<" in filter_condition:
                       field, value = filter_condition.split("<")
                       field = field.strip()
                       value = value.strip()
                       try:
                           value = int(value) if value.isdigit() else float(value)
                       except ValueError:
                           value = value
                       filter_conditions[field] = {"$lt": value}
                   elif ">" in filter_condition:
                       field, value = filter_condition.split(">")
                       field = field.strip()
                       value = value.strip()
                       try:
                           value = int(value) if value.isdigit() else float(value)
                       except ValueError:
                           value = value
                       filter_conditions[field] = {"$gt": value}
                   elif "=" in filter_condition:
                       field, value = filter_condition.split("=")
                       field = field.strip()
                       value = value.strip()
                       try:
                           value = int(value) if value.isdigit() else float(value)
                       except ValueError:
                           value = value
                       filter_conditions[field] = value

               if filter_conditions:
                   mongo_query.update(filter_conditions)

       # Determine how to execute the query based on conditions
       if pipeline:
           # If we have multiple conditions or vector search, use aggregation pipeline
           if mongo_query:
               pipeline.insert(0, {"$match": mongo_query})
           
           # Project only the selected columns if requested
           if select_cols and select_cols != ["*"]:
               projection = {col: 1 for col in select_cols}
               if "score" in mongo_scoring:
                   projection["score"] = mongo_scoring["score"]
               pipeline.append({"$project": projection})
           
           # Sort by score if available or other fields
           if "score" in mongo_scoring:
               pipeline.append({"$sort": {"score": -1}})
           
           # Limit the results
           pipeline.append({"$limit": limit})

           # Execute the aggregation pipeline
           result = list(collection.aggregate(pipeline))
           
       else:
           # Simple find query for basic conditions
           projection = None if select_cols == ["*"] else {col: 1 for col in select_cols}
           if mongo_scoring:
               projection = projection or {}
               projection.update(mongo_scoring)
           
           # Execute the find query
           cursor = collection.find(
               mongo_query,
               projection,
           ).sort([("_id", 1)])  # Default sort by _id
           
           if "score" in mongo_scoring:
               cursor = cursor.sort([("score", -1)])
           
           result = list(cursor.limit(limit))

       # Convert the results to the requested format
       if return_format == "pl":
           # Convert to Polars DataFrame
           import polars as pl
           df = pl.DataFrame(result)
           return [df]
       elif return_format == "pd":
           # Convert to Pandas DataFrame
           import pandas as pd
           df = pd.DataFrame(result)
           return [df]
       elif return_format == "arrow":
           # Convert to PyArrow Table
           import pyarrow as pa
           import pandas as pd
           df = pd.DataFrame(result)
           return [pa.Table.from_pandas(df)]
       else:
           # Return raw results
           return [result]