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


def binary_metrics(pairs: list[tuple[str, str]]) -> dict:
    """
    Primary metric: CONTEST vs DO NOT CONTEST (REVIEW + ACCEPT collapsed
    into one negative class). This maps to the actual business decision
    Dispute Autopsy drives — whether a merchant submits a contest — and
    is the headline number, with the 3-class breakdown reported as a
    secondary diagnostic below it.
    """
    tp = fp = fn = tn = 0
    for predicted, actual in pairs:
        pred_positive = predicted == "CONTEST"
        actual_positive = actual == "CONTEST"
        if pred_positive and actual_positive:
            tp += 1
        elif pred_positive and not actual_positive:
            fp += 1
        elif not pred_positive and actual_positive:
            fn += 1
        else:
            tn += 1

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
        "true_negatives": tn,
    }


def run_evaluation(n: int = 200, seed: int = 42) -> dict:
    holdout = generate_holdout_set(n=n, seed=seed)

    pairs = []
    fp_exposure = 0  # recommended CONTEST, actually shouldn't have
    fp_exposure_count = 0
    fn_exposure = 0  # recommended ACCEPT, actually should CONTEST
    fn_exposure_count = 0

    for dispute, ground_truth in holdout:
        analysis = build_evidence_analysis(dispute)
        predicted = analysis["recommendation"]
        pairs.append((predicted, ground_truth))

        if predicted == "CONTEST" and ground_truth != "CONTEST":
            fp_exposure += dispute["amount"]
            fp_exposure_count += 1
        if predicted == "ACCEPT" and ground_truth == "CONTEST":
            fn_exposure += dispute["amount"]
            fn_exposure_count += 1

    matrix = confusion_matrix(pairs)
    accuracy = sum(1 for p, a in pairs if p == a) / len(pairs)

    per_class = {label: precision_recall_f1(matrix, label) for label in LABELS}
    primary = binary_metrics(pairs)

    ground_truth_distribution = defaultdict(int)
    for _, actual in pairs:
        ground_truth_distribution[actual] += 1

    return {
        "n": n,
        "seed": seed,
        "primary_metric": {
            "description": "CONTEST vs DO NOT CONTEST (REVIEW + ACCEPT collapsed)",
            **primary,
        },
        "secondary_3class_accuracy": round(accuracy, 3),
        "confusion_matrix": matrix,
        "per_class_metrics": per_class,
        "ground_truth_distribution": dict(ground_truth_distribution),
        "false_positive_disputed_value_exposure_inr": fp_exposure,
        "false_positive_case_count": fp_exposure_count,
        "false_negative_disputed_value_exposure_inr": fn_exposure,
        "false_negative_case_count": fn_exposure_count,
        "exposure_disclaimer": (
            "These are disputed-value exposure proxies on synthetic "
            "ground truth, not measured real-world financial loss."
        ),
    }


def run_multi_seed_evaluation(n: int = 200, seeds: list[int] = [42, 43, 44]) -> dict:
    """
    Runs the same evaluation across multiple seeds and reports the
    range, not just one lucky/unlucky draw — for reproducibility.
    """
    runs = [run_evaluation(n=n, seed=s) for s in seeds]
    primary_precisions = [r["primary_metric"]["precision"] for r in runs]
    primary_recalls = [r["primary_metric"]["recall"] for r in runs]
    primary_f1s = [r["primary_metric"]["f1"] for r in runs]

    return {
        "seeds": seeds,
        "n_per_seed": n,
        "runs": runs,
        "primary_metric_summary": {
            "precision_mean": round(sum(primary_precisions) / len(seeds), 3),
            "precision_range": [min(primary_precisions), max(primary_precisions)],
            "recall_mean": round(sum(primary_recalls) / len(seeds), 3),
            "recall_range": [min(primary_recalls), max(primary_recalls)],
            "f1_mean": round(sum(primary_f1s) / len(seeds), 3),
            "f1_range": [min(primary_f1s), max(primary_f1s)],
        },
    }


def print_report(report: dict) -> None:
    print(f"Held-out evaluation — n={report['n']}, seed={report['seed']}")
    print()

    pm = report["primary_metric"]
    print(f"PRIMARY METRIC — {pm['description']}")
    print(
        f"  precision={pm['precision']:.3f}  recall={pm['recall']:.3f}  "
        f"f1={pm['f1']:.3f}"
    )
    print(
        f"  (tp={pm['true_positives']}, fp={pm['false_positives']}, "
        f"fn={pm['false_negatives']}, tn={pm['true_negatives']})"
    )
    print()

    print(f"Secondary 3-class accuracy: {report['secondary_3class_accuracy'] * 100:.1f}%")
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

    print("Per-class precision / recall / F1 (secondary diagnostic):")
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
        f"False-positive disputed-value exposure: "
        f"₹{report['false_positive_disputed_value_exposure_inr']:,} "
        f"across {report['false_positive_case_count']} cases"
    )
    print(
        f"False-negative disputed-value exposure: "
        f"₹{report['false_negative_disputed_value_exposure_inr']:,} "
        f"across {report['false_negative_case_count']} cases"
    )
    print(f"  ({report['exposure_disclaimer']})")


def print_multi_seed_report(report: dict) -> None:
    print(f"Multi-seed evaluation — seeds={report['seeds']}, n={report['n_per_seed']} each")
    print()
    s = report["primary_metric_summary"]
    print("Primary metric (CONTEST vs DO NOT CONTEST) across seeds:")
    print(f"  precision: mean={s['precision_mean']:.3f}  range={s['precision_range']}")
    print(f"  recall:    mean={s['recall_mean']:.3f}  range={s['recall_range']}")
    print(f"  f1:        mean={s['f1_mean']:.3f}  range={s['f1_range']}")


if __name__ == "__main__":
    report = run_evaluation(n=200, seed=42)
    print_report(report)

    print("\n" + "=" * 60 + "\n")

    multi = run_multi_seed_evaluation(n=200, seeds=[42, 43, 44])
    print_multi_seed_report(multi)

    with open("eval_report.json", "w") as f:
        json.dump({"single_seed": report, "multi_seed": multi}, f, indent=2)
    print("\nFull report written to eval_report.json")