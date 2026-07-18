"""Vista independiente para calcular edad corregida de prematuros."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any

import toga
from toga.style import Pack
from toga.style.pack import CENTER, COLUMN, ROW

from pediatria_neonatal.views.components import (
    SPACING_LG,
    SPACING_MD,
    SPACING_SM,
    field_label,
    primary_button,
    scroll_screen,
    secondary_button,
    subtitle,
    title,
    wrapped_text,
)

NOTE_TEXT = (
    "Esta vista es solo calculadora y no guarda lo generado. Solo recibe lo "
    "mínimo para calcular la edad corregida respecto a hoy y lo calcula aquí mismo."
)


class CorrectedAgeCalculatorView:
    """Calculadora efímera de edad corregida para prematuros."""

    def __init__(
        self,
        on_calculate: Callable[[dict[str, Any]], None],
        on_clear: Callable[[], None],
        on_back_home: Callable[[], None],
    ) -> None:
        self.on_calculate = on_calculate
        self.on_clear = on_clear
        self.on_back_home = on_back_home
        self.fecha_nacimiento_input = toga.DateInput(
            value=date.today(),
            max=date.today(),
            style=Pack(flex=1),
        )
        self.semanas_input = toga.Selection(
            items=[str(value) for value in range(22, 43)],
            value="32",
            style=Pack(flex=1),
        )
        self.dias_input = toga.Selection(
            items=[str(value) for value in range(0, 7)],
            value="0",
            style=Pack(flex=1),
        )
        self.result_box = toga.Box(style=Pack(direction=COLUMN))

    def build(self) -> toga.Widget:
        """Construye la vista completa."""

        content = toga.Box(
            children=[
                title("Edad corregida"),
                wrapped_text(NOTE_TEXT, height=96),
                subtitle("Datos mínimos"),
                field_label("Fecha de nacimiento"),
                self.fecha_nacimiento_input,
                field_label("Edad gestacional al nacer"),
                toga.Box(
                    children=[
                        self._field_group("Semanas", self.semanas_input),
                        toga.Box(style=Pack(width=SPACING_SM)),
                        self._field_group("Días", self.dias_input),
                    ],
                    style=Pack(direction=ROW),
                ),
                toga.Label(
                    f"Fecha de cálculo: {date.today().strftime('%d/%m/%Y')}",
                    style=Pack(
                        font_size=12,
                        color="#6B7280",
                        text_align=CENTER,
                        padding_top=SPACING_MD,
                    ),
                ),
                primary_button("Calcular", self.calculate),
                self.result_box,
                toga.Box(
                    children=[
                        secondary_button("Limpiar", self.clear_pressed),
                        toga.Box(style=Pack(width=SPACING_SM)),
                        secondary_button("Volver a Home", self.back_home),
                    ],
                    style=Pack(direction=ROW, padding_top=SPACING_LG),
                ),
            ],
            style=Pack(direction=COLUMN, padding=SPACING_MD),
        )
        return scroll_screen(content)

    def _field_group(self, label: str, widget: toga.Widget) -> toga.Box:
        """Agrupa etiqueta compacta y campo."""

        return toga.Box(
            children=[
                toga.Label(
                    label,
                    style=Pack(
                        font_size=12,
                        color="#6B7280",
                        padding_bottom=SPACING_SM,
                    ),
                ),
                widget,
            ],
            style=Pack(direction=COLUMN, flex=1),
        )

    def calculate(self, widget: toga.Widget) -> None:
        """Solicita cálculo al controlador."""

        self.on_calculate(
            {
                "fecha_nacimiento": self.fecha_nacimiento_input.value,
                "eg_semanas": self.semanas_input.value,
                "eg_dias": self.dias_input.value,
            }
        )

    def clear_pressed(self, widget: toga.Widget) -> None:
        """Botón limpiar."""

        self.on_clear()

    def back_home(self, widget: toga.Widget) -> None:
        """Regresa a Home sin persistir información."""

        self.on_back_home()

    def clear(self) -> None:
        """Limpia formulario y resultado visible."""

        self.fecha_nacimiento_input.value = date.today()
        self.semanas_input.value = "32"
        self.dias_input.value = "0"
        self.result_box.clear()

    def show_result(self, result: dict[str, Any]) -> None:
        """Muestra resultado del cálculo local."""

        self.result_box.clear()
        self.result_box.add(
            toga.Box(
                children=[
                    subtitle("Resultado"),
                    self._result_row(
                        "Edad cronológica",
                        str(result.get("edad_cronologica", "")),
                    ),
                    self._result_row(
                        "Edad corregida",
                        str(result.get("edad_corregida", "")),
                    ),
                    self._result_row(
                        "Prematuridad",
                        f"{result.get('prematuridad_dias', 0)} días",
                    ),
                    self._status_text(result),
                ],
                style=Pack(direction=COLUMN, padding_top=SPACING_MD),
            )
        )

    def show_error(self, message: str) -> None:
        """Muestra error de validación o cálculo."""

        self.result_box.clear()
        self.result_box.add(
            toga.Label(
                f"Error: {message}",
                style=Pack(
                    font_size=14,
                    color="#DC2626",
                    padding_top=SPACING_MD,
                ),
            )
        )

    def _result_row(self, label: str, value: str) -> toga.Box:
        """Fila de resultado."""

        return toga.Box(
            children=[
                toga.Label(
                    label,
                    style=Pack(font_size=13, color="#6B7280", flex=1),
                ),
                toga.Label(
                    value,
                    style=Pack(font_size=16, font_weight="bold", text_align=CENTER),
                ),
            ],
            style=Pack(
                direction=ROW,
                padding_top=SPACING_SM,
                padding_bottom=SPACING_SM,
            ),
        )

    def _status_text(self, result: dict[str, Any]) -> toga.Label:
        """Texto complementario según edad corregida."""

        if result.get("es_antes_de_termino"):
            text = "Aún no alcanza la edad corregida de término."
            color = "#D97706"
        else:
            text = "Cálculo realizado respecto a la fecha de hoy."
            color = "#16A34A"

        return toga.Label(
            text,
            style=Pack(
                font_size=13,
                color=color,
                padding_top=SPACING_SM,
            ),
        )
