from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.core.exceptions import DataValidationError
from app.utils.dataframe_utils import ensure_columns, is_unnamed_header, normalize_header_name
from app.utils.normalization import normalize_ruc, normalize_value, normalize_year

EXPECTED_COLUMNS = [
    "Número",
    "RUC",
    "Razón social",
    "Año de constitución",
    "Ciudad",
    "Provincia",
    "CIIU actividad principal",
    "Gerentes",
    "Hombres",
    "Mujeres",
    "Empresas",
    "Año",
    "Q de Tobin (%)",
    "ROA",
    "ROE",
    "Market to Book",
    "Dividend Payout",
    "Deuda financiera / Activo",
    "Cobertura de intereses",
    "CxC relacionadas / Total CxC",
    "Gastos administrativos / Ingresos",
    "CFO / Utilidad neta",
    "Apalancamiento",
    "Endeudamiento del activo",
    "Endeudamiento del patrimonio",
]


def detect_header_row(raw_df: pd.DataFrame):
    expected_norm = {normalize_header_name(col) for col in EXPECTED_COLUMNS if normalize_header_name(col)}
    best_index = 0
    best_score = -1

    for idx in range(len(raw_df)):
        row = raw_df.iloc[idx]
        values = [str(value).strip() if value is not None and not pd.isna(value) else "" for value in row]
        if not any(values):
            continue

        normalized_values = [normalize_header_name(value) for value in values if value != ""]
        matches = sum(1 for value in normalized_values if value in expected_norm)
        if matches > best_score:
            best_score = matches
            best_index = idx

    if best_score <= 0:
        return 0

    return best_index


def read_excel_file(file_path: str | Path):
    try:
        raw_df = pd.read_excel(file_path, header=None)
    except Exception as exc:
        raise DataValidationError(f"El archivo no es válido o está dañado: {exc}") from exc

    if raw_df.empty:
        raise DataValidationError("El archivo Excel está vacío.")

    header_row_index = detect_header_row(raw_df)
    header_row = raw_df.iloc[header_row_index].tolist()
    data_df = raw_df.iloc[header_row_index + 1:].copy()

    if data_df.empty:
        raise DataValidationError("El archivo Excel no contiene registros después de la cabecera.")

    valid_indexes = [idx for idx, col in enumerate(header_row) if not is_unnamed_header(col)]
    if not valid_indexes:
        raise DataValidationError("No se pudo detectar una fila válida de encabezados en el Excel.")

    selected_header = [header_row[idx] for idx in valid_indexes]
    data_df = data_df.iloc[:, valid_indexes]
    data_df = align_shifted_rows(raw_df.iloc[header_row_index + 1:].copy(), valid_indexes)
    data_df = data_df.iloc[:, valid_indexes]
    data_df.columns = canonicalize_headers(selected_header)

    missing_columns, unexpected_columns = ensure_columns(data_df, EXPECTED_COLUMNS)

    if missing_columns or unexpected_columns:
        details = []
        if missing_columns:
            details.append(f"Columnas faltantes: {missing_columns}")
        if unexpected_columns:
            details.append(f"Columnas inesperadas: {unexpected_columns}")
        raise DataValidationError("; ".join(details))

    df = normalize_dataframe(data_df)
    duplicate_rows = detect_duplicate_rows(df)

    return df, duplicate_rows


def canonicalize_headers(headers):
    expected_by_normalized = {
        normalize_header_name(column): column
        for column in EXPECTED_COLUMNS
    }
    aliases = {
        "ciiu actividad principal:": "CIIU actividad principal",
        "hombre": "Hombres",
        "market-to-book": "Market to Book",
        "cobertura intereses": "Cobertura de intereses",
        "gastos adm. / ingresos": "Gastos administrativos / Ingresos",
    }
    canonical_headers = []
    for header in headers:
        cleaned_header = str(header).strip().replace("\ufeff", "")
        normalized_header = normalize_header_name(cleaned_header)
        canonical_headers.append(
            aliases.get(
                normalized_header,
                expected_by_normalized.get(normalized_header, cleaned_header),
            )
        )
    return canonical_headers


