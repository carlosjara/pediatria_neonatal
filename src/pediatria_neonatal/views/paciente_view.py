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


class PacienteView:
    """Formulario visual para registrar un paciente."""

    def __init__(
        self,
        on_save: Callable[[dict], None],
        on_calcular_edad: Callable[[], None] | None = None,
    ) -> None:
        self.on_save = on_save
        self.on_calcular_edad = on_calcular_edad
        self.selected_sex = "Masculino"

        # Botones de género para controlar estado presionado
        self.masculino_button = None
        self.femenino_button = None

        self.nombre_input = toga.TextInput(
            placeholder="Nombre completo",
            style=Pack(flex=1),
        )

        self.fecha_nacimiento_input = toga.DateInput(
            value=date.today(),
            max=date.today(),
            style=Pack(flex=1),
        )

        self.semanas_input = toga.TextInput(
            placeholder="Semanas",
            style=Pack(flex=1, padding_right=6),
        )

        self.dias_input = toga.TextInput(
            placeholder="Días",
            style=Pack(flex=1, padding_left=6),
        )

        self.peso_input = toga.TextInput(
            placeholder="Peso al nacer en gramos",
            style=Pack(flex=1),
        )

        self.prematuro_switch = toga.Switch(
            "Es prematuro",
            value=False,
            style=Pack(
                padding_top=12,
                padding_bottom=12,
            ),
        )

        self.message_label = toga.Label(
            "",
            style=Pack(padding_top=12),
        )

    def build(self) -> toga.Widget:
        # Crear botones de género
        self.masculino_button = toga.Button(
            "Masculino",
            on_press=self.select_male,
            style=Pack(flex=1, padding_right=5),
        )
        self.femenino_button = toga.Button(
            "Femenino",
            on_press=self.select_female,
            style=Pack(flex=1, padding_left=5),
        )
        
        # Establecer estado inicial
        self.masculino_button.enabled = False  # Simula botón presionado
        
        sex_row = toga.Box(
            children=[
                self.masculino_button,
                self.femenino_button,
            ],
            style=Pack(direction=ROW),
        )

        gestational_age_row = toga.Box(
            children=[
                self.semanas_input,
                self.dias_input,
            ],
            style=Pack(direction=ROW),
        )

        content = toga.Box(
            children=[
                title("Nuevo paciente"),
                subtitle("Datos generales"),
                field_label("Nombre"),
                self.nombre_input,
                field_label("Fecha de nacimiento"),
                self.fecha_nacimiento_input,
                field_label("Sexo"),
                sex_row,
                subtitle("Datos al nacimiento"),
                field_label("Edad gestacional"),
                gestational_age_row,
                field_label("Peso al nacer (gramos)"),
                self.peso_input,
                self.prematuro_switch,
                toga.Button(
                    "Guardar paciente",
                    on_press=self.submit,
                    style=Pack(
                        padding_top=18,
                        padding_bottom=8,
                    ),
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

    def select_male(self, widget: toga.Widget) -> None:
        """Selecciona género masculino y actualiza estado de botones."""
        if self.selected_sex != "Masculino":
            self.selected_sex = "Masculino"
            # Actualizar estado de botones
            self.masculino_button.enabled = False  # Presionado
            self.femenino_button.enabled = True   # No presionado
            self.message_label.text = "Sexo seleccionado: Masculino"

    def select_female(self, widget: toga.Widget) -> None:
        """Selecciona género femenino y actualiza estado de botones."""
        if self.selected_sex != "Femenino":
            self.selected_sex = "Femenino"
            # Actualizar estado de botones
            self.masculino_button.enabled = True   # No presionado
            self.femenino_button.enabled = False  # Presionado
            self.message_label.text = "Sexo seleccionado: Femenino"

    def submit(self, widget: toga.Widget) -> None:
        self.on_save(
            {
                "nombre": self.nombre_input.value,
                "fecha_nacimiento": self.fecha_nacimiento_input.value,
                "sexo": self.selected_sex,
                "semanas": self.semanas_input.value,
                "dias": self.dias_input.value,
                "peso_nacer": self.peso_input.value,
                "prematuro": self.prematuro_switch.value,
            }
        )

    def calcular_edad(self, widget: toga.Widget) -> None:
        """Abre la calculadora de edad corregida."""
        if self.on_calcular_edad:
            self.on_calcular_edad()

    def show_error(self, message: str) -> None:
        self.message_label.text = message