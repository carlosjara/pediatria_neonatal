"""Controlador para capturar y validar mediciones antropométricas."""

from collections.abc import Callable
from typing import Any

import toga

from pediatria_neonatal.application.context import ServiceContext
from pediatria_neonatal.application.state import AppState
from pediatria_neonatal.domain.paciente import MedicionAntropometrica
from pediatria_neonatal.views.medicion_view import MedicionView


class MedicionController:
    """Coordina la captura de mediciones y el cálculo de resultados."""

    def __init__(
        self,
        state: AppState,
        services: ServiceContext,
        on_results_ready: Callable[[], None],
        on_back: Callable[[], None],
        on_calcular_edad: Callable[[], None] | None = None,
    ) -> None:
        self.state = state
        self.services = services
        self.on_results_ready = on_results_ready
        self.on_back = on_back
        self.on_calcular_edad = on_calcular_edad
        self.view: MedicionView | None = None

    def build_view(self) -> toga.Widget:
        """Construye la vista de medición con datos del paciente actual."""
        paciente = self.state.paciente_actual

        if paciente is None:
            raise ValueError("No hay paciente seleccionado")

        paciente_info = self._build_patient_info(paciente)

        self.view = MedicionView(
            paciente_nombre=paciente.nombre,
            paciente_info=paciente_info,
            on_calculate=self.calculate,
            on_back=self.on_back,
            on_calcular_edad=self.calcular_edad_corregida,
        )

        return self.view.build()

    def calculate(self, raw_data: dict[str, Any]) -> None:
        """Valida los datos y calcula los resultados antropométricos."""
        assert self.view is not None

        paciente = self.state.paciente_actual
        if paciente is None:
            self.view.show_error("No hay paciente seleccionado")
            return

        try:
            peso_str = str(raw_data.get("peso_kg") or "").strip()
            talla_str = str(raw_data.get("talla_cm") or "").strip()
            perimetro_str = str(raw_data.get("perimetro_cefalico_cm") or "").strip()

            if not peso_str and not talla_str:
                raise ValueError(
                    "Ingrese al menos peso o talla para calcular."
                )

            peso_kg = float(peso_str) if peso_str else None
            talla_cm = float(talla_str) if talla_str else None
            perimetro_cm = float(perimetro_str) if perimetro_str else None

            medicion = MedicionAntropometrica(
                fecha_medicion=raw_data["fecha_medicion"],
                peso_kg=peso_kg,
                talla_cm=talla_cm,
                perimetro_cefalico_cm=perimetro_cm,
            )

            resultados = self._calculate_results(paciente, medicion)

            self.state.medicion_actual = medicion
            self.state.resultados_actuales = resultados
            self.state.guardar_en_historial()

            self.on_results_ready()

        except ValueError as error:
            self.view.show_error(str(error))

    def _calculate_results(
        self,
        paciente: Any,
        medicion: MedicionAntropometrica,
    ) -> dict[str, Any]:
        """Ejecuta los cálculos usando los servicios."""
        resultados: dict[str, Any] = {
            "alertas": [],
        }

        edad_corregida = self.services.neonatal.calcular_edad_corregida_paciente(
            paciente=paciente,
            fecha_medicion=medicion.fecha_medicion,
        )

        # Formatear edad cronológica con abreviaturas
        edad_cronologica_texto = self._format_age_from_days(
            edad_corregida.edad_cronologica_dias
        )

        resultados["edad_corregida"] = {
            "texto": edad_corregida.texto,
            "semanas": edad_corregida.semanas,
            "dias": edad_corregida.dias,
            "meses": edad_corregida.meses,
            "edad_cronologica_dias": edad_corregida.edad_cronologica_dias,
            "edad_corregida_total_dias": edad_corregida.edad_corregida_total_dias,
            "es_prematuro": paciente.es_prematuro,
            "es_antes_de_termino": edad_corregida.es_antes_de_termino,
        }
        
        # Agregar edad cronológica formateada para el historial
        resultados["edad_cronologica_texto"] = edad_cronologica_texto
        
        # También agregar edad corregida formateada para el historial
        if paciente.es_prematuro:
            resultados["edad_corregida_texto"] = self._format_age_from_days(
                edad_corregida.edad_corregida_total_dias
            )

        if edad_corregida.es_antes_de_termino:
            resultados["alertas"].append(
                "El paciente aún no alcanza la edad de término corregida."
            )

        if medicion.peso_kg is not None and medicion.talla_cm is not None:
            imc = self.services.antropometria.calcular_imc(
                peso_kg=medicion.peso_kg,
                talla_cm=medicion.talla_cm,
            )

            imc_result = self._interpret_imc(imc, edad_corregida.meses)
            resultados["imc"] = imc_result

            resultados["interpretacion"] = {
                "resumen": imc_result.get("descripcion", ""),
                "recomendacion": self._get_recommendation(imc_result),
            }

        return resultados

    def _interpret_imc(self, imc: float, edad_meses: int) -> dict[str, Any]:
        """Interpreta el IMC según la edad."""
        if imc < 14:
            clasificacion = "Bajo peso"
            severidad = "moderada"
            descripcion = (
                "El IMC se encuentra por debajo del rango esperado. "
                "Se recomienda evaluación nutricional."
            )
        elif imc < 17:
            clasificacion = "Normal bajo"
            severidad = "observacion"
            descripcion = (
                "El IMC está en el límite inferior del rango normal. "
                "Mantener seguimiento."
            )
        elif imc < 25:
            clasificacion = "Normal"
            severidad = "normal"
            descripcion = (
                "El IMC se encuentra dentro del rango esperado "
                "para la edad del paciente."
            )
        elif imc < 30:
            clasificacion = "Sobrepeso"
            severidad = "observacion"
            descripcion = (
                "El IMC indica sobrepeso. "
                "Se recomienda evaluación de hábitos alimenticios."
            )
        else:
            clasificacion = "Obesidad"
            severidad = "alta"
            descripcion = (
                "El IMC indica obesidad. "
                "Se requiere intervención nutricional."
            )

        return {
            "valor": imc,
            "clasificacion": clasificacion,
            "severidad": severidad,
            "descripcion": descripcion,
            "percentil": self._estimate_percentile(imc),
            "z_score": self._estimate_zscore(imc),
        }

    def _estimate_percentile(self, imc: float) -> str:
        """Estima el percentil basado en el IMC (simplificado)."""
        if imc < 14:
            return "< P5"
        elif imc < 17:
            return "P5 - P25"
        elif imc < 22:
            return "P25 - P75"
        elif imc < 25:
            return "P75 - P85"
        elif imc < 30:
            return "P85 - P95"
        else:
            return "> P95"

    def _estimate_zscore(self, imc: float) -> str:
        """Estima el Z-score basado en el IMC (simplificado)."""
        if imc < 14:
            return "< -2 DE"
        elif imc < 17:
            return "-2 a -1 DE"
        elif imc < 25:
            return "-1 a +1 DE"
        elif imc < 30:
            return "+1 a +2 DE"
        else:
            return "> +2 DE"

    def _get_recommendation(self, imc_result: dict) -> str:
        """Genera recomendación basada en la clasificación."""
        severity = imc_result.get("severidad", "normal")

        recommendations = {
            "normal": "Continuar con controles de rutina.",
            "observacion": "Programar seguimiento en 1-2 meses.",
            "moderada": "Referir a nutrición para evaluación.",
            "alta": "Requiere intervención inmediata.",
        }

        return recommendations.get(severity, "Consultar con especialista.")

    def _build_patient_info(self, paciente: Any) -> str:
        """Construye información resumida del paciente."""
        datos = paciente.datos_neonatales
        info_parts = [
            f"Sexo: {paciente.sexo.value}",
            f"EG: {datos.edad_gestacional_semanas}+{datos.edad_gestacional_dias}",
        ]

        if paciente.es_prematuro:
            info_parts.append("Prematuro")

        return " | ".join(info_parts)

    def calcular_edad_corregida(self) -> None:
        """Calcula y muestra la edad corregida para la fecha actual."""
        try:
            paciente = self.state.paciente_actual
            if paciente is None:
                raise ValueError("No hay paciente seleccionado")

            # Usar la fecha del input de medición
            assert self.view is not None
            fecha_medicion = self.view.fecha_input.value

            # Calcular edad corregida usando el servicio existente
            edad_corregida = self.services.neonatal.calcular_edad_corregida_paciente(
                paciente=paciente,
                fecha_medicion=fecha_medicion,
            )

            # Formatear edades con el método existente
            edad_cronologica_texto = self._format_age_from_days(
                edad_corregida.edad_cronologica_dias
            )
            
            edad_corregida_texto = self._format_age_from_days(
                edad_corregida.edad_corregida_total_dias
            )

            resultado = {
                "edad_cronologica_texto": edad_cronologica_texto,
                "edad_corregida_texto": edad_corregida_texto,
                "es_prematuro": paciente.es_prematuro,
                "edad_cronologica_dias": edad_corregida.edad_cronologica_dias,
                "edad_corregida_total_dias": edad_corregida.edad_corregida_total_dias,
            }

            if self.view:
                self.view.show_edad_corregida(resultado)

        except Exception as error:
            if self.view:
                self.view.show_error(f"Error al calcular edad: {error}")

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
