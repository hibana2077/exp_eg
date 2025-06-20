import numpy as np
import matplotlib.pyplot as plt

# Define activation functions
def softplus(x):
    return np.log1p(np.exp(-np.abs(x))) + np.maximum(x, 0)

def mish(x):
    return x * np.tanh(softplus(x))

def sine_mish(x, alpha=0.2, beta=np.pi, gamma=1.0):
    """
    gSineMish variant:
    f(x) = x * tanh(softplus(x)) + alpha * sigmoid(-gamma * x) * sin(beta * x)
    """
    sigmoid = 1 / (1 + np.exp(-(-gamma * x)))  # sigmoid(-gamma * x)
    return mish(x) + alpha * sigmoid * np.sin(beta * x)

# Data for plotting
x = np.linspace(-5, 5, 1000)
y_mish = mish(x)
y_sine_mish = sine_mish(x)

# Plotting
plt.figure(figsize=(8, 6))
plt.plot(x, y_mish, label='Mish')
plt.plot(x, y_sine_mish, label='Sine-Mish (α=0.2, β=π, γ=1)')
plt.axhline(0, linewidth=0.5)
plt.axvline(0, linewidth=0.5)
plt.title('Mish and Sine-Mish Activation Functions')
plt.xlabel('x')
plt.ylabel('f(x)')
plt.legend()
plt.grid(True)
plt.show()