from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    file_name: str
    rows_found: int
    columns_detected: int
    columns_expected: int
    complete_records: int
    missing_records: int
    missing_fields_total: int
    duplicate_rows: int
    status: str
    message: str
