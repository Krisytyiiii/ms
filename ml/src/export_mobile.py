"""Export the trained SVM to a phone-portable artifact (no sklearn at runtime).

Writes two files next to the joblib:

    svm_mobile.json   metadata: label map, scaler, SVC params, feature spec, threshold
    svm_mobile.bin    float32 little-endian: scaler mean/scale, support vectors,
                      dual coefficients, intercepts, Platt A/B

The layout is documented in ``MOBILE_LAYOUT`` so the Dart reader cannot drift.

The self-check re-implements the portable math in pure NumPy -- scaler, RBF
kernel, one-vs-one decision values, Platt sigmoid, Wu-Lin-Weng multiclass
coupling -- and asserts it matches ``sklearn`` on random vectors. That is the
same math the Dart code will run, so a pass here is the contract.

    .venv\\Scripts\\python.exe ml\\src\\export_mobile.py
"""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import joblib
import numpy as np

# SVC(probability=True) is deprecated in sklearn 1.9 but is what the locked
# model used. The export reads probA_/probB_, so the warning is expected noise.
warnings.filterwarnings("ignore", category=FutureWarning, message=".*probA_.*")
warnings.filterwarnings("ignore", category=FutureWarning, message=".*probB_.*")

MOBILE_LAYOUT = {
    "dtype": "float32",
    "order": "little-endian, C-contiguous",
    "blocks": [
        {"name": "scaler_mean", "shape": ["n_features"]},
        {"name": "scaler_scale", "shape": ["n_features"]},
        {"name": "support_vectors", "shape": ["n_support_vectors", "n_features"]},
        {"name": "dual_coef", "shape": ["n_classes - 1", "n_support_vectors"]},
        {"name": "intercept", "shape": ["n_pairs"]},
        {"name": "probA", "shape": ["n_pairs"]},
        {"name": "probB", "shape": ["n_pairs"]},
    ],
}


def _unpack(pipeline):
    scaler = pipeline.named_steps.get("scaler")
    svm = pipeline.named_steps.get("svm")
    if scaler is None or svm is None:
        raise SystemExit("expected a Pipeline with 'scaler' and 'svm' steps")
    return scaler, svm


def _rbf(x: np.ndarray, sv: np.ndarray, gamma: float) -> np.ndarray:
    """Squared-distance RBF kernel, matching libsvm: exp(-gamma * ||x - sv||^2)."""
    xx = np.sum(x * x, axis=1)[:, None]
    ss = np.sum(sv * sv, axis=1)[None, :]
    dist = xx + ss - 2.0 * (x @ sv.T)
    return np.exp(-gamma * np.maximum(dist, 0.0))


def _starts(n_support: np.ndarray) -> np.ndarray:
    return np.concatenate([[0], np.cumsum(n_support)])


def ovo_decision(
    kernel: np.ndarray,
    dual_coef: np.ndarray,
    intercept: np.ndarray,
    n_support: np.ndarray,
) -> np.ndarray:
    """Pairwise (one-vs-one) decision values in sklearn's (i<j) pair order."""
    starts = _starts(n_support)
    n_classes = len(n_support)
    rows = []
    pair = 0
    for i in range(n_classes):
        for j in range(i + 1, n_classes):
            left = kernel[:, starts[i] : starts[i + 1]] @ dual_coef[j - 1, starts[i] : starts[i + 1]]
            right = kernel[:, starts[j] : starts[j + 1]] @ dual_coef[i, starts[j] : starts[j + 1]]
            rows.append(left + right + intercept[pair])
            pair += 1
    return np.stack(rows, axis=1)


def _sigmoid_pairs(decision: np.ndarray, prob_a: np.ndarray, prob_b: np.ndarray) -> np.ndarray:
    """Pairwise probability that the first class of each pair wins."""
    return 1.0 / (1.0 + np.exp(prob_a * decision + prob_b))


