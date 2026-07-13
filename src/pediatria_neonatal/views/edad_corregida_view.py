"""Vista para calcular edad corregida rápidamente."""

from collections.abc import Callable
from datetime import date

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from pediatria_neonatal.views.components import (
    field_label,
    scroll_screen,
    subtitle,
    title,
)


class EdadCorregidaView:
    """Formulario para calcular edad corregida sin mediciones."""

    def __init__(
        self,
        paciente_data: dict,
        on_calculate: Callable[[dict], None],
        on_back: Callable[[], None],
    ) -> None:
        self.paciente_data = paciente_data
        self.on_calculate = on_calculate
        self.on_back = on_back

        # Fecha de medición por defecto: hoy
        self.fecha_medicion_input = toga.DateInput(
            value=date.today(),
            max=date.today(),
            style=Pack(flex=1),
        )

        self.resultado_label = toga.Label(
            "",
            style=Pack(padding_top=20, font_size=14),
        )

    def build(self) -> toga.Widget:
        """Construye la interfaz de cálculo de edad corregida."""
        # Información del paciente
        paciente_info = (
            f"Paciente: {self.paciente_data.get('nombre', '')}\n"
            f"Fecha nacimiento: {self.paciente_data.get('fecha_nacimiento', '')}\n"
            f"Edad gestacional: {self.paciente_data.get('semanas_eg', 0)}+{self.paciente_data.get('dias_eg', 0)}\n"
            f"Prematuro: {'Sí' if self.paciente_data.get('es_prematuro', False) else 'No'}"
        )

        content = toga.Box(
            children=[
                title("Edad Corregida"),
                subtitle("Cálculo rápido"),
                toga.Label(
                    paciente_info,
                    style=Pack(
                        font_size=12,
                        padding_bottom=20,
                        color="#6B7280",
                    ),
                ),
                field_label("Fecha de medición"),
                self.fecha_medicion_input,
                toga.Button(
                    "Calcular edad corregida",
                    on_press=self.calculate,
                    style=Pack(
                        padding_top=18,
                        padding_bottom=8,
                    ),
                ),
                self.resultado_label,
                toga.Button(
                    "← Volver",
                    on_press=self.go_back,
                    style=Pack(padding_top=16),
                ),
            ],
            style=Pack(
                direction=COLUMN,
                padding=24,
                flex=1,
            ),
        )

        return scroll_screen(content)

    def calculate(self, widget: toga.Widget) -> None:
        """Calcula la edad corregida."""
        self.on_calculate(
            {
                "fecha_medicion": self.fecha_medicion_input.value,
            }
        )

    def go_back(self, widget: toga.Widget) -> None:
        """Regresa a la pantalla anterior."""
        self.on_back()

    def show_result(self, resultado: dict) -> None:
        """Muestra el resultado del cálculo."""
        edad_cronologica = resultado.get("edad_cronologica_texto", "")
        edad_corregida = resultado.get("edad_corregida_texto", "")
        
        texto_resultado = f"Edad cronológica: {edad_cronologica}"
        
        if resultado.get("es_prematuro", False) and edad_corregida:
            texto_resultado += f"\nEdad corregida: {edad_corregida}"
        
        self.resultado_label.text = texto_resultado

    def show_error(self, message: str) -> None:
        """Muestra un mensaje de error."""
        self.resultado_label.text = f"Error: {message}"
