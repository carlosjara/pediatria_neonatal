"""Vista para mostrar resultados de evaluación antropométrica."""

from collections.abc import Callable
from typing import Any

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from pediatria_neonatal.presentation.resultados import (
    ResultsSummaryGrid,
    semantic_color_for_classification,
)
from pediatria_neonatal.views.components import (
    SPACING_LG,
    SPACING_MD,
    SPACING_SM,
    SPACING_XS,
    age_display,
    alert_box,
    info_row,
    main_result_card,
    patient_summary_card,
    primary_button,
    results_summary_grid,
    scroll_screen,
    secondary_button,
    section_header,
    title,
    wrapped_text,
    zscore_chart,
)


class ResultadoView:
    """Presenta los resultados clínicos de forma clara y descansada."""

    def __init__(
        self,
        paciente_nombre: str,
        paciente_data: dict[str, Any],
        resultados: dict[str, Any],
        summary: ResultsSummaryGrid,
        on_new_measurement: Callable[[], None],
        on_back_to_patient: Callable[[], None],
    ) -> None:
        self.paciente_nombre = paciente_nombre
        self.paciente_data = paciente_data
        self.resultados = resultados
        self.summary = summary
        self.on_new_measurement = on_new_measurement
        self.on_back_to_patient = on_back_to_patient
        self.root: toga.Box | None = None
        self.selected_indicator_key: str | None = None

    def build(self) -> toga.Widget:
        """Construye el contenedor raíz de resultados."""
        self.root = toga.Box(style=Pack(direction=COLUMN, flex=1))
        self._render_summary()
        return self.root

    def _render_summary(self) -> None:
        """Muestra la pantalla de resumen de resultados."""
        children = [title("Resultados")]

        if "alertas" in self.resultados and self.resultados["alertas"]:
            children.append(self._build_alerts_section())

        children.append(main_result_card(self.summary.main_result))
        children.append(
            results_summary_grid(
                self.summary.indicators,
                self._show_indicator_detail,
            )
        )
        children.extend(
            [
                primary_button("Ver detalle completo", self._show_full_detail),
                secondary_button("← Volver al paciente", self._back_to_patient),
            ]
        )

        self._replace_content(children)

    def _render_detail(self) -> None:
        """Muestra la vista detallada actual con ajustes mínimos para móvil."""
        children = [title("Resultados")]
        children.append(secondary_button("Ver resumen", self._back_to_summary))

        children.append(self._build_patient_summary())

        if "edad_corregida" in self.resultados:
            children.append(self._build_age_section())

        children.append(self._build_measurements_section())

        if "oms2006" in self.resultados:
            children.append(self._build_detail_tabs_section())

        if "interpretacion" in self.resultados:
            children.append(self._build_interpretation_section())

        if "alertas" in self.resultados and self.resultados["alertas"]:
            children.append(self._build_alerts_section())

        children.extend(
            [
                toga.Box(style=Pack(height=SPACING_LG)),
                primary_button("Nueva medición", self._new_measurement),
                secondary_button("← Volver al resumen", self._back_to_summary),
                secondary_button("← Volver al paciente", self._back_to_patient),
            ]
        )

        self._replace_content(children)

    def _replace_content(self, children: list[toga.Widget]) -> None:
        """Reemplaza el contenido visible manteniendo el contenedor raíz."""
        content = toga.Box(
            children=children,
            style=Pack(
                direction=COLUMN,
                padding=SPACING_MD,
                flex=1,
            ),
        )

        assert self.root is not None
        self.root.clear()
        self.root.add(scroll_screen(content))

    def _build_patient_summary(self) -> toga.Box:
        """Construye la tarjeta resumen del paciente."""
        edad = self.resultados.get("edad_corregida", {})
        return patient_summary_card(
            nombre=self.paciente_nombre,
            edad_texto=edad.get("texto", ""),
            sexo=self.paciente_data.get("sexo", ""),
            es_prematuro=self.paciente_data.get("es_prematuro", False),
            semanas_eg=self.paciente_data.get("semanas_eg", 40),
            peso_nacer=self.paciente_data.get("peso_nacer_g", 0),
        )

    def _build_age_section(self) -> toga.Box:
        """Construye la sección de edad prominente."""
        edad = self.resultados["edad_corregida"]
        es_prematuro = self.paciente_data.get("es_prematuro", False)

        edad_cronologica = self._format_age_from_days(
            edad.get("edad_cronologica_dias", 0)
        )

        edad_corregida_dias = edad.get("edad_corregida_total_dias", 0)
        es_antes_de_termino = edad.get("es_antes_de_termino", False)

        if es_antes_de_termino or edad_corregida_dias < 0:
            edad_corregida_texto = "Aún no alcanza término"
        else:
            edad_corregida_texto = self._format_age_from_days(edad_corregida_dias)

        return age_display(
            edad_cronologica=edad_cronologica,
            edad_corregida=edad_corregida_texto,
            es_prematuro=es_prematuro,
        )

    def _build_measurements_section(self) -> toga.Box:
        """Construye la sección con los datos de medición actuales."""
        # Obtener datos de medición desde el estado o resultados
        medicion = self.resultados.get("medicion_actual", {})

        # Si no hay datos en resultados, intentar desde paciente_data
        if not medicion:
            medicion = {
                "peso_kg": self.paciente_data.get("peso_actual"),
                "talla_cm": self.paciente_data.get("talla_actual"),
                "perimetro_cefalico_cm": self.paciente_data.get(
                    "perimetro_cefalico_actual"
                ),
                "fecha_medicion": self.paciente_data.get("fecha_medicion"),
            }

        children = [section_header("Mediciones actuales", "Datos antropométricos")]

        # Peso
        if medicion.get("peso_kg"):
            children.append(info_row("Peso", f"{medicion['peso_kg']:.1f} kg"))

        # Talla
        if medicion.get("talla_cm"):
            children.append(info_row("Talla", f"{medicion['talla_cm']:.1f} cm"))

        # Perímetro cefálico
        if medicion.get("perimetro_cefalico_cm"):
            children.append(
                info_row(
                    "Perímetro cefálico", f"{medicion['perimetro_cefalico_cm']:.1f} cm"
                )
            )

        # Fecha de medición
        if medicion.get("fecha_medicion"):
            fecha = medicion["fecha_medicion"]
            if hasattr(fecha, "strftime"):
                fecha_str = fecha.strftime("%d/%m/%Y")
            else:
                fecha_str = str(fecha)
            children.append(info_row("Fecha", fecha_str))

        return toga.Box(
            children=children,
            style=Pack(direction=COLUMN),
        )

    def _build_detail_tabs_section(self) -> toga.Box:
        """Construye detalle técnico con pestañas ligeras para móvil."""

        oms = self.resultados.get("oms2006", {})
        indicadores = self._filtered_indicators(oms.get("indicadores", {}))
        interpretation_lines = []
        chart_children = []

        for item in indicadores.values():
            interpretation_lines.append(
                f"{item['nombre']}: {item['clasificacion']}. {item['interpretacion']}"
            )
            chart_children.append(self._build_zscore_chart(item))

        grafica_content = toga.Box(
            children=chart_children,
            style=Pack(direction=COLUMN),
        )
        grafica = scroll_screen(grafica_content)
        tabla = self._build_audit_table(indicadores)
        interpretacion = toga.Box(
            children=[
                wrapped_text("\n\n".join(interpretation_lines), height=260),
                toga.Box(style=Pack(height=SPACING_LG)),
            ],
            style=Pack(direction=COLUMN, padding=SPACING_MD),
        )

        tabs = toga.OptionContainer(
            content=[
                toga.OptionItem("Gráfica", grafica),
                toga.OptionItem("Tabla", tabla),
                toga.OptionItem("Interp.", interpretacion),
            ],
            style=Pack(height=430),
        )

        return toga.Box(
            children=[
                section_header(
                    self._detail_title("Detalle"),
                    "Auditoría técnica del cálculo",
                ),
                tabs,
            ],
            style=Pack(direction=COLUMN),
        )

    def _build_interpretation_section(self) -> toga.Box:
        """Construye la sección de interpretación clínica."""
        interp = self.resultados["interpretacion"]

        children = [
            section_header("Interpretación clínica", "Análisis del resultado"),
        ]

        if "resumen" in interp and interp["resumen"]:
            children.append(wrapped_text(interp["resumen"], height=70))

        if "recomendacion" in interp and interp["recomendacion"]:
            children.append(
                wrapped_text(
                    f"Recomendación: {interp['recomendacion']}",
                    height=90,
                )
            )

        return toga.Box(
            children=children,
            style=Pack(direction=COLUMN),
        )

    def _build_alerts_section(self) -> toga.Box:
        """Construye la sección de alertas."""
        children = [
            section_header("Alertas", "Puntos de atención"),
        ]

        for alerta in self.resultados["alertas"]:
            children.append(alert_box(alerta, severity="warning"))

        return toga.Box(
            children=children,
            style=Pack(direction=COLUMN),
        )

    def _format_age_from_days(self, total_days: int) -> str:
        """Formatea días totales a texto legible con abreviaturas y semanas."""
        if total_days < 0:
            return "Antes de término"

        if total_days < 30:
            return f"{total_days}D"

        months = total_days // 30
        days = total_days % 30

        # Calcular semanas
        weeks = total_days // 7
        remaining_days = total_days % 7

        if months < 12:
            if days > 0:
                return f"{months}M, {days}D ({weeks}S, {remaining_days}D)"
            return f"{months}M ({weeks}S)"

        years = months // 12
        remaining_months = months % 12

        if remaining_months > 0:
            return f"{years}a, {remaining_months}M"
        return f"{years}a"

    def _build_audit_table(
        self,
        indicadores: dict[str, dict[str, Any]],
    ) -> toga.ScrollContainer:
        """Construye una tabla visual de auditoría OMS."""

        rows = []
        for item in indicadores.values():
            rows.append(self._build_indicator_table(item))

        rows.append(toga.Box(style=Pack(height=SPACING_LG)))

        content = toga.Box(
            children=rows,
            style=Pack(
                direction=COLUMN,
                padding=SPACING_MD,
            ),
        )
        return scroll_screen(content)

    def _build_indicator_table(self, item: dict[str, Any]) -> toga.Box:
        """Construye una tabla campo/valor para un indicador."""

        audit = item.get("auditoria", {})
        rows = [
            self._table_row("Valor", f"{item['valor']:.2f} {item['unidad']}"),
            self._table_row("Z-score", f"{item['z_score']:+.2f} DE"),
            self._table_row("Percentil", item.get("percentil_texto", "")),
            self._table_row("Clasificación", item.get("clasificacion", "")),
            self._table_row("L", f"{audit.get('L'):.4f}"),
            self._table_row("M", f"{audit.get('M'):.4f}"),
            self._table_row("S", f"{audit.get('S'):.5f}"),
            self._table_row("Índice usado", str(audit.get("indice_usado", ""))),
            self._table_row("Método", str(audit.get("metodo", ""))),
            self._table_row("Fuente", str(audit.get("fuente", ""))),
            self._table_row("Versión", str(audit.get("version", ""))),
        ]

        return toga.Box(
            children=[
                toga.Label(
                    item.get("nombre", "Indicador OMS"),
                    style=Pack(
                        font_size=16,
                        font_weight="bold",
                        padding_bottom=SPACING_SM,
                    ),
                ),
                *rows,
            ],
            style=Pack(
                direction=COLUMN,
                padding_bottom=SPACING_LG,
            ),
        )

    def _table_row(self, label: str, value: str) -> toga.Box:
        """Fila visual de tabla para auditoría."""

        return toga.Box(
            children=[
                toga.Label(
                    label,
                    style=Pack(
                        font_size=12,
                        font_weight="bold",
                        padding_right=SPACING_SM,
                        width=112,
                    ),
                ),
                toga.Label(
                    value,
                    style=Pack(
                        font_size=12,
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

    def _build_zscore_chart(self, item: dict[str, Any]) -> toga.Box:
        """Construye una gráfica compacta de z-score para un indicador."""

        color = semantic_color_for_classification(
            str(item.get("clasificacion") or ""),
            str(item.get("severidad") or ""),
        )

        return zscore_chart(
            title_text=item.get("nombre", "Indicador OMS"),
            z_score=float(item.get("z_score") or 0),
            percentile_text=str(item.get("percentil_texto") or ""),
            classification=str(item.get("clasificacion") or ""),
            color=color,
        )

    def _filtered_indicators(
        self,
        indicadores: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        """Devuelve todos los indicadores o solo el seleccionado."""

        if self.selected_indicator_key is None:
            return indicadores

        item = indicadores.get(self.selected_indicator_key)
        if not item:
            return indicadores
        return {self.selected_indicator_key: item}

    def _detail_title(self, fallback: str) -> str:
        """Agrega el nombre del indicador cuando se abre desde una tarjeta."""

        if self.selected_indicator_key is None:
            return fallback

        for indicator in self.summary.indicators:
            if indicator.key == self.selected_indicator_key:
                return f"{fallback}: {indicator.label}"
        return fallback

    def _show_indicator_detail(self, key: str) -> None:
        """Abre el detalle filtrado para el indicador seleccionado."""

        self.selected_indicator_key = key
        self._render_detail()

    def _show_full_detail(self, widget: toga.Widget) -> None:
        """Abre la vista detallada general."""

        self.selected_indicator_key = None
        self._render_detail()

    def _back_to_summary(self, widget: toga.Widget) -> None:
        """Regresa al resumen de resultados."""

        self.selected_indicator_key = None
        self._render_summary()

    def _new_measurement(self, widget: toga.Widget) -> None:
        """Inicia una nueva medición."""
        self.on_new_measurement()

    def _back_to_patient(self, widget: toga.Widget) -> None:
        """Regresa a la pantalla de paciente."""
        self.on_back_to_patient()
