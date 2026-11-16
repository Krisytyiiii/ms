"""On-device export contract: the portable math must equal sklearn.

`export_mobile.py` re-implements scaler + RBF + one-vs-one + Platt coupling in
plain NumPy. Dart runs the same steps from `svm_mobile.bin`. If these tests
pass, the Dart port has a reference to match; if they fail, the export is not
safe to ship.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pytest

from export_mobile import (
    check,
    multiclass_probability,
    ovo_decision,
    portable_predict,
)

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"
JOBLIB = ARTIFACTS / "v1" / "svm_seagrass_v1.joblib"

pytestmark = pytest.mark.skipif(not JOBLIB.is_file(), reason="locked v1 joblib not present")


@pytest.fixture(scope="module")
def pipeline():
    return joblib.load(JOBLIB)


def test_portable_matches_sklearn(pipeline) -> None:
    result = check(pipeline, n_samples=128)
    assert result["label_mismatches"] == 0
    assert result["max_proba_abs_diff"] < 1e-9


def test_probabilities_sum_to_one(pipeline) -> None:
    rng = np.random.default_rng(7)
    scaler = pipeline.named_steps["scaler"]
    x = rng.normal(scaler.mean_, scaler.scale_, size=(16, scaler.mean_.shape[0]))
    _, proba = portable_predict(pipeline, x)
    assert np.allclose(proba.sum(axis=1), 1.0, atol=1e-9)


def test_multiclass_probability_is_a_distribution() -> None:
    rng = np.random.default_rng(3)
    pairwise = rng.uniform(0.0, 1.0, size=8 * 7 // 2)
    p = multiclass_probability(pairwise, 8)
    assert p.shape == (8,)
    assert np.all(p >= 0.0)
    assert abs(float(p.sum()) - 1.0) < 1e-9


def test_ovo_decision_shape(pipeline) -> None:
    svm = pipeline.named_steps["svm"]
    kernel = np.ones((5, svm.support_vectors_.shape[0]))
    decision = ovo_decision(kernel, svm.dual_coef_, svm.intercept_, svm.n_support_)
    n_classes = len(svm.classes_)
    assert decision.shape == (5, n_classes * (n_classes - 1) // 2)


def test_bin_matches_metadata_if_exported() -> None:
    bin_path = ARTIFACTS / "v1" / "svm_mobile.bin"
    meta_path = ARTIFACTS / "v1" / "svm_mobile.json"
    if not bin_path.is_file() or not meta_path.is_file():
        pytest.skip("run export_mobile.py first")

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    flat = np.fromfile(bin_path, dtype="<f4")
    spec = meta["svm"]
    expected = (
        meta["scaler"]["n_features"] * 2
        + spec["n_support_vectors"] * meta["feature_spec"]["length"]
        + (spec["n_classes"] - 1) * spec["n_support_vectors"]
        + spec["n_pairs"] * 3
    )
    assert flat.size == expected, "svm_mobile.bin size does not match svm_mobile.json"
