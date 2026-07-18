"""Módulo para cargar y gestionar iconos de la aplicación."""

from pathlib import Path

import toga

ICONS_DIR = Path(__file__).parent / "icons"


def _icon_path(name: str) -> Path | None:
    """Devuelve la ruta de un icono por nombre, si existe."""
    icon_path = ICONS_DIR / f"{name}.png"
    if icon_path.exists():
        return icon_path
    return None


def _load_icon(name: str) -> toga.Icon | None:
    """Carga un icono por nombre, retorna None si no existe."""
    icon_path = _icon_path(name)
    if icon_path:
        return toga.Icon(str(icon_path))
    return None


class AppIcons:
    """Iconos de la aplicación cargados una sola vez."""

    _instance: "AppIcons | None" = None

    def __init__(self) -> None:
        self.home = _load_icon("home")
        self.baby = _load_icon("baby")
        self.history = _load_icon("history")
        self.settings = _load_icon("settings")
        self.scale = _load_icon("scale")
        self.ruler = _load_icon("ruler")
        self.head = _load_icon("head")
        self.chart = _load_icon("chart")
        self.check = _load_icon("check")
        self.warning = _load_icon("warning")
        self.baby_bee_path = _icon_path("baby_bee")

    @classmethod
    def get(cls) -> "AppIcons":
        """Obtiene la instancia singleton de iconos."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


def get_icons() -> AppIcons:
    """Función de conveniencia para obtener los iconos."""
    return AppIcons.get()
