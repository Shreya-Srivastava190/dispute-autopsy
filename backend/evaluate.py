"""
Evaluates investigator.build_evidence_analysis against a held-out
synthetic test set (see eval_data.py for how that set — and its
ground truth — is generated, and the honesty notes about what this
can and can't claim).

Run with:
    python evaluate.py

This does NOT touch or import from main.py / disputes.json — it only
exercises the scoring engine itself, in isolation, against data that
was never used to design it.
"""

import json
from collections import defaultdict

from eval_data import generate_holdout_set
from investigator import build_evidence_analysis

LABELS = ["CONTEST", "REVIEW", "ACCEPT"]


def confusion_matrix(pairs: list[tuple[str, str]]) -> dict:
    """pairs = list of (predicted, actual)"""
    matrix = {p: {a: 0 for a in LABELS} for p in LABELS}
    for predicted, actual in pairs:
        matrix[predicted][actual] += 1
    return matrix


def precision_recall_f1(matrix: dict, label: str) -> dict:
    tp = matrix[label][label]
    fp = sum(matrix[label][a] for a in LABELS if a != label)
    fn = sum(matrix[p][label] for p in LABELS if p != label)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
    }


def run_evaluation(n: int = 200, seed: int = 42) -> dict:
    holdout = generate_holdout_set(n=n, seed=seed)

    pairs = []
    false_positive_cost = 0  # recommended CONTEST, actually shouldn't have
    false_negative_cost = 0  # recommended ACCEPT, actually should CONTEST

    for dispute, ground_truth in holdout:
        analysis = build_evidence_analysis(dispute)
        predicted = analysis["recommendation"]
        pairs.append((predicted, ground_truth))

        if predicted == "CONTEST" and ground_truth != "CONTEST":
            false_positive_cost += dispute["amount"]
        if predicted == "ACCEPT" and ground_truth == "CONTEST":
            false_negative_cost += dispute["amount"]

    matrix = confusion_matrix(pairs)
    accuracy = sum(1 for p, a in pairs if p == a) / len(pairs)

    per_class = {label: precision_recall_f1(matrix, label) for label in LABELS}

    ground_truth_distribution = defaultdict(int)
    for _, actual in pairs:
        ground_truth_distribution[actual] += 1

    return {
        "n": n,
        "seed": seed,
        "accuracy": round(accuracy, 3),
        "confusion_matrix": matrix,
        "per_class_metrics": per_class,
        "ground_truth_distribution": dict(ground_truth_distribution),
        "false_positive_cost_inr": false_positive_cost,
        "false_negative_cost_inr": false_negative_cost,
    }


def print_report(report: dict) -> None:
    print(f"Held-out evaluation — n={report['n']}, seed={report['seed']}")
    print(f"Overall accuracy: {report['accuracy'] * 100:.1f}%")
    print()

    print("Ground truth distribution:")
    for label, count in report["ground_truth_distribution"].items():
        print(f"  {label}: {count}")
    print()

    print("Confusion matrix (rows = predicted, columns = actual):")
    header = "             " + "".join(f"{a:>10}" for a in LABELS)
    print(header)
    for predicted in LABELS:
        row = "".join(
            f"{report['confusion_matrix'][predicted][a]:>10}" for a in LABELS
        )
        print(f"{predicted:>12} {row}")
    print()

    print("Per-class precision / recall / F1:")
    for label in LABELS:
        m = report["per_class_metrics"][label]
        print(
            f"  {label:>8}: precision={m['precision']:.3f}  "
            f"recall={m['recall']:.3f}  f1={m['f1']:.3f}  "
            f"(tp={m['true_positives']}, fp={m['false_positives']}, "
            f"fn={m['false_negatives']})"
        )
    print()

    print(
        f"False-positive cost (recommended CONTEST, shouldn't have): "
        f"₹{report['false_positive_cost_inr']:,}"
    )
    print(
        f"False-negative cost (recommended ACCEPT, should've CONTESTed): "
        f"₹{report['false_negative_cost_inr']:,}"
    )


if __name__ == "__main__":
    report = run_evaluation(n=200, seed=42)
    print_report(report)

    with open("eval_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print("\nFull report written to eval_report.json")