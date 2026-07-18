"""Componentes visuales reutilizables con estilo descansado para médicos."""

import toga
from toga.style import Pack
from toga.style.pack import CENTER, COLUMN, ROW

from pediatria_neonatal.presentation.resultados import (
    IndicatorSummaryCard,
    MainResultCard,
)

SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 16
SPACING_LG = 24
SPACING_XL = 32

FONT_SIZE_CAPTION = 11
FONT_SIZE_BODY = 14
FONT_SIZE_SUBTITLE = 16
FONT_SIZE_TITLE = 22
FONT_SIZE_HERO = 28

COLOR_PRIMARY = "#2563EB"
COLOR_SUCCESS = "#16A34A"
COLOR_WARNING = "#D97706"
COLOR_DANGER = "#DC2626"
COLOR_MUTED = "#9CA3AF"
COLOR_BACKGROUND = None
COLOR_CARD_BORDER = "#E5E7EB"
COLOR_CARD_SOFT = "#F8FAFC"

# Colores clínicos para clasificaciones de crecimiento
COLOR_SEVERE_UNDERWEIGHT = "#B91C1C"  # Rojo intenso - desnutrición severa
COLOR_MODERATE_UNDERWEIGHT = "#EA580C"  # Naranja - bajo peso moderado
COLOR_MILD_UNDERWEIGHT = "#F59E0B"  # Amarillo - bajo peso leve
COLOR_NORMAL = "#16A34A"  # Verde - normal
COLOR_OVERWEIGHT = "#D97706"  # Amarillo oscuro - sobrepeso
COLOR_OBESITY = "#DC2626"  # Rojo - obesidad

# Colores específicos para clasificaciones de prematuro
COLOR_PREMATURE_EXTREME = "#7C3AED"  # Púrpura intenso para prematuro extremo
COLOR_PREMATURE_VERY_PRETERM = "#A855F7"  # Púrpura para muy prematuro
COLOR_PREMATURE_MODERATE = "#C084FC"  # Púrpura claro para prematuro moderado
COLOR_PREMATURE_LATE = "#E9D5FF"  # Púrpura muy claro para prematuro tardío


def _soft_background_for_color(color: str) -> str:
    """Color pastel estable para resaltar resultados clínicos."""
    color_map = {
        COLOR_SUCCESS: "#DCFCE7",
        COLOR_NORMAL: "#DCFCE7",
        COLOR_WARNING: "#FEF3C7",
        COLOR_OVERWEIGHT: "#FEF3C7",
        COLOR_DANGER: "#FEE2E2",
        COLOR_OBESITY: "#FEE2E2",
        "#1D4ED8": "#DBEAFE",
        COLOR_MUTED: "#F3F4F6",
    }
    return color_map.get(color, "#F3F4F6")


def _soft_panel(children: list[toga.Widget], background: str = COLOR_CARD_SOFT):
    """Panel con fondo suave compatible con Toga 0.5.6."""
    return toga.Box(
        children=children,
        style=Pack(
            direction=COLUMN,
            background_color=background,
            padding=SPACING_MD,
        ),
    )


def _soft_row_panel(children: list[toga.Widget], background: str) -> toga.Box:
    return toga.Box(
        children=children,
        style=Pack(
            direction=ROW,
            background_color=background,
            padding=SPACING_SM,
        ),
    )


def get_clinical_color(clasificacion: str, severidad: str = "normal") -> str:
    """Devuelve el color clínico apropiado según clasificación y severidad."""
    # Mapeo de clasificaciones a colores
    color_map = {
        # Bajo peso
        "Desnutrición severa": COLOR_SEVERE_UNDERWEIGHT,
        "Bajo peso severo": COLOR_SEVERE_UNDERWEIGHT,
        "Bajo peso moderado": COLOR_MODERATE_UNDERWEIGHT,
        "Bajo peso leve": COLOR_MILD_UNDERWEIGHT,
        "Bajo peso": COLOR_MODERATE_UNDERWEIGHT,
        "Normal bajo": COLOR_MILD_UNDERWEIGHT,
        # Normal
        "Normal": COLOR_NORMAL,
        "Eutrofia": COLOR_NORMAL,
        # Sobrepeso y obesidad
        "Sobrepeso": COLOR_OVERWEIGHT,
        "Obesidad": COLOR_OBESITY,
        "Obesidad severa": COLOR_OBESITY,
        # Clasificaciones de prematuro
        "Prematuro extremo": COLOR_PREMATURE_EXTREME,
        "Prematuro muy precoz": COLOR_PREMATURE_VERY_PRETERM,
        "Prematuro moderado": COLOR_PREMATURE_MODERATE,
        "Prematuro tardío": COLOR_PREMATURE_LATE,
    }

    # Si no encuentra la clasificación, usa el sistema de severidad anterior
    if clasificacion not in color_map:
        severity_map = {
            "alta": COLOR_OBESITY,
            "moderada": COLOR_MODERATE_UNDERWEIGHT,
            "observacion": COLOR_WARNING,
            "normal": COLOR_NORMAL,
        }
        return severity_map.get(severidad, COLOR_MUTED)

    return color_map.get(clasificacion, COLOR_NORMAL)


