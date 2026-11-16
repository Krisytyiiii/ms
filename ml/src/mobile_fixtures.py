"""Write Dart parity fixtures: prepared 256px PNG + the vector Python computes.

The Dart port in `app/lib/classify/local/` must reproduce both. Fixtures are
small PNGs plus JSON, so they can live in `app/test/fixtures/` without images
from Drive.

    .venv\\Scripts\\python.exe ml\\src\\mobile_fixtures.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

try:
    from .features import extract_vector
    from .preprocess import prepare_rgb
except ImportError:
    from features import extract_vector
    from preprocess import prepare_rgb

SOURCES: tuple[str, ...] = ()

_MODEL = None


def _predict(vector: np.ndarray) -> dict | None:
    """sklearn's answer, so the Dart port can be graded on decisions, not just floats."""
    global _MODEL
    if _MODEL is None:
        path = Path(__file__).resolve().parents[1] / "artifacts" / "v1" / "svm_seagrass_v1.joblib"
        if not path.is_file():
            return None
        import joblib

        _MODEL = joblib.load(path)
    row = np.asarray(vector, dtype=np.float64).reshape(1, -1)
    proba = _MODEL.predict_proba(row)[0]
    classes = [str(c) for c in _MODEL.classes_]
    pred = str(_MODEL.predict(row)[0])
    # `predict` (votes) and `predict_proba` (coupled probabilities) can name
    # different classes. `identify.py` reports the vote winner, with the
    # probability of *that* class as the confidence -- not `proba.max()`.
    # Recording the max here graded the Dart port against the wrong number.
    return {
        "slug": pred,
        "confidence": float(proba[classes.index(pred)]),
        "proba_top_slug": classes[int(proba.argmax())],
        "proba_top": float(proba.max()),
    }


def _discover(image_dir: Path) -> list[Path]:
    """Every image in the folder, sorted, so the fixture set follows the assets."""
    if SOURCES:
        return [image_dir / n for n in SOURCES]
    found = [
        p
        for p in sorted(image_dir.iterdir())
        if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg"}
    ]
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images", default="app/assets/images/species")
    parser.add_argument("--out", default="app/test/fixtures")
    parser.add_argument("--version", default="v2")
    args = parser.parse_args()

    image_dir = Path(args.images)
    out = Path(args.out)
    (out / "prepared").mkdir(parents=True, exist_ok=True)

    manifest = []
    for src in _discover(image_dir):
        if not src.is_file():
            print(f"skip (missing): {src.name}")
            continue
        rgb = np.asarray(Image.open(src).convert("RGB"), dtype=np.uint8)
        prepared = prepare_rgb(rgb)
        slug_stem = src.stem
        Image.fromarray(prepared).save(out / "prepared" / f"{slug_stem}.png")
        vector = extract_vector(prepared, version=args.version)
        prediction = _predict(vector)
        manifest.append(
            {
                "id": slug_stem,
                "source": src.name,
                "prepared_png": f"prepared/{slug_stem}.png",
                "vector": [float(v) for v in vector],
                "vector_length": int(len(vector)),
                "feature_version": args.version,
                "sklearn_prediction": prediction,
            }
        )
        print(f"{slug_stem}: vector {len(vector)}")

    (out / "vectors.json").write_text(
        json.dumps(
            {
                "feature_version": args.version,
                "image_size": 256,
                "description": "prepared 256px RGB and the exact features.py vector",
                "items": manifest,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {out / 'vectors.json'} with {len(manifest)} items")


if __name__ == "__main__":
    main()
