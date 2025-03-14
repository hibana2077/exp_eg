---
marp: true
theme: academic
paginate: true
math: katex
---

<!-- _class: lead -->

# Weekly Report

## 03/10 - 03/14

---

<!-- _header: 大綱 -->

- 前端跟後端的部分功能串接
- text表格新增 embedding 

---

<!-- _header: コードブロック -->

```python
import torch
print(torch.cuda.is_available())
```

こんな感じでコードブロックを書くことができる。

```python
from transformers import AutoModelForMaskedLM, AutoTokenizer
model = AutoModelForMaskedLM.from_pretrained("cl-tohoku/bert-base-japanese-whole-word-masking")
tokenizer = AutoTokenizer.from_pretrained("cl-tohoku/bert-base-japanese-whole-word-masking")

inputs = tokenizer.encode_plus("私はとても[MASK]です。", return_tensors='pt')
outputs = model(**inputs)
tokenizer.convert_ids_to_tokens(outputs.logits[0][1:-1].argmax(axis=-1))
```

横幅は自動調整される（ドキュメントの[Auto-scaling](https://github.com/marp-team/marp-core#auto-scaling-features)を参照）。

---

<!-- _header: 数式 -->

$$ I_{xx}=\int\int_Ry^2f(x,y)\cdot{}dydx $$

$$
f(x) = \int_{-\infty}^\infty
    \hat f(\xi)\,e^{2 \pi i \xi x}
    \,d\xi
$$

こんな感じで数式を書くことができる。もちろんインラインの $\LaTeX$ も使える。  
ついでに絵文字も使える:smile:

---

<!-- _header: 図 -->

1. まず[このいらすとやのリンク](https://www.irasutoya.com/2018/10/blog-post_723.html)から画像（`kenkyu_woman_seikou.png`）を右クリックでダウンロードしてください。
2. この Markdown のあるディレクトリの中に `images` という名前のディレクトリを作り、先ほどダウンロードした画像を配置してください。これで準備が整いました。

![w:300 center](./images/kenkyu_woman_seikou.png)