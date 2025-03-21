from fastembed import TextEmbedding
from cfg.emb_settings import EMB_MODEL, EMB_SEARCH_METRIC

def add_emb_cond(condition: dict) -> dict:
    """
    Add embedding condition to the existing condition.
    """
    embedding_model = TextEmbedding(model_name=EMB_MODEL)
    embeddings_list = list(embedding_model.embed(condition["text"][0]['query']))
    
    # Add embedding to the condition
    # condition["embedding"] = embeddings_list[0]
    condition['dense'].append({
        'field': 'embedding',
        'query': embeddings_list[0],
        'element_type': 'float',
        'metric': EMB_SEARCH_METRIC,
        'topn': condition["text"][0]['topn']
    })
    
    return condition