def align_shifted_rows(data_df: pd.DataFrame, header_indexes: list[int]) -> pd.DataFrame:
    if not header_indexes or data_df.empty:
        return data_df

    first_header_index = min(header_indexes)
    last_header_index = max(header_indexes)
    width = len(header_indexes)
    aligned = data_df.copy()

    for row_index in aligned.index:
        row = aligned.loc[row_index]
        current_values = row.iloc[header_indexes]
        if current_values.map(is_present_value).any():
            continue

        non_empty_indexes = [
            index for index, value in row.items() if is_present_value(value)
        ]
        if not non_empty_indexes or min(non_empty_indexes) <= last_header_index:
            continue

        source_start = min(non_empty_indexes)
        source_values = row.iloc[source_start:source_start + width].tolist()
        if not source_values:
            continue

        for target_index, value in zip(header_indexes, source_values):
            aligned.at[row_index, target_index] = value

    return aligned


def is_present_value(value: Any) -> bool:
    if value is None or pd.isna(value):
        return False
    return str(value).strip() != ""


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = [str(col).strip() for col in normalized.columns]

    if "RUC" in normalized.columns:
        normalized["RUC"] = normalized["RUC"].map(normalize_ruc)

    for column in ["Razón social", "Ciudad", "Provincia", "CIIU actividad principal"]:
        if column in normalized.columns:
            normalized[column] = normalized[column].map(normalize_value)

    if "Año" in normalized.columns:
        normalized["Año"] = normalized["Año"].map(normalize_year)

    for column in [
        "Número",
        "Gerentes",
        "Hombres",
        "Mujeres",
        "Empresas",
        "Q de Tobin (%)",
        "ROA",
        "ROE",
        "Market to Book",
        "Dividend Payout",
        "Deuda financiera / Activo",
        "Cobertura de intereses",
        "CxC relacionadas / Total CxC",
        "Gastos administrativos / Ingresos",
        "CFO / Utilidad neta",
        "Apalancamiento",
        "Endeudamiento del activo",
        "Endeudamiento del patrimonio",
        "Año de constitución",
    ]:
        if column in normalized.columns:
            normalized[column] = normalized[column].apply(normalize_numeric_like_value)

    return normalized


def normalize_numeric_like_value(value: Any):
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if stripped == "":
            return None
        if stripped.lower() in {"nan", "n/a", "na", "null", "none"}:
            return None
        try:
            return float(stripped.replace("%", ""))
        except ValueError:
            return stripped
    return value


def detect_duplicate_rows(df: pd.DataFrame) -> int:
    key_columns = ["RUC", "Año"]
    if not all(col in df.columns for col in key_columns):
        return 0
    return int(df.duplicated(subset=key_columns, keep=False).sum())


def get_missing_summary(df: pd.DataFrame):
    indicator_columns = [
        "Q de Tobin (%)",
        "ROA",
        "ROE",
        "Market to Book",
        "Dividend Payout",
        "Deuda financiera / Activo",
        "Cobertura de intereses",
        "CxC relacionadas / Total CxC",
        "Gastos administrativos / Ingresos",
        "CFO / Utilidad neta",
        "Apalancamiento",
        "Endeudamiento del activo",
        "Endeudamiento del patrimonio",
    ]

    results = []
    for _, row in df.iterrows():
        missing = [col for col in indicator_columns if pd.isna(row.get(col))]
        results.append({
            "RUC": row.get("RUC"),
            "Razón social": row.get("Razón social"),
            "Año": row.get("Año"),
            "missing_fields": missing,
            "is_incomplete": bool(missing),
        })

    complete_records = sum(1 for item in results if not item["is_incomplete"])
    missing_records = sum(1 for item in results if item["is_incomplete"])
    missing_fields_total = sum(len(item["missing_fields"]) for item in results)

    return {
        "records": results,
        "complete_records": complete_records,
        "missing_records": missing_records,
        "missing_fields_total": missing_fields_total,
    }