def title(text: str) -> toga.Label:
    """Título principal de pantalla - grande y claro."""
    return toga.Label(
        text,
        style=Pack(
            font_size=FONT_SIZE_TITLE,
            font_weight="bold",
            padding_bottom=SPACING_LG,
        ),
    )


def subtitle(text: str) -> toga.Label:
    """Subtítulo de sección - separación visual clara."""
    return toga.Label(
        text,
        style=Pack(
            font_size=FONT_SIZE_SUBTITLE,
            font_weight="bold",
            padding_top=SPACING_LG,
            padding_bottom=SPACING_SM,
        ),
    )


def field_label(text: str) -> toga.Label:
    """Etiqueta de campo - legible y con espacio."""
    return toga.Label(
        text,
        style=Pack(
            font_size=FONT_SIZE_BODY,
            padding_top=SPACING_MD,
            padding_bottom=SPACING_XS,
        ),
    )


def body_text(text: str, wrap: bool = True) -> toga.MultilineTextInput:
    """Texto de cuerpo - lectura cómoda con wrap automático."""
    if wrap:
        widget = toga.MultilineTextInput(
            value=text,
            readonly=True,
            style=Pack(
                font_size=FONT_SIZE_BODY,
                padding_top=SPACING_XS,
                padding_bottom=SPACING_XS,
                flex=1,
                height=60,
            ),
        )
        return widget
    return toga.Label(
        text,
        style=Pack(
            font_size=FONT_SIZE_BODY,
            padding_top=SPACING_XS,
            padding_bottom=SPACING_XS,
        ),
    )


def caption_text(text: str, color: str = COLOR_MUTED) -> toga.Label:
    """Texto secundario - información complementaria."""
    return toga.Label(
        text,
        style=Pack(
            font_size=FONT_SIZE_CAPTION,
            color=color,
            padding_top=SPACING_XS,
        ),
    )


def wrapped_text(text: str, height: int = 80) -> toga.MultilineTextInput:
    """Texto largo con wrap automático - para descripciones."""
    return toga.MultilineTextInput(
        value=text,
        readonly=True,
        style=Pack(
            font_size=FONT_SIZE_BODY,
            padding_top=SPACING_SM,
            padding_bottom=SPACING_SM,
            flex=1,
            height=height,
        ),
    )


def alert_box(
    text: str,
    severity: str = "info",
) -> toga.Box:
    """Caja de alerta con color según severidad."""
    color_map = {
        "info": COLOR_PRIMARY,
        "success": COLOR_SUCCESS,
        "warning": COLOR_WARNING,
        "danger": COLOR_DANGER,
    }
    icon_map = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "danger": "🚨",
    }

    return toga.Box(
        children=[
            toga.MultilineTextInput(
                value=f"{icon_map.get(severity, '')} {text}",
                readonly=True,
                style=Pack(
                    font_size=FONT_SIZE_BODY,
                    color=color_map.get(severity, COLOR_MUTED),
                    flex=1,
                    height=64,
                ),
            ),
        ],
        style=Pack(
            direction=ROW,
            padding=SPACING_MD,
            # Remover background_color para que use el tema del sistema
        ),
    )


def badge(
    text: str,
    color: str = COLOR_PRIMARY,
    bg_color: str = "#EFF6FF",
) -> toga.Box:
    """Badge/etiqueta pequeña para indicadores."""
    return toga.Box(
        children=[
            toga.Label(
                text,
                style=Pack(
                    font_size=FONT_SIZE_CAPTION,
                    font_weight="bold",
                    color=color,
                ),
            ),
        ],
        style=Pack(
            padding_top=SPACING_XS,
            padding_bottom=SPACING_XS,
            padding_left=SPACING_SM,
            padding_right=SPACING_SM,
            # Remover background_color para que use el tema del sistema
        ),
    )


