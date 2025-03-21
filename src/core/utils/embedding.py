from fastembed import TextEmbedding


def make_emb(data:dict, model_name: str = "intfloat/multilingual-e5-large") -> dict:
    """
    Generate embeddings for the given data using the specified model.
        data (dict): The data to generate embeddings for.
        model_name (str): The name of the model to use for generating embeddings.
        Returns:
            dict: The data with the generated embeddings."
    """