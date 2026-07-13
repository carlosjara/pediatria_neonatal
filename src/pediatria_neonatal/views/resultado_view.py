"""Vista para mostrar resultados de evaluación antropométrica."""

from collections.abc import Callable
from typing import Any

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from pediatria_neonatal.views.components import (
    SPACING_LG,
    SPACING_MD,
    SPACING_SM,
    age_display,
    alert_box,
    hero_value,
    info_row,
    patient_summary_card,
    primary_button,
    result_card,
    scroll_screen,
    secondary_button,
    section_header,
    title,
    wrapped_text,
)


class ResultadoView:
    """Presenta los resultados clínicos de forma clara y descansada."""

    def __init__(
        self,
        paciente_nombre: str,
        paciente_data: dict[str, Any],
        resultados: dict[str, Any],
        on_new_measurement: Callable[[], None],
        on_back_to_patient: Callable[[], None],
    ) -> None:
        self.paciente_nombre = paciente_nombre
        self.paciente_data = paciente_data
        self.resultados = resultados
        self.on_new_measurement = on_new_measurement
        self.on_back_to_patient = on_back_to_patient

    def build(self) -> toga.Widget:
        """Construye la interfaz de resultados."""
        children = [title("Resultados")]

        children.append(self._build_patient_summary())

        if "edad_corregida" in self.resultados:
            children.append(self._build_age_section())

        # Agregar sección de mediciones actuales
        children.append(self._build_measurements_section())

        if "imc" in self.resultados:
            children.append(self._build_imc_section())

        if "interpretacion" in self.resultados:
            children.append(self._build_interpretation_section())

        if "alertas" in self.resultados and self.resultados["alertas"]:
            children.append(self._build_alerts_section())

        children.extend([
            toga.Box(style=Pack(height=SPACING_LG)),
            primary_button("Nueva medición", self._new_measurement),
            secondary_button("← Volver al paciente", self._back_to_patient),
        ])

        content = toga.Box(
            children=children,
            style=Pack(
                direction=COLUMN,
                padding=SPACING_MD,
                flex=1,
            ),
        )

        return scroll_screen(content)

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
                "perimetro_cefalico_cm": self.paciente_data.get("perimetro_cefalico_actual"),
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
            children.append(info_row("Perímetro cefálico", f"{medicion['perimetro_cefalico_cm']:.1f} cm"))
        
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

    def _build_imc_section(self) -> toga.Box:
        """Construye la sección de IMC con resultados."""
        imc_data = self.resultados["imc"]

        children = [
            section_header("Índice de Masa Corporal", "Evaluación nutricional"),
            hero_value(f"{imc_data['valor']:.1f}", "kg/m²"),
            self._build_result_cards(imc_data),
        ]

        return toga.Box(
            children=children,
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
                toga.Box(
                    children=[
                        toga.Label(
                            f"📋 Recomendación: {interp['recomendacion']}",
                            style=Pack(
                                font_size=14,
                                padding_top=SPACING_SM,
                            ),
                        ),
                    ],
                    style=Pack(direction=COLUMN),
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

    def _build_result_cards(self, imc_data: dict) -> toga.Box:
        """Construye las tarjetas de resultados."""
        cards = []

        # Mostrar valor del IMC con 2 decimales
        if "valor" in imc_data:
            cards.append(
                result_card(
                    label="IMC",
                    value=f"{imc_data['valor']:.2f}",
                    severity="normal",
                )
            )

        if "clasificacion" in imc_data:
            severity = imc_data.get("severidad", "normal")
            cards.append(
                result_card(
                    label="Clasificación",
                    value=imc_data["clasificacion"],
                    detail=imc_data.get("descripcion", ""),
                    severity=severity,
                )
            )

        if "percentil" in imc_data:
            cards.append(
                result_card(
                    label="Percentil",
                    value=imc_data["percentil"],
                    severity="normal",
                )
            )

        if "z_score" in imc_data:
            cards.append(
                result_card(
                    label="Z-Score",
                    value=imc_data["z_score"],
                    severity="normal",
                )
            )

        return toga.Box(
            children=cards,
            style=Pack(
                direction=COLUMN,
                padding_top=SPACING_SM,
                padding_bottom=SPACING_SM,
            ),
        )

    def _new_measurement(self, widget: toga.Widget) -> None:
        """Inicia una nueva medición."""
        self.on_new_measurement()

    def _back_to_patient(self, widget: toga.Widget) -> None:
        """Regresa a la pantalla de paciente."""
        self.on_back_to_patient()