def prematurity_badge(es_prematuro: bool, semanas: int = 0) -> toga.Box:
    """Badge específico para indicar prematuridad."""
    if not es_prematuro:
        return badge("Término", COLOR_SUCCESS, "#F0FDF4")

    if semanas < 28:
        return badge("Prematuro extremo", COLOR_DANGER, "#FEF2F2")
    elif semanas < 32:
        return badge("Muy prematuro", COLOR_WARNING, "#FFFBEB")
    elif semanas < 37:
        return badge("Prematuro tardío", COLOR_WARNING, "#FFFBEB")
    else:
        return badge("Término", COLOR_SUCCESS, "#F0FDF4")


def hero_value(value: str, unit: str = "") -> toga.Box:
    """Valor destacado grande - para resultados principales."""
    children = [
        toga.Label(
            value,
            style=Pack(
                font_size=FONT_SIZE_HERO,
                font_weight="bold",
                text_align=CENTER,
            ),
        ),
    ]
    if unit:
        children.append(
            toga.Label(
                unit,
                style=Pack(
                    font_size=FONT_SIZE_BODY,
                    color=COLOR_MUTED,
                    padding_left=SPACING_XS,
                ),
            ),
        )
    return toga.Box(
        children=children,
        style=Pack(
            direction=ROW,
            alignment=CENTER,
            padding_top=SPACING_SM,
            padding_bottom=SPACING_SM,
        ),
    )


def result_card(
    label: str,
    value: str,
    detail: str = "",
    severity: str = "normal",
) -> toga.Box:
    """Tarjeta de resultado clínico con indicador de severidad."""
    color_map = {
        "normal": COLOR_SUCCESS,
        "observacion": COLOR_WARNING,
        "moderada": COLOR_WARNING,
        "alta": COLOR_DANGER,
    }
    accent_color = color_map.get(severity, COLOR_MUTED)

    children = [
        toga.Label(
            label,
            style=Pack(
                font_size=FONT_SIZE_CAPTION,
                color=COLOR_MUTED,
            ),
        ),
        toga.Label(
            value,
            style=Pack(
                font_size=FONT_SIZE_SUBTITLE,
                font_weight="bold",
                color=accent_color,
                padding_top=SPACING_XS,
            ),
        ),
    ]

    if detail:
        children.append(
            toga.MultilineTextInput(
                value=detail,
                readonly=True,
                style=Pack(
                    font_size=FONT_SIZE_CAPTION,
                    padding_top=SPACING_XS,
                    height=50,
                    flex=1,
                ),
            ),
        )

    return toga.Box(
        children=children,
        style=Pack(
            direction=COLUMN,
            padding=SPACING_MD,
            padding_bottom=SPACING_SM,
        ),
    )


def section_header(title_text: str, subtitle_text: str = "") -> toga.Box:
    """Encabezado de sección con título y subtítulo opcional."""
    children = [
        toga.Label(
            title_text,
            style=Pack(
                font_size=FONT_SIZE_SUBTITLE,
                font_weight="bold",
                padding_bottom=SPACING_XS,
            ),
        ),
    ]

    if subtitle_text:
        children.append(
            toga.Label(
                subtitle_text,
                style=Pack(
                    font_size=FONT_SIZE_CAPTION,
                    color=COLOR_MUTED,
                ),
            ),
        )

    return toga.Box(
        children=children,
        style=Pack(
            direction=COLUMN,
            padding_top=SPACING_LG,
            padding_bottom=SPACING_SM,
        ),
    )


def patient_summary_card(
    nombre: str,
    edad_texto: str,
    sexo: str,
    es_prematuro: bool,
    semanas_eg: int,
    peso_nacer: float,
) -> toga.Box:
    """Tarjeta resumen del paciente para contexto clínico."""
    children = [
        toga.Box(
            children=[
                toga.Label(
                    nombre,
                    style=Pack(
                        font_size=FONT_SIZE_SUBTITLE,
                        font_weight="bold",
                        flex=1,
                    ),
                ),
                prematurity_badge(es_prematuro, semanas_eg),
            ],
            style=Pack(direction=ROW, padding_bottom=SPACING_SM),
        ),
        toga.Box(
            children=[
                toga.Label(
                    f"Sexo: {sexo}",
                    style=Pack(font_size=FONT_SIZE_BODY),
                ),
                toga.Box(style=Pack(flex=1)),
                toga.Label(
                    f"EG: {semanas_eg} sem",
                    style=Pack(font_size=FONT_SIZE_BODY),
                ),
            ],
            style=Pack(direction=ROW, padding_bottom=SPACING_SM),
        ),
        toga.Label(
            f"Peso al nacer: {peso_nacer:.0f} g",
            style=Pack(
                font_size=FONT_SIZE_BODY,
                padding_bottom=SPACING_SM,
            ),
        ),
    ]

    return toga.Box(
        children=children,
        style=Pack(
            direction=COLUMN,
            padding=SPACING_MD,
        ),
    )


