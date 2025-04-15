import pandas as pd

df = pd.DataFrame({
    "text": ["This is a sample text.", "Another sample text."],
    "label": ["label1", "label2"],
    "prov": [{"page_no": 1, "bbox": {"x0": 0, "y0": 0, "x1": 100, "y1": 100}}, {"page_no": 2, "bbox": {"x0": 10, "y0": 10, "x1": 110, "y1": 110}}],
    "self_ref": ["ref1", "ref2"],
    "parent": [{"$ref": "parent_ref1"}, {"$ref": "parent_ref2"}],
    "content_layer": ["layer1", "layer2"],
    "orig": ["original text 1", "original text 2"]
})

print(df)
# drop index
df.reset_index(drop=True, inplace=True)