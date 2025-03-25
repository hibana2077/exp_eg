import numpy as np
import matplotlib.pyplot as plt
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C

# 1. 產生訓練數據：使用 sin 函數並加上隨機噪音
X_train = np.atleast_2d(np.linspace(0, 10, 50)).T  # 50 個訓練點
y_train = np.sin(X_train).ravel() + np.random.normal(0, 0.1, X_train.shape[0])

# 2. 定義核函數：這裡使用常數核乘以 RBF 核，控制數據點間的相似性
kernel = C(1.0, (1e-3, 1e3)) * RBF(1.0, (1e-2, 1e2))

# 3. 建立 Gaussian Process 模型，並進行訓練
gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=9)
gp.fit(X_train, y_train)

# 4. 對新的輸入點進行預測，並獲得預測均值與標準差（不確定性量化）
X_test = np.atleast_2d(np.linspace(0, 10, 1000)).T  # 更多測試點用於畫圖
y_pred, sigma = gp.predict(X_test, return_std=True)

# 5. 繪製訓練數據、預測結果以及 95% 信賴區間
plt.figure(figsize=(10,6))
plt.plot(X_train, y_train, 'r.', markersize=8, label='Observed data')
plt.plot(X_test, y_pred, 'b-', label='Predicted mean')
plt.fill_between(X_test.ravel(), y_pred - 1.96 * sigma, y_pred + 1.96 * sigma, 
                 alpha=0.2, color='blue', label='95% confidence interval')
plt.xlabel('X')
plt.ylabel('y')
plt.title('Gaussian Process Regression with Uncertainty Quantification')
plt.legend()
plt.show()