def main_result_card(result: MainResultCard) -> toga.Box:
    """Tarjeta principal del resumen de resultados."""
    semantic_background = _soft_background_for_color(result.semantic_color)

    content = [
        toga.Label(
            "IMC para la edad",
            style=Pack(
                font_size=FONT_SIZE_SUBTITLE,
                font_weight="bold",
                text_align=CENTER,
            ),
        ),
        toga.Label(
            "(OMS 2006)",
            style=Pack(
                font_size=FONT_SIZE_SUBTITLE,
                font_weight="bold",
                text_align=CENTER,
                padding_bottom=SPACING_SM,
            ),
        ),
        _soft_panel(
            [
                toga.Label(
                    f"{result.value_text} {result.unit}",
                    style=Pack(
                        font_size=FONT_SIZE_HERO,
                        font_weight="bold",
                        text_align=CENTER,
                    ),
                ),
            ],
            background="#FFFFFF",
        ),
        toga.Box(style=Pack(height=SPACING_SM)),
        _soft_row_panel(
            [
                toga.Label(
                    f"{result.z_score_text} (Z-score)",
                    style=Pack(
                        font_size=FONT_SIZE_BODY,
                        font_weight="bold",
                        color=result.semantic_color,
                        flex=1,
                    ),
                ),
                toga.Label(
                    result.percentile_text,
                    style=Pack(
                        font_size=FONT_SIZE_BODY,
                        font_weight="bold",
                        color=result.semantic_color,
                        text_align=CENTER,
                    ),
                ),
            ],
            background=semantic_background,
        ),
        toga.Box(style=Pack(height=SPACING_SM)),
        toga.Label(
            "Clasificación",
            style=Pack(
                font_size=FONT_SIZE_CAPTION,
                color=COLOR_MUTED,
                text_align=CENTER,
                padding_bottom=SPACING_XS,
            ),
        ),
        _soft_panel(
            [
                toga.Label(
                    result.classification_text,
                    style=Pack(
                        font_size=FONT_SIZE_SUBTITLE,
                        font_weight="bold",
                        color=result.semantic_color,
                        text_align=CENTER,
                    ),
                ),
            ],
            background=semantic_background,
        ),
    ]

    return toga.Box(
        children=[
            toga.Box(
                children=[
                    _soft_panel(content, background=COLOR_CARD_SOFT),
                ],
                style=Pack(
                    direction=COLUMN,
                    background_color=COLOR_CARD_BORDER,
                    padding=1,
                ),
            )
        ],
        style=Pack(
            direction=COLUMN,
            padding_top=SPACING_SM,
            padding_bottom=SPACING_MD,
        ),
    )


def indicator_summary_card(
    item: IndicatorSummaryCard,
    on_press: callable,
) -> toga.Box:
    """Tarjeta compacta para un indicador secundario."""
    background = _soft_background_for_color(item.semantic_color)

    content = [
        toga.Label(
            item.label,
            style=Pack(
                font_size=FONT_SIZE_CAPTION,
                font_weight="bold",
                color=item.semantic_color,
                text_align=CENTER,
                padding_bottom=SPACING_XS,
            ),
        ),
        toga.Label(
            item.z_score_text,
            style=Pack(
                font_size=FONT_SIZE_BODY,
                font_weight="bold",
                color=item.semantic_color,
                text_align=CENTER,
            ),
        ),
        toga.Label(
            item.percentile_text,
            style=Pack(
                font_size=FONT_SIZE_BODY,
                font_weight="bold",
                color=item.semantic_color,
                text_align=CENTER,
            ),
        ),
        toga.Label(
            item.classification_text,
            style=Pack(
                font_size=FONT_SIZE_CAPTION,
                color=item.semantic_color,
                text_align=CENTER,
                padding_bottom=SPACING_XS,
            ),
        ),
        toga.Button(
            "Detalle",
            on_press=on_press,
            style=Pack(
                font_size=FONT_SIZE_CAPTION,
                padding_top=SPACING_XS,
                padding_bottom=SPACING_XS,
            ),
        ),
    ]

    return toga.Box(
        children=[
            toga.Box(
                children=[_soft_panel(content, background=background)],
                style=Pack(
                    direction=COLUMN,
                    background_color=COLOR_CARD_BORDER,
                    padding=1,
                    flex=1,
                    height=132,
                ),
            ),
        ],
        style=Pack(
            direction=COLUMN,
            flex=1,
            height=132,
            padding=SPACING_SM,
        ),
    )


