# moments_demo.py
"""
示範：計算中心矩 (order 1~5) 並繪圖
執行方法：
    python moments_demo.py
依賴：
    pip install numpy scipy matplotlib
"""

import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

# ---------------------------
# 1. 準備資料（範例用標準常態分布 1 萬筆）
#    若用自己的資料，把下一行改掉即可，例如：
#    data = np.loadtxt("mydata.csv")
# ---------------------------
data = np.random.normal(loc=0, scale=1, size=10_000)

# ---------------------------
# 2. 計算 1~5 階中心矩
# ---------------------------
def central_moment(x: np.ndarray, k: int) -> float:
    """
    回傳第 k 階中心矩。
    📌 注意：k=1 時理論值 0（因為減掉平均後再取一次方的期望）。
    """
    mean = np.mean(x)
    return np.mean((x - mean) ** k)

moments = {k: central_moment(data, k) for k in range(1, 6)}

print("Central moments (order 1–5):")
for k, v in moments.items():
    print(f"{k} 階中心矩: {v:.6f}")

# ---------------------------
# 3. 繪圖
# ---------------------------
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

# 3-1 直方圖
axes[0].hist(data, bins=50, density=True, alpha=0.7)
axes[0].set_title("Histogram")
axes[0].set_xlabel("Value")
axes[0].set_ylabel("Density")

# 3-2 中心矩長條圖
axes[1].bar(list(moments.keys()), list(moments.values()))
axes[1].set_xlabel("Order")
axes[1].set_title("Central moments (1–5)")

# 讓版面更緊湊
plt.tight_layout()

# ---------------------------
# 4. 存檔 & 顯示
# ---------------------------
plt.savefig("moments_demo.png", dpi=300, bbox_inches="tight")
plt.show()

print("\n✅ 圖片已儲存為 moments_demo.png")