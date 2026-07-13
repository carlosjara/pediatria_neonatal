"""Controlador para calcular edad corregida rápidamente."""

from collections.abc import Callable
from datetime import date
from typing import Any

import toga

from pediatria_neonatal.application.state import AppState
from pediatria_neonatal.views.edad_corregida_view import EdadCorregidaView


class EdadCorregidaController:
    """Coordina el cálculo rápido de edad corregida."""

    def __init__(
        self,
        state: AppState,
        on_back: Callable[[], None],
    ) -> None:
        self.state = state
        self.on_back = on_back
        self.view: EdadCorregidaView | None = None

    def build_view(self) -> toga.Widget:
        """Construye la vista de cálculo de edad corregida."""
        paciente = self.state.paciente_actual

        if paciente is None:
            raise ValueError("No hay paciente seleccionado")

        paciente_data = self._build_patient_data(paciente)

        self.view = EdadCorregidaView(
            paciente_data=paciente_data,
            on_calculate=self._calculate_edad_corregida,
            on_back=self.on_back,
        )

        return self.view.build()

    def _build_patient_data(self, paciente: Any) -> dict[str, Any]:
        """Construye diccionario con datos del paciente."""
        datos = paciente.datos_neonatales
        return {
            "nombre": paciente.nombre,
            "fecha_nacimiento": datos.fecha_nacimiento.strftime("%d/%m/%Y"),
            "semanas_eg": datos.edad_gestacional_semanas,
            "dias_eg": datos.edad_gestacional_dias,
            "es_prematuro": paciente.es_prematuro,
        }

    def _calculate_edad_corregida(self, data: dict) -> None:
        """Calcula la edad corregida para la fecha dada."""
        try:
            paciente = self.state.paciente_actual
            if paciente is None:
                raise ValueError("No hay paciente seleccionado")

            fecha_medicion = data["fecha_medicion"]

            # Calcular edad corregida usando el servicio existente
            edad_corregida = self.state.services.neonatal.calcular_edad_corregida_paciente(
                paciente=paciente,
                fecha_medicion=fecha_medicion,
            )

            # Formatear edades con el método existente
            from pediatria_neonatal.controllers.medicion_controller import MedicionController
            med_controller = MedicionController(
                state=self.state,
                view=None,
                on_results_ready=lambda: None,
            )

            edad_cronologica_texto = med_controller._format_age_from_days(
                edad_corregida.edad_cronologica_dias
            )
            
            edad_corregida_texto = med_controller._format_age_from_days(
                edad_corregida.edad_corregida_total_dias
            )

            resultado = {
                "edad_cronologica_texto": edad_cronologica_texto,
                "edad_corregida_texto": edad_corregida_texto,
                "es_prematuro": paciente.es_prematuro,
                "edad_cronologica_dias": edad_corregida.edad_cronologica_dias,
                "edad_corregida_total_dias": edad_corregida.edad_corregida_total_dias,
            }

            if self.view:
                self.view.show_result(resultado)

        except Exception as error:
            if self.view:
                self.view.show_error(str(error))
