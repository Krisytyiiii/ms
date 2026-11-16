"""Disk cache for the slow, deterministic steps of a training run.

QC, dHash, and feature extraction each decode every photo, and a retrain that
only moves `C`, `gamma`, or a class weight should not pay for that again. Every
entry is keyed by the file's resolved path, mtime and size *plus* the parameters
that change the result (image size, feature version), so an edited or replaced
file misses the cache instead of returning a stale vector.

The cache holds derived data, so it lives outside the repo
(`~/.cache/marinesee` by default). `MARINESEE_CACHE` overrides the root and
`--no-cache` bypasses it. Deleting the folder is always safe.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import numpy as np

try:  # package import (train_curated.py, pytest from ml/)
    from .features import extract_vector
    from .phash import dhash
    from .preprocess import load_prepared, qc_path
except ImportError:  # `python cache.py` / direct script use from ml/src
    from features import extract_vector
    from phash import dhash
    from preprocess import load_prepared, qc_path


def default_root() -> Path:
    override = os.environ.get("MARINESEE_CACHE")
    return Path(override) if override else Path.home() / ".cache" / "marinesee"


class Cache:
    """Content-addressed store of arrays and short strings.

    `enabled=False` still counts hits and misses so a run can report how much
    the cache would have helped, but nothing is read or written.
    """

    def __init__(self, root: Path | None = None, enabled: bool = True) -> None:
        self.root = Path(root) if root is not None else default_root()
        self.enabled = enabled
        self.hits = 0
        self.misses = 0

    def key(self, path: Path, *parts: object) -> str:
        """Fingerprint a file plus the parameters that change the derived value."""
        stat = path.stat()
        raw = "|".join(
            [
                str(path.resolve()),
                str(stat.st_mtime_ns),
                str(stat.st_size),
                *(str(part) for part in parts),
            ]
        )
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()

    def _target(self, namespace: str, key: str, suffix: str) -> Path:
        return self.root / namespace / key[:2] / f"{key}{suffix}"

    def _store(self, target: Path, write) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".tmp")
        write(temporary)
        os.replace(temporary, target)

    def array(
        self,
        key: str,
        loader,
        namespace: str = "features",
    ) -> np.ndarray:
        target = self._target(namespace, key, ".npy")
        if self.enabled and target.is_file():
            try:
                self.hits += 1
                return np.load(target)
            except (OSError, ValueError):
                pass  # half-written or from an older numpy: recompute
        self.misses += 1
        value = np.asarray(loader())
        if self.enabled:

            def _write(temp: Path) -> None:
                # A file handle stops numpy appending a second ".npy".
                with temp.open("wb") as handle:
                    np.save(handle, value)

            self._store(target, _write)
        return value

    def text(self, key: str, loader, namespace: str = "qc") -> str:
        target = self._target(namespace, key, ".txt")
        if self.enabled and target.is_file():
            try:
                self.hits += 1
                return target.read_text(encoding="utf-8")
            except OSError:
                pass
        self.misses += 1
        value = str(loader())
        if self.enabled:
            self._store(
                target,
                lambda temp: temp.write_text(value, encoding="utf-8"),
            )
        return value

    def summary(self) -> dict:
        entries = self.hits + self.misses
        return {
            "enabled": self.enabled,
            "root": str(self.root),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / entries, 3) if entries else 0.0,
        }


def prepared(cache: Cache, path: Path, size: int) -> np.ndarray:
    """`load_prepared`, cached per file fingerprint and target size."""
    key = cache.key(path, "prepared", size)
    return cache.array(key, lambda: load_prepared(path, size=size), "prepared")


def vector(cache: Cache, path: Path, version: str, image=None) -> np.ndarray:
    """`extract_vector` on the prepared frame, cached per file and feature version."""
    key = cache.key(path, "feature", version)
    return cache.array(
        key,
        lambda: extract_vector(
            load_prepared(path) if image is None else image, version=version
        ),
        "features",
    )


def qc_reason(cache: Cache, path: Path) -> str | None:
    """`qc_path`, cached. The sentinel "-" means the frame passed QC."""
    key = cache.key(path, "qc")
    value = cache.text(key, lambda: qc_path(path) or "-")
    return None if value == "-" else value


def dhash_value(cache: Cache, path: Path) -> int:
    """`dhash`, cached as a one-element uint64 array."""
    key = cache.key(path, "dhash")
    return int(cache.array(key, lambda: [dhash(path)], "hashes")[0])
