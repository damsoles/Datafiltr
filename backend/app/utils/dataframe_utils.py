import re
import unicodedata

import pandas as pd


def normalize_header_name(value):
    if value is None:
        return ""

    if isinstance(value, float) and pd.isna(value):
        return ""

    text = str(value).strip().replace("\ufeff", "")
    if text == "" or text.lower() in {"nan", "null", "none", "n/a", "unnamed"}:
        return ""

    text = re.sub(r"\s+", " ", text)
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.casefold()


def is_unnamed_header(value):
    normalized = normalize_header_name(value)
    if normalized == "":
        return True
    if isinstance(value, str) and value.strip().lower().startswith("unnamed:"):
        return True
    return False


def ensure_columns(df, expected_columns):
    expected_norm = {normalize_header_name(col) for col in expected_columns if normalize_header_name(col)}
    actual_norm = {normalize_header_name(col) for col in df.columns if normalize_header_name(col)}

    missing = [col for col in expected_columns if normalize_header_name(col) not in actual_norm]
    unexpected = [
        col for col in df.columns
        if not is_unnamed_header(col) and normalize_header_name(col) and normalize_header_name(col) not in expected_norm
    ]
    return missing, unexpected
