"""Vista para mostrar el historial de mediciones."""

from typing import Any

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from pediatria_neonatal.views.components import (
    COLOR_MUTED,
    FONT_SIZE_BODY,
    FONT_SIZE_CAPTION,
    FONT_SIZE_SUBTITLE,
    SPACING_MD,
    SPACING_SM,
    SPACING_XS,
    caption_text,
    get_clinical_color,
    scroll_screen,
    title,
)


class HistorialView:
    """Muestra el historial de mediciones del paciente."""

    def __init__(
        self,
        mediciones: list[dict[str, Any]],
    ) -> None:
        self.mediciones = mediciones

    def build(self) -> toga.Widget:
        """Construye la interfaz del historial."""
        children = [title("Historial de Mediciones")]

        if not self.mediciones:
            children.append(self._build_empty_state())
        else:
            children.append(
                caption_text(f"{len(self.mediciones)} mediciones registradas")
            )
            for medicion in self.mediciones:
                children.append(self._build_medicion_card(medicion))

        content = toga.Box(
            children=children,
            style=Pack(
                direction=COLUMN,
                padding=SPACING_MD,
                flex=1,
            ),
        )

        return scroll_screen(content)

    def _build_empty_state(self) -> toga.Box:
        """Construye el estado vacío cuando no hay mediciones."""
        return toga.Box(
            children=[
                toga.Label(
                    "📋",
                    style=Pack(
                        font_size=48,
                        text_align="center",
                        padding_top=SPACING_MD * 2,
                        padding_bottom=SPACING_MD,
                    ),
                ),
                toga.Label(
                    "Sin mediciones registradas",
                    style=Pack(
                        font_size=FONT_SIZE_SUBTITLE,
                        font_weight="bold",
                        text_align="center",
                        padding_bottom=SPACING_SM,
                    ),
                ),
                toga.Label(
                    "Las mediciones aparecerán aquí después de evaluar un paciente.",
                    style=Pack(
                        font_size=FONT_SIZE_BODY,
                        color=COLOR_MUTED,
                        text_align="center",
                    ),
                ),
            ],
            style=Pack(
                direction=COLUMN,
                padding=SPACING_MD,
                flex=1,
            ),
        )

    def _build_medicion_card(self, medicion: dict[str, Any]) -> toga.Box:
        """Construye una tarjeta de medición con toda la información visible."""
        fecha = medicion.get("fecha", "")
        paciente = medicion.get("paciente_nombre", "Paciente")
        imc = medicion.get("imc", 0)
        clasificacion = medicion.get("clasificacion", "")
        severidad = medicion.get("severidad", "normal")

        # Usar colores clínicos según clasificación
        color = get_clinical_color(clasificacion, severidad)

        # Extraer edad y edad corregida
        edad_texto = medicion.get("edad_texto", "")
        es_prematuro = medicion.get("es_prematuro", False)
        edad_corregida_texto = medicion.get("edad_corregida_texto", "")
        clasificacion_prematuro = medicion.get("clasificacion_prematuro", "")

        children = [
            # Nombre y fecha
            toga.Box(
                children=[
                    toga.Label(
                        paciente,
                        style=Pack(
                            font_size=FONT_SIZE_BODY,
                            font_weight="bold",
                            flex=1,
                        ),
                    ),
                    toga.Label(
                        fecha,
                        style=Pack(
                            font_size=FONT_SIZE_CAPTION,
                            color=COLOR_MUTED,
                        ),
                    ),
                ],
                style=Pack(direction=ROW, padding_bottom=SPACING_XS),
            ),
            # Edad
            toga.Label(
                f"Edad: {edad_texto}",
                style=Pack(font_size=FONT_SIZE_CAPTION, color=COLOR_MUTED),
            ),
            # Edad corregida (solo si es prematuro)
        ]

        if es_prematuro and edad_corregida_texto:
            children.append(
                toga.Label(
                    f"Edad corregida: {edad_corregida_texto}",
                    style=Pack(
                        font_size=FONT_SIZE_CAPTION,
                        color=COLOR_MUTED,
                        font_style="italic",
                    ),
                )
            )

        # Clasificación de prematuro
        if clasificacion_prematuro:
            # Usar colores clínicos para clasificación de prematuro
            color_prematuro = get_clinical_color(clasificacion_prematuro)
            children.append(
                toga.Label(
                    f"👶 {clasificacion_prematuro}",
                    style=Pack(
                        font_size=FONT_SIZE_CAPTION,
                        color=color_prematuro,
                        font_style="italic",
                    ),
                )
            )

        # IMC y clasificación
        children.append(
            toga.Box(
                children=[
                    toga.Label(
                        f"IMC: {imc:.2f}",
                        style=Pack(
                            font_size=FONT_SIZE_BODY,
                            flex=1,
                        ),
                    ),
                    toga.Label(
                        clasificacion,
                        style=Pack(
                            font_size=FONT_SIZE_BODY,
                            font_weight="bold",
                            color=color,
                        ),
                    ),
                ],
                style=Pack(direction=ROW, padding_top=SPACING_XS),
            ),
        )

        return toga.Box(
            children=children,
            style=Pack(
                direction=COLUMN,
                padding=SPACING_MD,
                # Remover background_color para que use el tema del sistema
            ),
        )
