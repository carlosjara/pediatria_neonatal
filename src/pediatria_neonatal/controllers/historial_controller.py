"""Controlador para el historial de mediciones."""

import toga

from pediatria_neonatal.application.state import AppState
from pediatria_neonatal.views.historial_view import HistorialView


class HistorialController:
    """Coordina la vista del historial de mediciones."""

    def __init__(self, state: AppState) -> None:
        self.state = state
        self.view: HistorialView | None = None

    def build_view(self) -> toga.Widget:
        """Construye la vista del historial."""
        mediciones = self.state.historial_mediciones

        self.view = HistorialView(
            mediciones=mediciones,
            on_select=self._on_select_medicion,
        )

        return self.view.build()

    def _on_select_medicion(self, medicion: dict) -> None:
        """Maneja la selección de una medición del historial."""
        pass
