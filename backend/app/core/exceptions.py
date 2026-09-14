class DataValidationError(ValueError):
    """Error de validación del archivo Excel."""


class MissingDataError(ValueError):
    """Error al detectar faltantes."""


class UpdateDataError(ValueError):
    """Error al aplicar actualización de datos."""
