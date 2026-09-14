from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pathlib import Path
from datetime import datetime

import pandas as pd

from app.core.exceptions import DataValidationError
from app.services.excel_service import EXPECTED_COLUMNS, read_excel_file, get_missing_summary
from app.services.missing_service import build_missing_grouped_view, build_missing_report_dataframe
from app.services.update_service import apply_excel_update

router = APIRouter(prefix="/api", tags=["data"])

DATASTORE = {
    "main_df": None,
    "missing_records": [],
    "report_path": None,
    "active_file": None,
    "file_history": [],
}


def reset_datastore():
    DATASTORE["main_df"] = None
    DATASTORE["missing_records"] = []
    DATASTORE["report_path"] = None
    DATASTORE["active_file"] = None


def clear_session_data():
    reset_datastore()
    DATASTORE["file_history"] = []


def sanitize_for_json(value):
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, list):
        return [sanitize_for_json(item) for item in value]
    if isinstance(value, dict):
        return {key: sanitize_for_json(val) for key, val in value.items()}
    return value


@router.get("/columns")
def get_expected_columns():
    return {"columns": EXPECTED_COLUMNS, "count": len(EXPECTED_COLUMNS)}


@router.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls).")

    temp_path = Path("/tmp") / file.filename
    temp_path.parent.mkdir(parents=True, exist_ok=True)

    content = await file.read()
    temp_path.write_bytes(content)
    reset_datastore()

    try:
        df, duplicate_rows = read_excel_file(temp_path)
    except DataValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    summary = get_missing_summary(df)
    DATASTORE["main_df"] = df
    DATASTORE["missing_records"] = build_missing_grouped_view(df)
    file_info = {
        "file_name": file.filename,
        "rows": len(df),
        "columns": len(df.columns),
        "loaded_at": datetime.now().isoformat(timespec="seconds"),
    }
    DATASTORE["active_file"] = file_info
    DATASTORE["file_history"].append(file_info)

    return {
        "file_name": file.filename,
        "rows_found": len(df),
        "columns_detected": len(df.columns),
        "columns_expected": len(EXPECTED_COLUMNS),
        "complete_records": summary["complete_records"],
        "missing_records": summary["missing_records"],
        "missing_fields_total": summary["missing_fields_total"],
        "duplicate_rows": duplicate_rows,
        "duplicate_warning": (
            f"Se detectaron {duplicate_rows} filas duplicadas por RUC y Año."
            if duplicate_rows
            else None
        ),
        "status": "ok",
        "message": "Excel cargado y validado correctamente.",
    }


@router.get("/session")
def get_session_info():
    return {
        "active_file": DATASTORE["active_file"],
        "file_history": DATASTORE["file_history"],
        "has_data": DATASTORE["main_df"] is not None,
    }


@router.delete("/session")
def delete_session_data():
    clear_session_data()
    return {
        "status": "ok",
        "message": "La carga activa y el historial de sesión fueron eliminados.",
    }


@router.get("/data")
def get_main_data():
    if DATASTORE["main_df"] is None:
        raise HTTPException(status_code=404, detail="No hay un Excel cargado.")
    records = DATASTORE["main_df"].to_dict(orient="records")
    sanitized = [{key: sanitize_for_json(value) for key, value in row.items()} for row in records]
    return sanitized


@router.get("/missing")
def get_missing_records():
    if DATASTORE["main_df"] is None:
        raise HTTPException(status_code=404, detail="No hay un Excel cargado.")
    return [sanitize_for_json(record) for record in DATASTORE["missing_records"]]


@router.post("/detect-missing")
def detect_missing():
    if DATASTORE["main_df"] is None:
        raise HTTPException(status_code=404, detail="No hay un Excel cargado.")
    DATASTORE["missing_records"] = build_missing_grouped_view(DATASTORE["main_df"])
    return {"status": "ok", "missing_records": len(DATASTORE["missing_records"])}


@router.get("/missing-report")
def download_missing_report():
    if DATASTORE["main_df"] is None:
        raise HTTPException(status_code=404, detail="No hay un Excel cargado.")

    report_df = build_missing_report_dataframe(DATASTORE["main_df"])
    output_path = Path("/tmp") / "REPORTE_FALTANTES.xlsx"
    report_df.to_excel(output_path, index=False)
    DATASTORE["report_path"] = str(output_path)
    return FileResponse(path=str(output_path), filename="REPORTE_FALTANTES.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.post("/update")
async def update_data(file: UploadFile = File(...)):
    if DATASTORE["main_df"] is None:
        raise HTTPException(status_code=404, detail="No hay un Excel principal cargado.")

    temp_path = Path("/tmp") / f"update_{file.filename}"
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path.write_bytes(await file.read())

    try:
        update_df = __import__("pandas").read_excel(temp_path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"El archivo de actualización no es válido: {exc}") from exc

    try:
        merged_df = apply_excel_update(DATASTORE["main_df"], update_df)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    DATASTORE["main_df"] = merged_df
    DATASTORE["missing_records"] = build_missing_grouped_view(merged_df)

    return {
        "status": "ok",
        "message": "Datos actualizados correctamente.",
        "rows_after_update": len(merged_df),
    }


@router.get("/download-updated")
def download_updated_data():
    if DATASTORE["main_df"] is None:
        raise HTTPException(status_code=404, detail="No hay datos para descargar.")

    output_path = Path("/tmp") / "BASE_EMPRESAS_ACTUALIZADA.xlsx"
    DATASTORE["main_df"].to_excel(output_path, index=False)
    return FileResponse(path=str(output_path), filename="BASE_EMPRESAS_ACTUALIZADA.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
