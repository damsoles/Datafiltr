from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.data import router as data_router
from app.api.health import router as health_router

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="DATAFILTR",
    description="Gestión local de empresas y análisis de datos faltantes en Excel",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(data_router)

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "templates" / "index.html")
