"""Controlador para el historial de mediciones."""

from collections.abc import Callable

import toga

from pediatria_neonatal.application.state import AppState
from pediatria_neonatal.views.historial_view import HistorialView


class HistorialController:
    """Coordina la vista del historial de mediciones."""

    def __init__(
        self,
        state: AppState,
        on_select_result: Callable[[int], None] | None = None,
    ) -> None:
        self.state = state
        self.on_select_result = on_select_result
        self.view: HistorialView | None = None

    def build_view(self) -> toga.Widget:
        """Construye la vista del historial."""
        mediciones = self.state.historial_mediciones

        self.view = HistorialView(
            mediciones=mediciones,
            on_select_result=self.on_select_result,
        )

        return self.view.build()
