import pandas as pd
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

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


def build_sample_frame():
    row_a = {column: value for column, value in zip(EXPECTED_COLUMNS, [
        1, "099001", "Empresa A", 2018, "Quito", "Pichincha", "A", 3, 2, 1, 1, 2023,
        1.2, None, None, 1.32, 0.5, 0.4, 2.0, 0.3, 0.5, 1.1, 1.4, 0.6, 0.7
    ])}
    row_b = {column: value for column, value in zip(EXPECTED_COLUMNS, [
        2, "099002", "Empresa B", 2017, "Guayaquil", "Guayas", "B", 4, 3, 1, 1, 2024,
        1.5, 5.4, 8.2, 1.45, 0.6, 0.5, 2.4, 0.4, 0.6, 1.2, 1.5, 0.7, 0.8
    ])}
    return pd.DataFrame([row_a, row_b])


def test_health_route():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_columns_route():
    response = client.get("/api/columns")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 25
    assert "RUC" in payload["columns"]
    assert "Año" in payload["columns"]


def test_upload_and_missing_detection(tmp_path):
    sample_file = tmp_path / "BASE_EMPRESAS.xlsx"
    build_sample_frame().to_excel(sample_file, index=False)

    with sample_file.open("rb") as file:
        response = client.post(
            "/api/upload",
            files={"file": (sample_file.name, file.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["rows_found"] == 2
    assert payload["missing_records"] == 1
    assert payload["missing_fields_total"] == 2

    missing_response = client.get("/api/missing")
    assert missing_response.status_code == 200
    missing_data = missing_response.json()
    assert len(missing_data) == 1
    assert missing_data[0]["ruc"] == "099001"
    assert missing_data[0]["cantidad"] == 2
    assert "ROA" in missing_data[0]["campos_faltantes"]
    assert "ROE" in missing_data[0]["campos_faltantes"]


def test_upload_accepts_header_row_below_blank_first_row(tmp_path):
    sample_df = build_sample_frame()
    blank_row = pd.DataFrame([[''] * len(sample_df.columns)], columns=sample_df.columns)
    header_row = pd.DataFrame([sample_df.columns.tolist()], columns=sample_df.columns)
    combined = pd.concat([blank_row, header_row, sample_df], ignore_index=True)

    sample_file = tmp_path / "BASE_EMPRESAS_HEADER_OFFSET.xlsx"
    combined.to_excel(sample_file, index=False, header=False)

    with sample_file.open("rb") as file:
        response = client.post(
            "/api/upload",
            files={"file": (sample_file.name, file.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["rows_found"] == 2
    assert payload["missing_records"] == 1


def test_upload_maps_equivalent_headers_without_shifting_values(tmp_path):
    sample_df = build_sample_frame().rename(columns={
        "Número": "Numero",
        "Razón social": "Razon social",
        "Año de constitución": "Ano de constitucion",
        "Año": "Ano",
    })
    sample_file = tmp_path / "BASE_EMPRESAS_EQUIVALENT_HEADERS.xlsx"
    sample_df.to_excel(sample_file, index=False)

    with sample_file.open("rb") as file:
        response = client.post(
            "/api/upload",
            files={"file": (sample_file.name, file.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )

    assert response.status_code == 200, response.text
    data_response = client.get("/api/data")
    assert data_response.status_code == 200
    first_row = data_response.json()[0]
    assert first_row["Número"] == 1
    assert first_row["RUC"] == "099001"
    assert first_row["Razón social"] == "Empresa A"
    assert first_row["Año"] == 2023


def test_upload_aligns_rows_shifted_after_empty_columns(tmp_path):
    sample_df = build_sample_frame()
    blank_prefix = pd.DataFrame([[None] * len(EXPECTED_COLUMNS)] * len(sample_df))
    shifted_rows = pd.concat([blank_prefix, sample_df], axis=1)
    header = EXPECTED_COLUMNS + [None] * len(EXPECTED_COLUMNS)
    raw_df = pd.concat([
        pd.DataFrame([[None] * len(header)]),
        pd.DataFrame([header]),
        shifted_rows,
    ], ignore_index=True)
    sample_file = tmp_path / "BASE_EMPRESAS_SHIFTED_ROWS.xlsx"
    raw_df.to_excel(sample_file, index=False, header=False)

    with sample_file.open("rb") as file:
        response = client.post(
            "/api/upload",
            files={"file": (sample_file.name, file.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )

    assert response.status_code == 200, response.text
    first_row = client.get("/api/data").json()[0]
    assert first_row["Número"] == 1
    assert first_row["RUC"] == "099001"
    assert first_row["Razón social"] == "Empresa A"


def test_upload_accepts_real_header_variants(tmp_path):
    sample_df = build_sample_frame().rename(columns={
        "CIIU actividad principal": "CIIU actividad principal:",
        "Hombres": "Hombre",
        "Market to Book": "Market-to-book",
        "Cobertura de intereses": "Cobertura intereses",
        "Gastos administrativos / Ingresos": "Gastos adm. / ingresos",
    })
    sample_file = tmp_path / "EMPRESAS_ECONOMIA.xlsx"
    sample_df.to_excel(sample_file, index=False)

    with sample_file.open("rb") as file:
        response = client.post(
            "/api/upload",
            files={"file": (sample_file.name, file.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )

    assert response.status_code == 200, response.text
    first_row = client.get("/api/data").json()[0]
    assert first_row["CIIU actividad principal"] == "A"
    assert first_row["Hombres"] == 2
    assert first_row["Market to Book"] == 1.32


def test_failed_upload_clears_previous_data(tmp_path):
    valid_file = tmp_path / "BASE_EMPRESAS.xlsx"
    build_sample_frame().to_excel(valid_file, index=False)
    with valid_file.open("rb") as file:
        valid_response = client.post(
            "/api/upload",
            files={"file": (valid_file.name, file.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
    assert valid_response.status_code == 200

    invalid_file = tmp_path / "EMPRESAS_INVALIDA.xlsx"
    pd.DataFrame([["dato"]]).to_excel(invalid_file, index=False)
    with invalid_file.open("rb") as file:
        invalid_response = client.post(
            "/api/upload",
            files={"file": (invalid_file.name, file.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )

    assert invalid_response.status_code == 400
    assert client.get("/api/data").status_code == 404


def test_reuploading_same_file_replaces_instead_of_duplicating(tmp_path):
    sample_file = tmp_path / "BASE_EMPRESAS_RELOAD.xlsx"
    build_sample_frame().to_excel(sample_file, index=False)
    file_payload = sample_file.read_bytes()

    for _ in range(2):
        response = client.post(
            "/api/upload",
            files={"file": (sample_file.name, file_payload, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert response.status_code == 200, response.text

    data_response = client.get("/api/data")
    assert data_response.status_code == 200
    assert len(data_response.json()) == 2


def test_session_info_and_clear_remove_active_data_and_history(tmp_path):
    client.delete("/api/session")
    sample_file = tmp_path / "BASE_EMPRESAS_SESSION.xlsx"
    build_sample_frame().to_excel(sample_file, index=False)

    with sample_file.open("rb") as file:
        response = client.post(
            "/api/upload",
            files={"file": (sample_file.name, file.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
    assert response.status_code == 200

    session_response = client.get("/api/session")
    assert session_response.status_code == 200
    session = session_response.json()
    assert session["has_data"] is True
    assert session["active_file"]["file_name"] == sample_file.name
    assert len(session["file_history"]) == 1

    clear_response = client.delete("/api/session")
    assert clear_response.status_code == 200
    assert client.get("/api/data").status_code == 404
    assert client.get("/api/session").json() == {
        "active_file": None,
        "file_history": [],
        "has_data": False,
    }
