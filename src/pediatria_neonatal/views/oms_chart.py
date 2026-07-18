"""Canvas OMS 2006 para detalle de indicadores."""

from __future__ import annotations

from collections.abc import Callable

import toga
from toga.fonts import BOLD, NORMAL, SYSTEM, Font
from toga.style import Pack
from toga.style.pack import CENTER, COLUMN, ROW

from pediatria_neonatal.presentation.oms_chart import (
    OmsChartCurve,
    OmsChartModel,
)
from pediatria_neonatal.views.components import (
    COLOR_MUTED,
    SPACING_MD,
    SPACING_SM,
    SPACING_XS,
    caption_text,
)

CHART_HEIGHT = 310
CHART_PADDING_LEFT = 46
CHART_PADDING_RIGHT = 40
CHART_PADDING_TOP = 28
CHART_PADDING_BOTTOM = 42


def oms_curve_chart(model: OmsChartModel) -> toga.Box:
    """Crea una gráfica OMS con curvas percentilares y punto del paciente."""

    canvas = toga.Canvas(style=Pack(height=CHART_HEIGHT, flex=1))
    canvas.on_resize = _draw_on_resize(model)
    _prime_canvas(canvas, model)

    return toga.Box(
        children=[
            toga.Label(
                model.title,
                style=Pack(
                    font_size=16,
                    font_weight="bold",
                    text_align=CENTER,
                    padding_bottom=SPACING_XS,
                ),
            ),
            toga.Box(
                children=[
                    caption_text(f"Z-score: {model.z_score_text}"),
                    toga.Box(style=Pack(flex=1)),
                    caption_text(f"Percentil: {model.percentile_text}"),
                ],
                style=Pack(direction=ROW, padding_bottom=SPACING_SM),
            ),
            canvas,
        ],
        style=Pack(direction=COLUMN, padding=SPACING_MD),
    )


def _prime_canvas(canvas: toga.Canvas, model: OmsChartModel) -> None:
    """Dibuja una primera versión antes del resize nativo en iOS."""

    canvas.root_state.drawing_actions.clear()
    _draw_chart(canvas, model, 320, CHART_HEIGHT)


def _draw_on_resize(model: OmsChartModel) -> Callable[..., None]:
    """Devuelve el handler que redibuja la gráfica al conocer el ancho real."""

    def draw(widget: toga.Canvas, width: int, height: int, **kwargs: object) -> None:
        widget.root_state.drawing_actions.clear()
        _draw_chart(widget, model, max(width, 260), max(height, CHART_HEIGHT))
        widget.redraw()

    return draw


def _draw_chart(
    canvas: toga.Canvas,
    model: OmsChartModel,
    width: int,
    height: int,
) -> None:
    plot = _PlotArea(width=width, height=height)
    x_min = model.view_x_min
    x_max = model.view_x_max
    y_min, y_max = _range_for_values(model.visible_y_values, pad_ratio=0.08)

    _fill_background(canvas, width, height)
    _draw_grid(canvas, plot, x_min, x_max, y_min, y_max)
    _draw_curves(canvas, model.curves, plot, x_min, x_max, y_min, y_max)
    _draw_patient_point(canvas, model, plot, x_min, x_max, y_min, y_max)
    _draw_axis_labels(canvas, model, plot, x_min, x_max, y_min, y_max)


def _fill_background(canvas: toga.Canvas, width: int, height: int) -> None:
    with canvas.fill(color="#FFFFFF"):
        canvas.round_rect(0, 0, width, height, 14)


