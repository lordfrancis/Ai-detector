"""Runtime configuration loading for AWARE Local."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


DEFAULT_SCORING_CONFIG_PATH = Path("config/scoring_config.yaml")

DEFAULT_SCORING_CONFIG: dict[str, Any] = {
    "risk_bands": {
        "low_max": 20,
        "moderate_max": 50,
        "high_max": 80,
    },
    "calibration": {
        "multiplier": 5,
    },
    "severity_weights": {
        "low": 1,
        "medium": 3,
        "high": 5,
    },
}


def get_scoring_config(path: str | Path | None = None) -> dict[str, Any]:
    """Return normalized scoring config, falling back to current defaults."""
    config_path = Path(
        path or os.environ.get("AWARE_SCORING_CONFIG", DEFAULT_SCORING_CONFIG_PATH)
    )
    return _load_scoring_config(str(config_path))


def clear_scoring_config_cache() -> None:
    """Clear cached config; useful for tests that swap config paths."""
    _load_scoring_config.cache_clear()


@lru_cache(maxsize=8)
def _load_scoring_config(path: str) -> dict[str, Any]:
    config = _deep_copy(DEFAULT_SCORING_CONFIG)
    config_path = Path(path)

    if not config_path.exists():
        return config

    with config_path.open("r", encoding="utf-8") as file:
        loaded = yaml.safe_load(file) or {}

    if not isinstance(loaded, dict):
        return config

    _merge_config(config, _normalize_legacy_config(loaded))
    return config


def _normalize_legacy_config(config: dict[str, Any]) -> dict[str, Any]:
    if "risk_bands" in config:
        return config

    risk_levels = config.get("risk_levels")
    if not isinstance(risk_levels, dict):
        return config

    normalized = dict(config)
    normalized["risk_bands"] = {
        "low_max": _nested_number(risk_levels, "low", "max", 20),
        "moderate_max": _nested_number(risk_levels, "moderate", "max", 50),
        "high_max": _nested_number(risk_levels, "high", "max", 80),
    }
    return normalized


def _merge_config(base: dict[str, Any], updates: dict[str, Any]) -> None:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge_config(base[key], value)
        else:
            base[key] = value


def _nested_number(
    values: dict[str, Any],
    outer_key: str,
    inner_key: str,
    default: int | float,
) -> int | float:
    outer_value = values.get(outer_key, {})
    if not isinstance(outer_value, dict):
        return default
    value = outer_value.get(inner_key, default)
    if isinstance(value, int | float):
        return value
    return default


def _deep_copy(value: dict[str, Any]) -> dict[str, Any]:
    return {
        key: _deep_copy(item) if isinstance(item, dict) else item
        for key, item in value.items()
    }
