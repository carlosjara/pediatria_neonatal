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
        on_calcular_edad: Callable[[], None] | None = None,
    ) -> None:
        self.paciente_nombre = paciente_nombre
        self.paciente_info = paciente_info
        self.on_calculate = on_calculate
        self.on_back = on_back
        self.on_calcular_edad = on_calcular_edad

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

        self.posicion_input = toga.Selection(
            items=["Acostado", "De pie"],
            value="Acostado",
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

        self.edad_corregida_label = toga.Label(
            "",
            style=Pack(
                padding_top=SPACING_SM,
                font_size=12,
                color="#6B7280",
            ),
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
                toga.Button(
                    "Calcular edad corregida",
                    on_press=self.calcular_edad,
                    style=Pack(padding_top=SPACING_SM, padding_bottom=SPACING_SM),
                ),
                self.edad_corregida_label,
                field_label("Peso (kg)"),
                self.peso_input,
                caption_text("Ingrese el peso en kilogramos"),
                field_label("Longitud / talla (cm)"),
                self.talla_input,
                caption_text(
                    "OMS ajusta 0.7 cm según edad y posición."
                ),
                field_label("Posición"),
                self.posicion_input,
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
                toga.Box(style=Pack(height=300)),
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
                "posicion": self.posicion_input.value,
            }
        )

    def calcular_edad(self, widget: toga.Widget) -> None:
        """Calcula y muestra la edad corregida para la fecha actual."""
        if self.on_calcular_edad:
            self.on_calcular_edad()

    def show_edad_corregida(self, resultado: dict) -> None:
        """Muestra el resultado del cálculo de edad corregida."""
        edad_cronologica = resultado.get("edad_cronologica_texto", "")
        edad_corregida = resultado.get("edad_corregida_texto", "")

        texto = f"Edad cronológica: {edad_cronologica}"

        if resultado.get("es_prematuro", False) and edad_corregida:
            texto += f"\nEdad corregida: {edad_corregida}"

        self.edad_corregida_label.text = texto

    def go_back(self, widget: toga.Widget) -> None:
        """Regresa a la pantalla anterior."""
        self.on_back()

    def show_error(self, message: str) -> None:
        """Muestra un mensaje de error."""
        self.message_label.text = message

    def show_success(self, message: str) -> None:
        """Muestra un mensaje de éxito."""
        self.message_label.text = message
