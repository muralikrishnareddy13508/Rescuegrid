"""Synthetic-data DecisionTree baseline for donation urgency (not food-safety eligibility)."""
from functools import lru_cache
from datetime import datetime, timezone

import numpy as np
from sklearn.metrics import confusion_matrix, f1_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

FEATURE_NAMES = ["hours_until_expiry", "quantity", "category_code"]


def _synthetic_dataset(seed: int = 42, n: int = 1200):
    rng = np.random.default_rng(seed)
    hours = rng.uniform(0.1, 120, n)
    quantity = rng.uniform(1, 300, n)
    category = rng.integers(0, 7, n)
    # Synthetic labels are deliberately generated from a documented rule plus noise.
    base = np.where(hours <= 6, 2, np.where(hours <= 24, 1, 0))
    # Small synthetic variation avoids a perfectly deterministic threshold-only dataset.
    noise = rng.random(n) < 0.08
    alt = rng.integers(0, 3, n)
    labels = np.where(noise, alt, base)
    X = np.column_stack([hours, quantity, category])
    return X, labels


@lru_cache(maxsize=1)
def _trained():
    X, y = _synthetic_dataset()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    model = DecisionTreeClassifier(max_depth=4, min_samples_leaf=12, random_state=42)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    metrics = {
        "dataset": "synthetic generated examples",
        "train_rows": int(len(y_train)),
        "test_rows": int(len(y_test)),
        "macro_f1": round(float(f1_score(y_test, pred, average="macro", zero_division=0)), 3),
        "class_recall": {"low": round(float(recall_score(y_test, pred, labels=[0], average="macro", zero_division=0)), 3),
                          "medium": round(float(recall_score(y_test, pred, labels=[1], average="macro", zero_division=0)), 3),
                          "high": round(float(recall_score(y_test, pred, labels=[2], average="macro", zero_division=0)), 3)},
        "confusion_matrix_labels": ["low", "medium", "high"],
        "confusion_matrix": confusion_matrix(y_test, pred, labels=[0, 1, 2]).tolist(),
        "warning": "Metrics measure a model trained and tested on synthetic labels, not real-world forecasting performance.",
    }
    return model, metrics


def predict(hours_until_expiry: float, quantity: float, category_code: int) -> dict:
    model, metrics = _trained()
    row = np.array([[max(0.0, hours_until_expiry), max(0.0, quantity), category_code]], dtype=float)
    label = int(model.predict(row)[0])
    probs = model.predict_proba(row)[0]
    return {
        "urgency": ["low", "medium", "high"][label],
        "probabilities": {"low": round(float(probs[0]), 3), "medium": round(float(probs[1]), 3), "high": round(float(probs[2]), 3)},
        "model": "DecisionTreeClassifier (max_depth=4)",
        "training_data": "synthetic",
        "metrics": metrics,
        "safety_note": "Urgency prediction only. Separate explicit safety rules determine whether a donation is eligible for matching.",
    }