def multiclass_probability(pairwise: np.ndarray, n_classes: int) -> np.ndarray:
    """Wu-Lin-Weng coupling, as implemented by libsvm.

    ``pairwise`` holds r[i][j] = P(i beats j) for i < j, flattened in
    sklearn's pair order.
    """
    r = np.zeros((n_classes, n_classes))
    pair = 0
    for i in range(n_classes):
        for j in range(i + 1, n_classes):
            r[i, j] = pairwise[pair]
            r[j, i] = 1.0 - pairwise[pair]
            pair += 1

    eps = 0.005 / n_classes
    max_iter = max(100, n_classes)
    p = np.full(n_classes, 1.0 / n_classes)

    # Q as built by libsvm's multiclass_probability.
    q = np.zeros((n_classes, n_classes))
    for t in range(n_classes):
        for j in range(t):
            q[t, t] += r[j, t] * r[j, t]
            q[t, j] = q[j, t]
        for j in range(t + 1, n_classes):
            q[t, t] += r[j, t] * r[j, t]
            q[t, j] = -r[j, t] * r[t, j]

    for _ in range(max_iter):
        qp = q @ p
        p_qp = float(p @ qp)
        if float(np.max(np.abs(qp - p_qp))) < eps:
            break

        for t in range(n_classes):
            diff = (-qp[t] + p_qp) / q[t, t]
            p[t] += diff
            p_qp = (p_qp + diff * (diff * q[t, t] + 2.0 * qp[t])) / (1.0 + diff) / (1.0 + diff)
            qp = (qp + diff * q[t, :]) / (1.0 + diff)
            p = p / (1.0 + diff)

    p = np.maximum(p, 0.0)
    total = float(p.sum())
    return p / total if total else np.full(n_classes, 1.0 / n_classes)