def _draw_grid(
    canvas: toga.Canvas,
    plot: "_PlotArea",
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> None:
    grid_font = Font(SYSTEM, 9, weight=NORMAL)
    axis_font = Font(SYSTEM, 10, weight=BOLD)

    for index in range(5):
        ratio = index / 4
        y = plot.bottom - ratio * plot.height
        value = y_min + ratio * (y_max - y_min)
        with canvas.stroke(color="#E5E7EB", line_width=1):
            canvas.move_to(plot.left, y)
            canvas.line_to(plot.right, y)
        canvas.fill_style = COLOR_MUTED
        canvas.fill_text(f"{value:.0f}", 8, y + 3, font=grid_font)

    for tick in _x_ticks(x_min, x_max):
        x = plot.x(tick, x_min, x_max)
        with canvas.stroke(color="#F3F4F6", line_width=1):
            canvas.move_to(x, plot.top)
            canvas.line_to(x, plot.bottom)
        canvas.fill_style = COLOR_MUTED
        canvas.fill_text(_format_tick(tick), x - 9, plot.bottom + 18, font=grid_font)

    with canvas.stroke(color="#CBD5E1", line_width=1.4):
        canvas.move_to(plot.left, plot.top)
        canvas.line_to(plot.left, plot.bottom)
        canvas.line_to(plot.right, plot.bottom)

    canvas.fill_style = "#111827"
    canvas.fill_text("P", plot.right + 10, plot.top + 4, font=axis_font)


def _draw_curves(
    canvas: toga.Canvas,
    curves: tuple[OmsChartCurve, ...],
    plot: "_PlotArea",
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> None:
    label_font = Font(SYSTEM, 10, weight=BOLD)

    for curve in curves:
        points = tuple(
            point
            for point in curve.points
            if x_min <= point.x <= x_max
        )
        if len(points) < 2:
            continue

        with canvas.stroke(color=curve.color, line_width=2):
            first = points[0]
            canvas.move_to(plot.x(first.x, x_min, x_max), plot.y(first.y, y_min, y_max))
            for point in points[1:]:
                canvas.line_to(
                    plot.x(point.x, x_min, x_max),
                    plot.y(point.y, y_min, y_max),
                )

        last = _last_visible_point(points, x_min, x_max)
        if last is None:
            continue
        canvas.fill_style = curve.color
        canvas.fill_text(
            curve.label,
            plot.x(last.x, x_min, x_max) + 8,
            plot.y(last.y, y_min, y_max) + 4,
            font=label_font,
        )


def _draw_patient_point(
    canvas: toga.Canvas,
    model: OmsChartModel,
    plot: "_PlotArea",
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> None:
    point_x = plot.x(model.patient_x, x_min, x_max)
    point_y = plot.y(model.patient_y, y_min, y_max)
    label_font = Font(SYSTEM, 10, weight=BOLD)

    with canvas.fill(color="#111827"):
        canvas.arc(point_x, point_y, 5)

    canvas.fill_style = "#111827"
    canvas.fill_text(model.patient_label, point_x - 28, point_y - 12, font=label_font)


def _draw_axis_labels(
    canvas: toga.Canvas,
    model: OmsChartModel,
    plot: "_PlotArea",
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> None:
    axis_font = Font(SYSTEM, 10, weight=BOLD)
    canvas.fill_style = "#111827"
    canvas.fill_text(
        model.x_label,
        plot.left + (plot.width / 2) - 42,
        plot.bottom + 34,
        font=axis_font,
    )
    canvas.fill_text(
        model.y_label,
        plot.left,
        plot.y(y_max, y_min, y_max) - 12,
        font=axis_font,
    )


def _range_for_values(
    values: tuple[float, ...],
    pad_ratio: float,
) -> tuple[float, float]:
    min_value = min(values)
    max_value = max(values)
    span = max(max_value - min_value, 1)
    pad = span * pad_ratio
    return min_value - pad, max_value + pad


def _x_ticks(min_value: float, max_value: float) -> tuple[float, ...]:
    """Marcas del eje X ajustadas al rango visible."""

    span = max_value - min_value
    if span <= 6:
        step = 1.0
    elif span <= 12:
        step = 2.0
    elif span <= 24:
        step = 4.0
    else:
        step = 12.0

    ticks = []
    value = min_value
    while value <= max_value + 0.001:
        ticks.append(round(value, 1))
        value += step
    return tuple(ticks)


def _format_tick(value: float) -> str:
    """Formatea marcas evitando decimales innecesarios."""

    if abs(value - round(value)) < 0.01:
        return str(int(round(value)))
    return f"{value:.1f}"


def _last_visible_point(points: tuple, min_value: float, max_value: float):
    """Último punto visible de una curva, usado para ubicar la etiqueta."""

    for point in reversed(points):
        if min_value <= point.x <= max_value:
            return point
    return None


class _PlotArea:
    """Convierte coordenadas clínicas a coordenadas Canvas."""

    def __init__(self, width: int, height: int) -> None:
        self.left = CHART_PADDING_LEFT
        self.right = width - CHART_PADDING_RIGHT
        self.top = CHART_PADDING_TOP
        self.bottom = height - CHART_PADDING_BOTTOM
        self.width = max(self.right - self.left, 1)
        self.height = max(self.bottom - self.top, 1)

    def x(self, value: float, min_value: float, max_value: float) -> float:
        ratio = (value - min_value) / max(max_value - min_value, 1)
        return self.left + ratio * self.width

    def y(self, value: float, min_value: float, max_value: float) -> float:
        ratio = (value - min_value) / max(max_value - min_value, 1)
        return self.bottom - ratio * self.height