def results_summary_grid(
    indicators: tuple[IndicatorSummaryCard, ...],
    on_select: callable,
) -> toga.Box:
    """Grilla 2x2 de indicadores OMS para iPhone."""

    rows: list[toga.Box] = []
    for index in range(0, len(indicators), 2):
        pair = indicators[index : index + 2]
        row_children: list[toga.Widget] = []
        for item_index, item in enumerate(pair):
            if item_index > 0:
                row_children.append(toga.Box(style=Pack(width=SPACING_SM)))
            row_children.append(
                indicator_summary_card(
                    item,
                    lambda widget, key=item.key: on_select(key),
                )
            )
        rows.append(
            toga.Box(
                children=row_children,
                style=Pack(
                    direction=ROW,
                    padding_top=SPACING_XS,
                    padding_bottom=SPACING_XS,
                ),
            )
        )

    return toga.Box(
        children=rows,
        style=Pack(
            direction=COLUMN,
            padding_top=SPACING_SM,
            padding_bottom=SPACING_SM,
        ),
    )


def zscore_chart(
    *,
    title_text: str,
    z_score: float,
    percentile_text: str,
    classification: str,
    color: str,
) -> toga.Box:
    """Gráfico horizontal compacto de posición por z-score."""

    marker_index = _zscore_marker_index(z_score)
    band_labels = ["Muy bajo", "Bajo", "Normal", "Alto", "Muy alto"]
    band_colors = [
        COLOR_DANGER,
        COLOR_WARNING,
        COLOR_SUCCESS,
        COLOR_OVERWEIGHT,
        COLOR_DANGER,
    ]

    return toga.Box(
        children=[
            toga.Label(
                title_text,
                style=Pack(
                    font_size=FONT_SIZE_SUBTITLE,
                    font_weight="bold",
                    padding_bottom=SPACING_SM,
                ),
            ),
            toga.Box(
                children=[
                    _chart_label(label, band_color)
                    for label, band_color in zip(band_labels, band_colors)
                ],
                style=Pack(direction=ROW, padding_bottom=SPACING_XS),
            ),
            toga.Box(
                children=[
                    _chart_marker_cell(index == marker_index, color)
                    for index in range(9)
                ],
                style=Pack(direction=ROW, padding_bottom=SPACING_SM),
            ),
            toga.Label(
                f"Z-score {z_score:+.2f} DE · {percentile_text}",
                style=Pack(
                    font_size=FONT_SIZE_BODY,
                    font_weight="bold",
                    color=color,
                    text_align=CENTER,
                    padding_bottom=SPACING_XS,
                ),
            ),
            toga.Label(
                classification,
                style=Pack(
                    font_size=FONT_SIZE_BODY,
                    font_weight="bold",
                    color=color,
                    text_align=CENTER,
                ),
            ),
        ],
        style=Pack(
            direction=COLUMN,
            padding=SPACING_MD,
        ),
    )


def _chart_label(text: str, color: str) -> toga.Label:
    return toga.Label(
        text,
        style=Pack(
            flex=1,
            font_size=10,
            font_weight="bold",
            color=color,
            text_align=CENTER,
        ),
    )


def _chart_marker_cell(is_current: bool, color: str) -> toga.Label:
    return toga.Label(
        "▲" if is_current else "─",
        style=Pack(
            flex=1,
            font_size=12,
            font_weight="bold",
            color=color if is_current else COLOR_MUTED,
            text_align=CENTER,
        ),
    )


def _zscore_marker_index(z_score: float) -> int:
    clipped = min(4.0, max(-4.0, float(z_score)))
    return round(((clipped + 4.0) / 8.0) * 8)


