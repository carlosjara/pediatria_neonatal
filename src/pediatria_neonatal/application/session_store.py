"""Almacenamiento temporal de sesión para pacientes evaluados."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import gettempdir
from typing import Any


class SessionStore:
    """Persiste datos temporales mientras la aplicación está abierta."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path(gettempdir()) / "pediatria_neonatal_session.json"

    def reset(self) -> None:
        """Recrea el archivo temporal al iniciar una sesión de app."""

        self.path.write_text("[]", encoding="utf-8")

    def load(self) -> list[dict[str, Any]]:
        """Carga registros temporales, tolerando archivo inexistente o inválido."""

        if not self.path.exists():
            return []

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

        if not isinstance(data, list):
            return []
        return [item for item in data if isinstance(item, dict)]

    def save(self, records: list[dict[str, Any]]) -> None:
        """Guarda los registros temporales de sesión."""

        self.path.write_text(
            json.dumps(records, ensure_ascii=False, default=str, indent=2),
            encoding="utf-8",
        )
