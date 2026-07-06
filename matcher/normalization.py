# matcher/normalization.py

import numpy as np


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def normalize_series(values):
    """
    Z-score + sigmoid normalization
    مناسب برای scoring features
    """
    values = np.array(values, dtype=float)

    mean = np.mean(values)
    std = np.std(values)

    if std == 0:
        return np.zeros_like(values)

    z = (values - mean) / std
    return sigmoid(z)