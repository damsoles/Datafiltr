from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CompanyRecord:
    """Representa un registro de empresa por año."""

    ruc: str | None = None
    razon_social: str | None = None
    ano: str | int | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)
    missing_fields: list[str] = field(default_factory=list)
    is_complete: bool = True
