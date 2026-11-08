"""Score one photo with the exported SVM.

Prefers `ml/artifacts/v2` when that export exists. Otherwise the locked v1 joblib.
The retake threshold is read from the model folder's metrics. The fallback is 0.20.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np

try:
    from .dataset_contract import TRAINABLE_SPECIES
    from .features import extract_vector
    from .preprocess import load_prepared, prepared_from_bytes
except ImportError:
    from dataset_contract import TRAINABLE_SPECIES
    from features import extract_vector
    from preprocess import load_prepared, prepared_from_bytes

# Fallback until a v2 metrics file carries a threshold frozen on validation.
# Chance for eight classes is 0.125.
LOW_CONFIDENCE = 0.20
STUDY_ACCEPTED_ACCURACY = 0.85
MIN_ACCEPTED_COVERAGE = 0.30
FALLBACK_COVERAGE = 0.50

_ACTIVE = {"version": "v2", "threshold": LOW_CONFIDENCE, "path": None}


def default_model_path() -> Path:
    here = Path(__file__).resolve()
    artifacts = here.parents[1] / "artifacts"
    candidates = (
        artifacts / "v2" / "svm_seagrass_v2.joblib",
        artifacts / "v1" / "svm_seagrass_v1.joblib",
        artifacts / "svm_seagrass_v1.joblib",
    )
    for cand in candidates:
        if cand.is_file():
            return cand
    raise FileNotFoundError("svm joblib not in ml/artifacts")


def _read_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def sidecar(model_path: Path) -> dict:
    spec = _read_json(model_path.parent / "feature_spec.json")
    metrics = _read_json(model_path.parent / "metrics.json")
    version = str(spec.get("version") or "v2")
    threshold = LOW_CONFIDENCE
    if "retake_threshold" in metrics:
        threshold = float(metrics["retake_threshold"])
    return {"version": version, "threshold": threshold, "path": str(model_path)}


def load_model(path: Path | None = None):
    model_path = path or default_model_path()
    _ACTIVE.update(sidecar(model_path))
    return joblib.load(model_path)


def acceptance(confidence: np.ndarray, correct: np.ndarray, threshold: float) -> dict:
    """Accuracy and coverage among photos whose top-class probability clears the threshold."""
    confidence = np.asarray(confidence, dtype=np.float64)
    correct = np.asarray(correct, dtype=bool)
    if len(confidence) == 0:
        return {"accepted": 0, "coverage": 0.0, "accuracy": None}
    accept = confidence >= threshold
    accepted = int(accept.sum())
    coverage = float(accept.mean())
    accuracy = float(correct[accept].mean()) if accepted else None
    return {"accepted": accepted, "coverage": coverage, "accuracy": accuracy}


def choose_retake_threshold(confidence: np.ndarray, correct: np.ndarray) -> dict:
    """Freeze a retake threshold on validation probabilities.

    The lowest threshold where accepted accuracy is at least 85% and at least
    30% of photos are accepted. When no threshold reaches 85%, the threshold
    with the best accepted accuracy that still keeps at least half the photos.
    """
    confidence = np.asarray(confidence, dtype=np.float64)
    correct = np.asarray(correct, dtype=bool)
    grid = [0.0, *[round(0.05 + 0.01 * step, 2) for step in range(95)]]
    rows = []
    for threshold in grid:
        stats = acceptance(confidence, correct, threshold)
        if stats["accuracy"] is None:
            continue
        rows.append({"threshold": threshold, **stats})

    meeting = [
        row
        for row in rows
        if row["accuracy"] >= STUDY_ACCEPTED_ACCURACY and row["coverage"] >= MIN_ACCEPTED_COVERAGE
    ]
    if meeting:
        chosen = min(meeting, key=lambda row: row["threshold"])
        return {**chosen, "study_line_met": True, "rule": "accepted accuracy >= 0.85 and coverage >= 0.30"}

    half = [row for row in rows if row["coverage"] >= FALLBACK_COVERAGE]
    if not rows:
        return {
            "threshold": LOW_CONFIDENCE,
            "accepted": 0,
            "coverage": 0.0,
            "accuracy": None,
            "study_line_met": False,
            "rule": "no validation probabilities",
        }
    pool = half or rows
    chosen = max(pool, key=lambda row: (row["accuracy"], row["coverage"], -row["threshold"]))
    rule = (
        "best accepted accuracy with coverage >= 0.50"
        if half
        else "no threshold kept half of validation"
    )
    return {**chosen, "study_line_met": False, "rule": rule}


def _score(rgb: np.ndarray, model) -> dict:
    vector = extract_vector(rgb, version=_ACTIVE["version"]).reshape(1, -1)
    pred = str(model.predict(vector)[0])
    proba = model.predict_proba(vector)[0]
    classes = [str(name) for name in model.classes_]
    ranked = sorted(zip(classes, proba.tolist()), key=lambda item: item[1], reverse=True)
    conf = float(dict(ranked)[pred])
    threshold = float(_ACTIVE["threshold"])
    return {
        "slug": pred,
        "predicted": pred,
        "confidence": conf,
        "low_confidence": conf < threshold,
        "retake_threshold": threshold,
        "known": pred in TRAINABLE_SPECIES,
        "top": [{"slug": slug, "p": float(p)} for slug, p in ranked[:3]],
    }


def identify_path(path: Path, model=None) -> dict:
    model = model or load_model()
    result = _score(load_prepared(path), model)
    result["path"] = str(path)
    return result


def identify_bytes(data: bytes, model=None) -> dict:
    model = model or load_model()
    return _score(prepared_from_bytes(data), model)


def main() -> None:
    parser = argparse.ArgumentParser(description="Identify one seagrass photo with the SVM.")
    parser.add_argument("image", type=Path)
    parser.add_argument("--model", type=Path, default=None)
    args = parser.parse_args()
    result = identify_path(args.image, model=load_model(args.model) if args.model else None)
    print(result["predicted"], f"{result['confidence']:.3f}")
    for row in result["top"]:
        print(f"  {row['slug']}  {row['p']:.3f}")


if __name__ == "__main__":
    main()
