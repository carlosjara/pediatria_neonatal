"""Interfaz gráfica inicial de Pediatría Neonatal."""

from __future__ import annotations

import toga
from toga.style import Pack
from toga.style.pack import COLUMN


class PediatriaNeonatalApp(toga.App):
    """Aplicación principal."""

    def startup(self) -> None:
        """Construye y muestra la ventana principal."""

        titulo = toga.Label(
            "Pediatría Neonatal",
            style=Pack(
                font_size=24,
                font_weight="bold",
                margin_bottom=12,
            ),
        )

        mensaje = toga.Label(
            "La aplicación Toga está funcionando correctamente.",
            style=Pack(
                font_size=14,
                margin_bottom=16,
            ),
        )

        boton = toga.Button(
            "Continuar",
            on_press=self.mostrar_confirmacion,
            style=Pack(
                margin_top=12,
            ),
        )

        contenido = toga.Box(
            children=[
                titulo,
                mensaje,
                boton,
            ],
            style=Pack(
                direction=COLUMN,
                padding=24,
            ),
        )

        self.main_window = toga.MainWindow(
            title=self.formal_name,
            size=(500, 320),
        )
        self.main_window.content = contenido
        self.main_window.show()

    def mostrar_confirmacion(self, widget: toga.Widget) -> None:
        """Actualiza el título al pulsar el botón."""

        self.main_window.title = "Pediatría Neonatal — Activa"


def main() -> PediatriaNeonatalApp:
    """Crea la aplicación."""

    return PediatriaNeonatalApp(
        formal_name="Pediatría Neonatal",
        app_id="com.carlosjara.pediatria-neonatal",
    )