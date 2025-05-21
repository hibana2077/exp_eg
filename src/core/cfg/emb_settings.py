# TEXT data
EMB_MODEL = "intfloat/multilingual-e5-large"
EMB_SEARCH_METRIC = "cosine" # ip -> inner product, cosine -> cosine similarity, l2 -> l2 distance
TEXT_EMB_DIM = 1024

# IMAGE data
IMG_EMB_MODEL = "Qdrant/clip-ViT-B-32-vision"
IMG_CLIP_EMB_MODEL = "Qdrant/clip-ViT-B-32-text"
IMG_EMB_SEARCH_METRIC = "cosine"
IMG_EMB_DIM = 512

# TABLE data
TABLE_CHUNK_MAX_TOKENS = 66
TABLE_EMB_MODEL = "intfloat/multilingual-e5-large"
TABLE_EMB_DIM = 1024