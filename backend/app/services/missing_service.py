from __future__ import annotations

import pandas as pd


def build_missing_grouped_view(df):
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

    records = []
    for _, row in df.iterrows():
        missing = [col for col in indicator_columns if pd.isna(row.get(col))]
        if missing:
            records.append({
                "empresa": row.get("Razón social"),
                "ruc": row.get("RUC"),
                "año": row.get("Año"),
                "campos_faltantes": missing,
                "cantidad": len(missing),
                "fila": row.to_dict(),
            })

    return records


def build_missing_report_dataframe(df):
    missing_rows = []
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

    for _, row in df.iterrows():
        missing = [col for col in indicator_columns if pd.isna(row.get(col))]
        if missing:
            row_copy = row.copy()
            for col in indicator_columns:
                if col in missing:
                    row_copy[col] = None
            missing_rows.append(row_copy)

    if not missing_rows:
        return df.iloc[0:0].copy()

    return pd.DataFrame(missing_rows)
