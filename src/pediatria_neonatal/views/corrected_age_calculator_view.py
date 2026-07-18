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
        self.semanas_value = 32
        self.dias_value = 0
        self.semanas_label = toga.Label(
            str(self.semanas_value),
            style=Pack(font_size=18, font_weight="bold", text_align=CENTER, flex=1),
        )
        self.dias_label = toga.Label(
            str(self.dias_value),
            style=Pack(font_size=18, font_weight="bold", text_align=CENTER, flex=1),
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
                        self._field_group(
                            "Semanas",
                            self._stepper(
                                self.decrement_weeks,
                                self.semanas_label,
                                self.increment_weeks,
                            ),
                        ),
                        toga.Box(style=Pack(width=SPACING_SM)),
                        self._field_group(
                            "Días",
                            self._stepper(
                                self.decrement_days,
                                self.dias_label,
                                self.increment_days,
                            ),
                        ),
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
                toga.Box(style=Pack(height=220)),
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

    def _stepper(
        self,
        on_decrement: Callable[[toga.Widget], None],
        value_label: toga.Label,
        on_increment: Callable[[toga.Widget], None],
    ) -> toga.Box:
        """Control inline para evitar teclado y picker nativo."""

        return toga.Box(
            children=[
                toga.Button(
                    "-",
                    on_press=on_decrement,
                    style=Pack(width=44, padding_right=SPACING_SM),
                ),
                value_label,
                toga.Button(
                    "+",
                    on_press=on_increment,
                    style=Pack(width=44, padding_left=SPACING_SM),
                ),
            ],
            style=Pack(direction=ROW),
        )

    def calculate(self, widget: toga.Widget) -> None:
        """Solicita cálculo al controlador."""

        self.on_calculate(
            {
                "fecha_nacimiento": self.fecha_nacimiento_input.value,
                "eg_semanas": str(self.semanas_value),
                "eg_dias": str(self.dias_value),
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
        self.semanas_value = 32
        self.dias_value = 0
        self._refresh_stepper_labels()
        self.result_box.clear()

    def decrement_weeks(self, widget: toga.Widget) -> None:
        """Disminuye semanas gestacionales."""

        self.semanas_value = max(22, self.semanas_value - 1)
        self._refresh_stepper_labels()

    def increment_weeks(self, widget: toga.Widget) -> None:
        """Aumenta semanas gestacionales."""

        self.semanas_value = min(42, self.semanas_value + 1)
        self._refresh_stepper_labels()

    def decrement_days(self, widget: toga.Widget) -> None:
        """Disminuye días gestacionales."""

        self.dias_value = max(0, self.dias_value - 1)
        self._refresh_stepper_labels()

    def increment_days(self, widget: toga.Widget) -> None:
        """Aumenta días gestacionales."""

        self.dias_value = min(6, self.dias_value + 1)
        self._refresh_stepper_labels()

    def _refresh_stepper_labels(self) -> None:
        """Actualiza valores visibles de semanas y días."""

        self.semanas_label.text = str(self.semanas_value)
        self.dias_label.text = str(self.dias_value)

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
