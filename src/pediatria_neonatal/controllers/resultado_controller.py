"""Controlador para mostrar resultados de evaluación antropométrica."""

from collections.abc import Callable
from typing import Any

import toga

from pediatria_neonatal.application.state import AppState
from pediatria_neonatal.presentation.resultados import build_results_summary
from pediatria_neonatal.views.resultado_view import ResultadoView


class ResultadoController:
    """Coordina la presentación de resultados clínicos."""

    def __init__(
        self,
        state: AppState,
        on_new_measurement: Callable[[], None],
        on_back_to_patient: Callable[[], None],
    ) -> None:
        self.state = state
        self.on_new_measurement = on_new_measurement
        self.on_back_to_patient = on_back_to_patient
        self.view: ResultadoView | None = None

    def build_view(self) -> toga.Widget:
        """Construye la vista de resultados con los datos calculados."""
        paciente = self.state.paciente_actual

        if paciente is None:
            raise ValueError("No hay paciente seleccionado")

        resultados = self.state.resultados_actuales

        if not resultados:
            raise ValueError("No hay resultados calculados")

        paciente_data = self._build_patient_data(paciente)
        summary = build_results_summary(resultados)

        self.view = ResultadoView(
            paciente_nombre=paciente.nombre,
            paciente_data=paciente_data,
            resultados=resultados,
            summary=summary,
            on_new_measurement=self.on_new_measurement,
            on_back_to_patient=self.on_back_to_patient,
        )

        return self.view.build()

    def _build_patient_data(self, paciente: Any) -> dict[str, Any]:
        """Construye diccionario con datos del paciente para la vista."""
        datos = paciente.datos_neonatales
        medicion = self.state.medicion_actual

        patient_data = {
            "sexo": paciente.sexo.value,
            "es_prematuro": paciente.es_prematuro,
            "semanas_eg": datos.edad_gestacional_semanas,
            "peso_nacer_g": datos.peso_nacimiento_kg * 1000,
        }

        # Agregar datos de medición actual si existen
        if medicion:
            patient_data.update(
                {
                    "peso_actual": medicion.peso_kg,
                    "talla_actual": medicion.talla_cm,
                    "perimetro_cefalico_actual": medicion.perimetro_cefalico_cm,
                    "fecha_medicion": medicion.fecha_medicion,
                }
            )

        return patient_data
