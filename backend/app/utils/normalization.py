import math

import pandas as pd


def normalize_value(value):
    if value is None:
        return None

    if isinstance(value, float) and pd.isna(value):
        return None

    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned == "" or cleaned.lower() in {"nan", "n/a", "na", "null", "none"}:
            return None
        return cleaned

    return value


def normalize_ruc(value):
    if value is None:
        return None

    if isinstance(value, float) and pd.isna(value):
        return None

    normalized = normalize_value(value)
    if normalized is None:
        return None

    if isinstance(normalized, (int, float)):
        if pd.isna(normalized):
            return None
        normalized = str(int(normalized))

    normalized = str(normalized).strip()

    if normalized.isdigit() and len(normalized) < 6:
        return normalized.zfill(6)

    return normalized


def normalize_year(value):
    normalized = normalize_value(value)
    if normalized is None:
        return None
    if isinstance(normalized, str):
        try:
            return int(float(normalized))
        except ValueError:
            return None
    return int(normalized)
