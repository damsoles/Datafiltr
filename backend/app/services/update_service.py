from __future__ import annotations

import pandas as pd

from app.core.exceptions import UpdateDataError


def apply_excel_update(main_df: pd.DataFrame, update_df: pd.DataFrame):
    if "RUC" not in main_df.columns or "Año" not in main_df.columns:
        raise UpdateDataError("La tabla principal no contiene las columnas RUC y Año.")
    if "RUC" not in update_df.columns or "Año" not in update_df.columns:
        raise UpdateDataError("El archivo de actualización no contiene las columnas RUC y Año.")

    main_index = main_df.set_index(["RUC", "Año"]).sort_index()
    update_index = update_df.set_index(["RUC", "Año"]).sort_index()

    result = main_index.combine_first(update_index)

    if result.empty:
        raise UpdateDataError("No se encontraron registros válidos para actualizar.")

    return result.reset_index()
