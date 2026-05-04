"""MAT file loader – auto-detects v7.2 vs v7.3 (HDF5)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import scipy.io as sio

logger = logging.getLogger(__name__)

_SCIPY_META_KEYS = {"__header__", "__version__", "__globals__"}


def load(path: Path) -> dict[str, Any]:
    """Load a .mat file and return its contents as a plain dict.

    Auto-detects v7.2 (scipy) vs v7.3+ (mat73/HDF5).
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"MAT file not found: {path}")

    # Try scipy first (v4 – v7.2).
    try:
        raw = sio.loadmat(str(path), squeeze_me=True, struct_as_record=False)
        return _clean_scipy_dict(raw)
    except NotImplementedError:
        pass

    # Fall back to mat73 for v7.3+.
    try:
        import mat73
        raw = mat73.loadmat(str(path))
        return dict(raw)
    except Exception as exc:
        raise ValueError(f"Cannot read MAT file {path}: {exc}") from exc


def load_folder(folder: Path) -> dict[str, dict[str, Any]]:
    """Load all .mat files in *folder* (non-recursive).

    Returns dict mapping filename stem to loaded contents.
    """
    if not folder.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder}")
    result: dict[str, dict[str, Any]] = {}
    for mat_file in sorted(folder.glob("*.mat")):
        try:
            result[mat_file.stem] = load(mat_file)
        except (ValueError, FileNotFoundError) as exc:
            logger.warning("Skipping %s: %s", mat_file.name, exc)
    return result


def _clean_scipy_dict(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        key: _convert_value(value)
        for key, value in raw.items()
        if key not in _SCIPY_META_KEYS
    }


def _convert_value(value: Any) -> Any:
    if hasattr(value, "_fieldnames"):
        return {
            fname: _convert_value(getattr(value, fname))
            for fname in value._fieldnames
        }
    if isinstance(value, np.ndarray) and value.dtype == object:
        return np.array([_convert_value(v) for v in value.flat], dtype=object).reshape(value.shape)
    return value
