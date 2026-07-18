"""Controlador para calculadora independiente de edad corregida."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any

import toga

from pediatria_neonatal.services.neonatal import CalculadoraNeonatal
from pediatria_neonatal.views.corrected_age_calculator_view import (
    CorrectedAgeCalculatorView,
)


class CorrectedAgeCalculatorController:
    """Coordina cálculo efímero de edad corregida sin estado de paciente."""

    def __init__(
        self,
        neonatal: CalculadoraNeonatal,
        on_back_home: Callable[[], None],
    ) -> None:
        self.neonatal = neonatal
        self.on_back_home = on_back_home
        self.view: CorrectedAgeCalculatorView | None = None

    def build_view(self) -> toga.Widget:
        """Construye la calculadora independiente."""

        self.view = CorrectedAgeCalculatorView(
            on_calculate=self._calculate,
            on_clear=self._clear,
            on_back_home=self.on_back_home,
        )
        return self.view.build()

    def _calculate(self, data: dict[str, Any]) -> None:
        """Calcula edad corregida respecto a hoy sin persistir datos."""

        try:
            fecha_nacimiento = data["fecha_nacimiento"]
            semanas = self._parse_int(data.get("eg_semanas"), "semanas")
            dias = self._parse_int(data.get("eg_dias"), "días")

            result = self.neonatal.calcular_edad_corregida(
                fecha_nacimiento=fecha_nacimiento,
                fecha_medicion=date.today(),
                eg_semanas=semanas,
                eg_dias=dias,
            )

            payload = {
                "fecha_calculo": date.today().strftime("%d/%m/%Y"),
                "edad_cronologica": _format_age_from_days(
                    result.edad_cronologica_dias
                ),
                "edad_corregida": _format_age_from_days(
                    result.edad_corregida_total_dias
                ),
                "prematuridad_dias": result.prematuridad_dias,
                "es_antes_de_termino": result.es_antes_de_termino,
            }

            if self.view is not None:
                self.view.show_result(payload)

        except Exception as error:
            if self.view is not None:
                self.view.show_error(str(error))

    def _clear(self) -> None:
        """Limpia el formulario sin tocar estado global."""

        if self.view is not None:
            self.view.clear()

    @staticmethod
    def _parse_int(value: object, field_name: str) -> int:
        """Convierte un campo de texto a entero clínico."""

        text = str(value or "").strip()
        if not text:
            raise ValueError(f"Ingrese {field_name} de edad gestacional.")
        return int(text)


def _format_age_from_days(total_days: int) -> str:
    """Formatea días a una representación compacta usada por la app."""

    if total_days < 0:
        return "Antes de término"

    if total_days < 30:
        return f"{total_days}D"

    months = total_days // 30
    days = total_days % 30
    weeks = total_days // 7
    remaining_days = total_days % 7

    if months < 12:
        if days > 0:
            return f"{months}M, {days}D ({weeks}S, {remaining_days}D)"
        return f"{months}M ({weeks}S)"

    years = months // 12
    remaining_months = months % 12
    if remaining_months > 0:
        return f"{years}a, {remaining_months}M"
    return f"{years}a"
