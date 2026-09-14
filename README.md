# DATAFILTR

Aplicación local para gestionar información de empresas a partir de archivos Excel, con validación, detección de registros faltantes, actualización y exportación de resultados.

## Estructura inicial

- backend/: lógica del servidor FastAPI
- frontend/: interfaz web HTML + CSS + JavaScript
- docs/: documentación y reglas del negocio

## Requisitos

- Python 3.11+
- pip

## Instalación

```bash
cd S:\Practicas Profesionales\Primer programa\DATAFILTR
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecutar la aplicación

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Luego abrir en el navegador:

http://localhost:8001

## Despliegue en Vercel

Configura el proyecto conectado a la rama `main` con estos valores:

```text
Root Directory: vacío
Build Command: pip install -r requirements.txt
Start Command: automático
```

El entrypoint de FastAPI está declarado en `pyproject.toml` como `backend.app.main:app`.

## Estado actual

La aplicación actualmente permite:
- cargar y validar Excel con encabezados y columnas desplazadas;
- reemplazar la carga anterior sin duplicar registros al recargar el mismo archivo;
- mostrar automáticamente los datos en la tabla principal;
- navegar entre la tabla principal y la vista de registros faltantes en la misma pestaña;
- actualizar datos mediante un archivo adicional;
- exportar faltantes y descargar la base actualizada.

La información cargada se mantiene en memoria mientras el servidor está activo. Al reiniciar el servidor se limpia la carga anterior.

Desde **Configuración** se puede consultar el archivo activo y el historial de documentos cargados durante la sesión. La opción **Limpiar datos de sesión** elimina la carga y el historial de DATAFILTR, pero no borra los archivos Excel originales del equipo.
