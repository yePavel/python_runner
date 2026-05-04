"""Diff engine – recursive comparison of MATLAB data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, List, Dict, Tuple

import numpy as np


# ── Models ──────────────────────────────────────────────────────────────────

class MatchStatus(Enum):
    MATCH = auto()
    MISMATCH = auto()
    TYPE_MISMATCH = auto()
    MISSING_IN_BASE = auto()
    MISSING_IN_NEW = auto()


@dataclass(frozen=True)
class Tolerance:
    atol: float = 1e-9
    rtol: float = 1e-6


@dataclass
class FieldDiff:
    field_path: str
    base_value: str
    new_value: str
    status: MatchStatus
    numeric_diff: str = ""


@dataclass
class ComparisonReport:
    comparator_name: str
    source_file: str
    diffs: list[FieldDiff] = field(default_factory=list)

    @property
    def has_mismatches(self) -> bool:
        return any(d.status != MatchStatus.MATCH for d in self.diffs)


# ── Diff Engine ─────────────────────────────────────────────────────────────

def compare_values(
    base: Any,
    new: Any,
    tolerance: Tolerance,
    path: str = "",
) -> list[FieldDiff]:
    """Recursively compare two values, returning a flat list of FieldDiff rows."""

    if isinstance(base, dict) and isinstance(new, dict):
        return _compare_dicts(base, new, tolerance, path)

    if isinstance(base, (list, tuple)) and isinstance(new, (list, tuple)):
        return _compare_sequences(base, new, tolerance, path)

    if isinstance(base, np.ndarray) and isinstance(new, np.ndarray):
        return _compare_arrays(base, new, tolerance, path)

    if _is_numeric(base) and _is_numeric(new):
        return [_compare_scalars(float(base), float(new), tolerance, path)]

    if isinstance(base, str) and isinstance(new, str):
        status = MatchStatus.MATCH if base == new else MatchStatus.MISMATCH
        return [FieldDiff(path, base, new, status)]

    return [FieldDiff(path, _short_repr(base), _short_repr(new), MatchStatus.TYPE_MISMATCH)]


def compare_extended_data(
    base: dict[str, Any],
    new: dict[str, Any],
    tolerance: Tolerance,
    source_file: str = "",
) -> ComparisonReport:
    """Compare the 'extended_data' field between two loaded MAT dicts."""
    has_base = "extended_data" in base
    has_new = "extended_data" in new

    if not has_base and not has_new:
        return ComparisonReport("extended_data", source_file, [
            FieldDiff("extended_data", "<missing>", "<missing>", MatchStatus.TYPE_MISMATCH)
        ])
    if not has_base:
        return ComparisonReport("extended_data", source_file, [
            FieldDiff("extended_data", "<missing>", "<present>", MatchStatus.MISSING_IN_BASE)
        ])
    if not has_new:
        return ComparisonReport("extended_data", source_file, [
            FieldDiff("extended_data", "<present>", "<missing>", MatchStatus.MISSING_IN_NEW)
        ])

    diffs = compare_values(base["extended_data"], new["extended_data"], tolerance, "extended_data")
    return ComparisonReport("extended_data", source_file, diffs)


# ── Internal Helpers ────────────────────────────────────────────────────────

def _compare_dicts(base, new, tolerance, path):
    results = []
    for key in sorted(set(base.keys()) | set(new.keys())):
        child = f"{path}.{key}" if path else key
        if key not in base:
            results.append(FieldDiff(child, "<missing>", _short_repr(new[key]), MatchStatus.MISSING_IN_BASE))
        elif key not in new:
            results.append(FieldDiff(child, _short_repr(base[key]), "<missing>", MatchStatus.MISSING_IN_NEW))
        else:
            results.extend(compare_values(base[key], new[key], tolerance, child))
    return results


def _compare_sequences(base, new, tolerance, path):
    results = []
    for i in range(max(len(base), len(new))):
        child = f"{path}[{i}]"
        if i >= len(base):
            results.append(FieldDiff(child, "<missing>", _short_repr(new[i]), MatchStatus.MISSING_IN_BASE))
        elif i >= len(new):
            results.append(FieldDiff(child, _short_repr(base[i]), "<missing>", MatchStatus.MISSING_IN_NEW))
        else:
            results.extend(compare_values(base[i], new[i], tolerance, child))
    return results


def _compare_arrays(base, new, tolerance, path):
    if base.shape != new.shape:
        return [FieldDiff(path, f"array{base.shape}", f"array{new.shape}", MatchStatus.MISMATCH, "shape mismatch")]

    if base.dtype == object or new.dtype == object:
        results = []
        for idx in range(base.size):
            child = f"{path}[{idx}]" if base.size > 1 else path
            results.extend(compare_values(base.flat[idx], new.flat[idx], tolerance, child))
        return results

    if base.dtype.kind in ("U", "S") or new.dtype.kind in ("U", "S"):
        status = MatchStatus.MATCH if np.array_equal(base, new) else MatchStatus.MISMATCH
        return [FieldDiff(path, _short_repr(base), _short_repr(new), status)]

    try:
        close = np.allclose(base, new, atol=tolerance.atol, rtol=tolerance.rtol, equal_nan=True)
    except TypeError:
        close = np.array_equal(base, new)

    if close:
        return [FieldDiff(path, _short_repr(base), _short_repr(new), MatchStatus.MATCH)]

    if base.size <= 20:
        results = []
        for idx in np.ndindex(base.shape):
            child = f"{path}[{','.join(map(str, idx))}]"
            results.append(_compare_scalars(float(base[idx]), float(new[idx]), tolerance, child))
        return results

    max_diff = float(np.nanmax(np.abs(base - new)))
    return [FieldDiff(path, f"array{base.shape}", f"array{new.shape}", MatchStatus.MISMATCH, f"max |Δ| = {max_diff:.6e}")]


def _compare_scalars(base_val, new_val, tolerance, path):
    close = bool(np.isclose(base_val, new_val, atol=tolerance.atol, rtol=tolerance.rtol, equal_nan=True))
    diff_str = "" if close else f"Δ = {new_val - base_val:.6e}"
    return FieldDiff(path, f"{base_val}", f"{new_val}", MatchStatus.MATCH if close else MatchStatus.MISMATCH, diff_str)


def _is_numeric(value):
    if isinstance(value, (int, float, complex)):
        return True
    if isinstance(value, np.generic) and np.issubdtype(type(value), np.number):
        return True
    return False


def _short_repr(value, max_len=80):
    if isinstance(value, np.ndarray):
        text = np.array2string(value, separator=", ") if value.size <= 6 else f"array{value.shape}"
        return text[:max_len]
    text = repr(value)
    return text[:max_len - 3] + "..." if len(text) > max_len else text