def age_display(
    edad_cronologica: str,
    edad_corregida: str = "",
    es_prematuro: bool = False,
) -> toga.Box:
    """Muestra prominente de edad cronológica y corregida."""
    children = [
        toga.Box(
            children=[
                toga.Label(
                    "Edad cronológica:",
                    style=Pack(
                        font_size=FONT_SIZE_CAPTION,
                        color=COLOR_MUTED,
                    ),
                ),
                toga.Label(
                    edad_cronologica,
                    style=Pack(
                        font_size=FONT_SIZE_BODY,
                        font_weight="bold",
                        padding_left=SPACING_SM,
                    ),
                ),
            ],
            style=Pack(direction=ROW, padding_bottom=SPACING_XS),
        ),
    ]

    if es_prematuro and edad_corregida:
        es_antes_termino = "término" in edad_corregida.lower()
        color_edad = COLOR_WARNING if es_antes_termino else COLOR_PRIMARY

        children.append(
            toga.Box(
                children=[
                    toga.Label(
                        "Edad corregida:",
                        style=Pack(
                            font_size=FONT_SIZE_CAPTION,
                            color=COLOR_MUTED,
                        ),
                    ),
                    toga.Label(
                        edad_corregida,
                        style=Pack(
                            font_size=FONT_SIZE_SUBTITLE,
                            font_weight="bold",
                            color=color_edad,
                            padding_left=SPACING_SM,
                        ),
                    ),
                ],
                style=Pack(direction=ROW),
            ),
        )

        if es_antes_termino:
            mensaje = "⏳ Paciente aún en período neonatal pretérmino"
        else:
            mensaje = "📊 Se usa edad corregida para evaluación"

        children.append(
            toga.Label(
                mensaje,
                style=Pack(
                    font_size=FONT_SIZE_CAPTION,
                    color=COLOR_WARNING if es_antes_termino else COLOR_PRIMARY,
                    padding_top=SPACING_XS,
                ),
            ),
        )

    return toga.Box(
        children=children,
        style=Pack(
            direction=COLUMN,
            padding=SPACING_MD,
        ),
    )


def info_row(label: str, value: str) -> toga.Box:
    """Fila de información label: value."""
    return toga.Box(
        children=[
            toga.Label(
                f"{label}:",
                style=Pack(
                    font_size=FONT_SIZE_BODY,
                    font_weight="bold",
                    padding_right=SPACING_SM,
                ),
            ),
            toga.Label(
                value,
                style=Pack(
                    font_size=FONT_SIZE_BODY,
                    flex=1,
                ),
            ),
        ],
        style=Pack(
            direction=ROW,
            padding_top=SPACING_XS,
            padding_bottom=SPACING_XS,
        ),
    )


def primary_button(
    text: str,
    on_press: callable,
) -> toga.Button:
    """Botón principal - acción destacada."""
    return toga.Button(
        text,
        on_press=on_press,
        style=Pack(
            padding_top=SPACING_LG,
            padding_bottom=SPACING_SM,
            font_size=FONT_SIZE_BODY,
            font_weight="bold",
        ),
    )


def secondary_button(
    text: str,
    on_press: callable,
) -> toga.Button:
    """Botón secundario - acción alternativa."""
    return toga.Button(
        text,
        on_press=on_press,
        style=Pack(
            padding_top=SPACING_SM,
            padding_bottom=SPACING_SM,
            font_size=FONT_SIZE_BODY,
        ),
    )


def spacer(size: int = SPACING_MD) -> toga.Box:
    """Espaciador vertical."""
    return toga.Box(style=Pack(height=size))


def divider() -> toga.Box:
    """Línea divisoria sutil."""
    return toga.Box(
        style=Pack(
            height=1,
            # Remover background_color para que use el tema del sistema
            padding_top=SPACING_MD,
            padding_bottom=SPACING_MD,
        ),
    )


def scroll_screen(content: toga.Widget) -> toga.ScrollContainer:
    """Contenedor scrolleable para pantallas largas."""
    return toga.ScrollContainer(
        content=content,
        horizontal=False,
        style=Pack(flex=1),
    )


def screen_box(*children: toga.Widget) -> toga.Box:
    """Contenedor principal de pantalla con padding generoso."""
    return toga.Box(
        children=list(children),
        style=Pack(
            direction=COLUMN,
            padding=SPACING_LG,
            flex=1,
        ),
    )


def card_box(*children: toga.Widget) -> toga.Box:
    """Tarjeta contenedora con fondo y padding."""
    return toga.Box(
        children=list(children),
        style=Pack(
            direction=COLUMN,
            padding=SPACING_MD,
        ),
    )


def row_box(*children: toga.Widget) -> toga.Box:
    """Fila horizontal con espaciado."""
    return toga.Box(
        children=list(children),
        style=Pack(
            direction=ROW,
            padding_top=SPACING_SM,
            padding_bottom=SPACING_SM,
        ),
    )
