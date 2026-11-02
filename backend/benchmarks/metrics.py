"""Evaluation metrics for the Guardian AI benchmark suite."""

from typing import Dict, List, Sequence


def precision_recall_f1(tp: int, fp: int, fn: int) -> Dict[str, float]:
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


def accuracy(actual: Sequence[bool], predicted: Sequence[bool]) -> float:
    if len(actual) != len(predicted) or not actual:
        return 0.0
    return sum(a == p for a, p in zip(actual, predicted)) / len(actual)


def false_positive_rate(labels: Sequence[bool], predicted: Sequence[bool]) -> float:
    """FP rate among negative (benign) samples."""
    negatives = [(l, p) for l, p in zip(labels, predicted) if not l]
    if not negatives:
        return 0.0
    fps = sum(1 for _, p in negatives if p)
    return fps / len(negatives)


def false_negative_rate(labels: Sequence[bool], predicted: Sequence[bool]) -> float:
    positives = [(l, p) for l, p in zip(labels, predicted) if l]
    if not positives:
        return 0.0
    fns = sum(1 for _, p in positives if not p)
    return fns / len(positives)


def classify_binary(scores: Sequence[float], threshold: float) -> List[bool]:
    return [s >= threshold for s in scores]


def class_report(labels: Sequence[bool], predicted: Sequence[bool]) -> Dict[str, float]:
    tp = sum(1 for l, p in zip(labels, predicted) if l and p)
    fp = sum(1 for l, p in zip(labels, predicted) if not l and p)
    fn = sum(1 for l, p in zip(labels, predicted) if l and not p)
    tn = sum(1 for l, p in zip(labels, predicted) if not l and not p)

    prf = precision_recall_f1(tp, fp, fn)
    return {
        **prf,
        "accuracy": round(accuracy(labels, predicted), 4),
        "false_positive_rate": round(false_positive_rate(labels, predicted), 4),
        "false_negative_rate": round(false_negative_rate(labels, predicted), 4),
        "support": len(labels),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    }