def portable_predict(pipeline, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Scaler -> RBF -> OVO -> Platt -> coupling, using only NumPy."""
    scaler, svm = _unpack(pipeline)
    scaled = (x - scaler.mean_) / scaler.scale_
    kernel = _rbf(scaled, svm.support_vectors_, float(svm._gamma))
    decision = ovo_decision(kernel, svm.dual_coef_, svm.intercept_, svm.n_support_)
    pairwise = _sigmoid_pairs(decision, svm.probA_, svm.probB_)
    proba = np.stack(
        [multiclass_probability(row, len(svm.classes_)) for row in pairwise],
        axis=0,
    )
    votes = _ovo_votes(decision, len(svm.classes_))
    return np.asarray(svm.classes_)[votes], proba


def _ovo_votes(decision: np.ndarray, n_classes: int) -> np.ndarray:
    """libsvm voting: for each pair the higher decision value wins one vote."""
    votes = np.zeros((decision.shape[0], n_classes), dtype=np.int64)
    pair = 0
    for i in range(n_classes):
        for j in range(i + 1, n_classes):
            win_i = decision[:, pair] > 0
            votes[win_i, i] += 1
            votes[~win_i, j] += 1
            pair += 1
    return np.argmax(votes, axis=1)


def build_metadata(pipeline, feature_spec: dict, threshold: float, label_map: dict) -> dict:
    scaler, svm = _unpack(pipeline)
    n_classes = len(svm.classes_)
    return {
        "format": "marinesee-svm-mobile",
        "format_version": 1,
        "feature_spec": feature_spec,
        "classes": [str(c) for c in svm.classes_],
        "label_map": label_map,
        "retake_threshold": threshold,
        "scaler": {
            "with_mean": bool(scaler.with_mean),
            "with_std": bool(scaler.with_std),
            "n_features": int(scaler.mean_.shape[0]),
        },
        "svm": {
            "kernel": "rbf",
            "gamma": float(svm._gamma),
            "C": float(svm.C),
            "degree": int(svm.degree),
            "coef0": float(svm.coef0),
            "n_classes": n_classes,
            "n_pairs": n_classes * (n_classes - 1) // 2,
            "n_support": [int(n) for n in svm.n_support_],
            "n_support_vectors": int(svm.support_vectors_.shape[0]),
            "probability": "platt + wu-lin-weng coupling",
        },
        "predict_rule": (
            "slug = argmax of one-vs-one votes (sklearn predict); "
            "confidence = coupled probability of that slug (sklearn predict_proba). "
            "These can disagree; keep both, as ml/src/identify.py does."
        ),
        "layout": MOBILE_LAYOUT,
    }


def pack(pipeline) -> np.ndarray:
    """Flatten every float32 block in ``MOBILE_LAYOUT`` order."""
    scaler, svm = _unpack(pipeline)
    blocks = [
        scaler.mean_,
        scaler.scale_,
        svm.support_vectors_,
        svm.dual_coef_,
        svm.intercept_,
        svm.probA_,
        svm.probB_,
    ]
    return np.concatenate([np.asarray(b, dtype="<f4").ravel() for b in blocks])


def check(pipeline, n_samples: int = 64, seed: int = 42, tol: float = 1e-9) -> dict:
    """Prove the portable math reproduces sklearn on random feature vectors."""
    scaler, svm = _unpack(pipeline)
    rng = np.random.default_rng(seed)
    mean, std = scaler.mean_, scaler.scale_
    x = rng.normal(mean, std, size=(n_samples, mean.shape[0]))

    want_proba = svm.predict_proba((x - mean) / std)
    want_label = svm.predict((x - mean) / std)
    got_label, got_proba = portable_predict(pipeline, x)

    proba_diff = float(np.max(np.abs(want_proba - got_proba)))
    label_diff = int(np.sum(np.asarray(want_label) != got_label))
    return {
        "samples": n_samples,
        "max_proba_abs_diff": proba_diff,
        "label_mismatches": label_diff,
        "tolerance": tol,
        "passed": proba_diff <= tol and label_diff == 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", default="ml/artifacts")
    parser.add_argument("--version", default="v1")
    parser.add_argument("--out", default=None, help="output stem; defaults next to the joblib")
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help=(
            "retake threshold written into the export. Defaults to the "
            "version's metrics.json, then 0.20. Pass the frozen study value "
            "explicitly when the version's metrics file has no threshold, so "
            "the phone gates on a recorded decision instead of the fallback."
        ),
    )
    args = parser.parse_args()

    root = Path(args.artifacts) / args.version
    joblib_path = root / f"svm_seagrass_{args.version}.joblib"
    if not joblib_path.is_file():
        raise SystemExit(f"missing {joblib_path}")

    pipeline = joblib.load(joblib_path)
    feature_spec = json.loads((root / "feature_spec.json").read_text(encoding="utf-8"))
    metrics = json.loads((root / "metrics.json").read_text(encoding="utf-8"))
    label_map_path = root / "label_map.json"
    label_map = (
        json.loads(label_map_path.read_text(encoding="utf-8"))
        if label_map_path.is_file()
        else {}
    )
    threshold = float(metrics.get("retake_threshold", 0.20))
    if args.threshold is not None:
        threshold = float(args.threshold)
        source = "explicit --threshold"
        print(f"retake threshold: {threshold} (explicit --threshold)")
    elif "retake_threshold" in metrics:
        source = f"{root / 'metrics.json'}:retake_threshold"
    else:
        source = "0.20 fallback: metrics.json has no retake_threshold"
        print(f"retake threshold: {threshold} ({source})")

    result = check(pipeline)
    print("portable check:", json.dumps(result))
    if not result["passed"]:
        raise SystemExit("portable math does not match sklearn; refusing to export")

    stem = Path(args.out) if args.out else root / "svm_mobile"
    meta = build_metadata(pipeline, feature_spec, threshold, label_map)
    meta["check"] = result
    meta["source"] = str(joblib_path)
    meta["retake_threshold_source"] = source

    bin_path = stem.with_suffix(".bin")
    json_path = stem.with_suffix(".json")
    pack(pipeline).tofile(bin_path)
    json_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {bin_path} ({bin_path.stat().st_size} bytes)")
    print(f"wrote {json_path}")
    print(f"classes: {meta['svm']['n_classes']}  support vectors: {meta['svm']['n_support_vectors']}")
    print(f"retake threshold: {threshold}")


if __name__ == "__main__":
    main()
