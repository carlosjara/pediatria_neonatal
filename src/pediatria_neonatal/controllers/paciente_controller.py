from collections.abc import Callable
from typing import Any

import toga

from pediatria_neonatal.application.state import AppState
from pediatria_neonatal.domain.paciente import DatosNeonatales, Paciente
from pediatria_neonatal.views.paciente_view import PacienteView


class PacienteController:
    """Coordina la vista y el dominio del paciente."""

    def __init__(
        self,
        state: AppState,
        on_patient_saved: Callable[[], None],
        on_calcular_edad: Callable[[], None] | None = None,
    ) -> None:
        self.state = state
        self.on_patient_saved = on_patient_saved
        self.on_calcular_edad = on_calcular_edad
        self.view: PacienteView | None = None

    def build_view(self) -> toga.Widget:
        self.view = PacienteView(
            on_save=self.save,
            on_calcular_edad=self.on_calcular_edad,
        )
        return self.view.build()

    def save(self, raw_data: dict[str, Any]) -> None:
        assert self.view is not None

        try:
            nombre = str(raw_data["nombre"] or "").strip()
            semanas_str = str(raw_data["semanas"] or "").strip()
            dias_str = str(raw_data["dias"] or "").strip()
            peso_nacer_str = str(raw_data["peso_nacer"] or "").strip()

            if not nombre:
                raise ValueError("Ingresa el nombre del paciente.")

            if not semanas_str:
                raise ValueError("Ingresa las semanas gestacionales.")

            semanas = int(semanas_str)

            dias = int(dias_str) if dias_str else 0

            if not peso_nacer_str:
                raise ValueError("Ingresa el peso al nacer.")

            peso_nacer_gramos = float(peso_nacer_str)
            peso_nacer_kg = peso_nacer_gramos / 1000.0

            datos_neonatales = DatosNeonatales(
                edad_gestacional_semanas=semanas,
                edad_gestacional_dias=dias,
                peso_nacimiento_kg=peso_nacer_kg,
            )

            paciente = Paciente(
                nombre=nombre,
                fecha_nacimiento=raw_data["fecha_nacimiento"],
                sexo=raw_data["sexo"],
                datos_neonatales=datos_neonatales,
            )

        except (TypeError, ValueError) as error:
            self.view.show_error(str(error))
            return

        self.state.paciente_actual = paciente
        self.on_patient_saved()
