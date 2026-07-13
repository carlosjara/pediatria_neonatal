"""Vista para registrar mediciones antropométricas."""

from collections.abc import Callable
from datetime import date

import toga
from toga.style import Pack
from toga.style.pack import COLUMN

from pediatria_neonatal.views.components import (
    SPACING_MD,
    SPACING_SM,
    caption_text,
    field_label,
    info_row,
    primary_button,
    scroll_screen,
    subtitle,
    title,
)


class MedicionView:
    """Formulario para registrar peso, talla y perímetro cefálico."""

    def __init__(
        self,
        paciente_nombre: str,
        paciente_info: str,
        on_calculate: Callable[[dict], None],
        on_back: Callable[[], None],
    ) -> None:
        self.paciente_nombre = paciente_nombre
        self.paciente_info = paciente_info
        self.on_calculate = on_calculate
        self.on_back = on_back

        self.fecha_input = toga.DateInput(
            value=date.today(),
            max=date.today(),
            style=Pack(flex=1),
        )

        self.peso_input = toga.TextInput(
            placeholder="Ej: 8.5",
            style=Pack(flex=1),
        )

        self.talla_input = toga.TextInput(
            placeholder="Ej: 68.0",
            style=Pack(flex=1),
        )

        self.perimetro_input = toga.TextInput(
            placeholder="Ej: 43.5",
            style=Pack(flex=1),
        )

        self.message_label = toga.Label(
            "",
            style=Pack(padding_top=SPACING_MD),
        )

    def build(self) -> toga.Widget:
        """Construye la interfaz del formulario de medición."""
        content = toga.Box(
            children=[
                title("Nueva medición"),
                info_row("Paciente", self.paciente_nombre),
                caption_text(self.paciente_info),
                subtitle("Datos de la medición"),
                field_label("Fecha de medición"),
                self.fecha_input,
                field_label("Peso (kg)"),
                self.peso_input,
                caption_text("Ingrese el peso en kilogramos"),
                field_label("Talla (cm)"),
                self.talla_input,
                caption_text("Longitud en menores de 2 años, talla en mayores"),
                field_label("Perímetro cefálico (cm)"),
                self.perimetro_input,
                caption_text("Opcional para mayores de 2 años"),
                primary_button("Calcular resultados", self.submit),
                toga.Button(
                    "← Volver al paciente",
                    on_press=self.go_back,
                    style=Pack(padding_top=SPACING_SM),
                ),
                self.message_label,
            ],
            style=Pack(
                direction=COLUMN,
                padding=24,
                flex=1,
            ),
        )

        return scroll_screen(content)

    def submit(self, widget: toga.Widget) -> None:
        """Envía los datos al controlador."""
        self.on_calculate(
            {
                "fecha_medicion": self.fecha_input.value,
                "peso_kg": self.peso_input.value,
                "talla_cm": self.talla_input.value,
                "perimetro_cefalico_cm": self.perimetro_input.value,
            }
        )

    def go_back(self, widget: toga.Widget) -> None:
        """Regresa a la pantalla anterior."""
        self.on_back()

    def show_error(self, message: str) -> None:
        """Muestra un mensaje de error."""
        self.message_label.text = message

    def show_success(self, message: str) -> None:
        """Muestra un mensaje de éxito."""
        self.message_label.text = message
