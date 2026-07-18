"""Controlador para capturar y validar mediciones antropométricas."""

from collections.abc import Callable
from typing import Any

import toga

from pediatria_neonatal.application.context import ServiceContext
from pediatria_neonatal.application.state import AppState
from pediatria_neonatal.domain.lms import IndicadorCrecimiento
from pediatria_neonatal.domain.paciente import MedicionAntropometrica
from pediatria_neonatal.services.oms2006 import PosicionMedicion, ResultadoIndicadorOMS
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
                raise ValueError("Ingrese al menos peso o talla para calcular.")

            peso_kg = float(peso_str) if peso_str else None
            talla_cm = float(talla_str) if talla_str else None
            perimetro_cm = float(perimetro_str) if perimetro_str else None

            medicion = MedicionAntropometrica(
                fecha_medicion=raw_data["fecha_medicion"],
                peso_kg=peso_kg,
                talla_cm=talla_cm,
                perimetro_cefalico_cm=perimetro_cm,
            )

            resultados = self._calculate_results(
                paciente,
                medicion,
                raw_data.get("posicion"),
            )

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
        posicion_medicion: str | None = None,
    ) -> dict[str, Any]:
        """Ejecuta los cálculos usando los servicios OMS 2006."""
        resultados: dict[str, Any] = {
            "alertas": [],
        }

        edad_corregida = self.services.neonatal.calcular_edad_corregida_paciente(
            paciente=paciente,
            fecha_medicion=medicion.fecha_medicion,
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
        resultados["edad_cronologica_texto"] = self._format_age_from_days(
            edad_corregida.edad_cronologica_dias
        )

        if paciente.es_prematuro:
            resultados["edad_corregida_texto"] = self._format_age_from_days(
                edad_corregida.edad_corregida_total_dias
            )
            resultados["clasificacion_prematuro"] = self._clasificar_prematuro(
                paciente.datos_neonatales.edad_gestacional_semanas
            )

        if edad_corregida.es_antes_de_termino:
            resultados["alertas"].append(
                "El paciente aún no alcanza la edad de término corregida."
            )

        posicion = PosicionMedicion.normalizar(
            posicion_medicion or "Acostado"
        )
        evaluacion = self.services.oms2006.evaluar(
            paciente=paciente,
            medicion=medicion,
            posicion=posicion,
            usar_edad_corregida=True,
        )
        resultados["oms2006"] = self._serializar_evaluacion_oms(evaluacion)
        resultados["alertas"].extend(evaluacion.alertas)
        resultados["medicion_actual"] = {
            "fecha_medicion": medicion.fecha_medicion,
            "peso_kg": medicion.peso_kg,
            "talla_cm": medicion.talla_cm,
            "perimetro_cefalico_cm": medicion.perimetro_cefalico_cm,
            "posicion": posicion.value,
            "talla_oms_cm": evaluacion.longitud_talla.valor_oms_cm
            if evaluacion.longitud_talla
            else medicion.talla_cm,
        }

        imc_oms = evaluacion.obtener(IndicadorCrecimiento.IMC_PARA_EDAD)
        if imc_oms is not None:
            resultados["imc"] = self._serializar_resultado_principal(imc_oms)
            resultados["interpretacion"] = {
                "resumen": imc_oms.interpretacion,
                "recomendacion": self._get_recommendation(resultados["imc"]),
            }

        return resultados

    def _serializar_evaluacion_oms(self, evaluacion: Any) -> dict[str, Any]:
        """Convierte la evaluación OMS a un diccionario apto para UI/historial."""

        return {
            "edad_cronologica_dias": evaluacion.edad_cronologica_dias,
            "edad_usada_dias": evaluacion.edad_usada_dias,
            "tipo_edad_usada": evaluacion.tipo_edad_usada,
            "motivo_edad_usada": evaluacion.motivo_edad_usada,
            "longitud_talla": {
                "valor_original_cm": evaluacion.longitud_talla.valor_original_cm,
                "valor_oms_cm": evaluacion.longitud_talla.valor_oms_cm,
                "posicion_original": evaluacion.longitud_talla.posicion_original.value,
                "ajuste_cm": evaluacion.longitud_talla.ajuste_cm,
                "descripcion_ajuste": evaluacion.longitud_talla.descripcion_ajuste,
            }
            if evaluacion.longitud_talla
            else None,
            "indicadores": {
                indicador.value: self._serializar_indicador(resultado)
                for indicador, resultado in evaluacion.resultados.items()
            },
            "alertas": list(evaluacion.alertas),
        }

    def _serializar_indicador(
        self,
        resultado: ResultadoIndicadorOMS,
    ) -> dict[str, Any]:
        """Convierte un indicador OMS completo a dict auditable."""

        auditoria = resultado.auditoria
        return {
            "indicador": resultado.indicador.value,
            "nombre": resultado.nombre,
            "valor": resultado.valor,
            "unidad": resultado.unidad,
            "z_score": resultado.z_score,
            "z_score_texto": resultado.z_score_texto,
            "percentil": resultado.percentil,
            "percentil_texto": resultado.percentil_texto,
            "clasificacion": resultado.clasificacion,
            "severidad": resultado.severidad,
            "interpretacion": resultado.interpretacion,
            "bandera_plausibilidad": resultado.bandera_plausibilidad,
            "auditoria": {
                "valor_observado": auditoria.valor_observado,
                "unidad": auditoria.unidad,
                "L": auditoria.parametros_lms["L"],
                "M": auditoria.parametros_lms["M"],
                "S": auditoria.parametros_lms["S"],
                "z_score_bruto": auditoria.z_score_bruto,
                "z_score": auditoria.z_score,
                "percentil": auditoria.percentil,
                "clasificacion": auditoria.clasificacion,
                "severidad": auditoria.severidad,
                "fuente": auditoria.fuente,
                "version": auditoria.version,
                "indice_solicitado": auditoria.indice_lms.indice_solicitado
                if auditoria.indice_lms
                else None,
                "indice_usado": auditoria.indice_lms.indice_usado
                if auditoria.indice_lms
                else None,
                "unidad_indice": auditoria.indice_lms.unidad_indice
                if auditoria.indice_lms
                else None,
                "metodo": auditoria.indice_lms.metodo if auditoria.indice_lms else None,
            },
        }

    def _serializar_resultado_principal(
        self,
        resultado: ResultadoIndicadorOMS,
    ) -> dict[str, Any]:
        """Adapta BMIFA a la estructura que ya consume ResultadoView."""

        return {
            "valor": resultado.valor,
            "clasificacion": resultado.clasificacion,
            "severidad": resultado.severidad,
            "descripcion": resultado.interpretacion,
            "percentil": resultado.percentil_texto,
            "percentil_valor": resultado.percentil,
            "z_score": resultado.z_score_texto,
            "z_score_valor": resultado.z_score,
            "auditoria": self._serializar_indicador(resultado)["auditoria"],
        }

    def _clasificar_prematuro(self, semanas_gestacion: int) -> str:
        """Clasifica prematuridad por semanas gestacionales."""

        if semanas_gestacion >= 37:
            return "Término"
        if semanas_gestacion >= 34:
            return "Prematuro tardío"
        if semanas_gestacion >= 32:
            return "Prematuro moderado"
        if semanas_gestacion >= 28:
            return "Prematuro muy precoz"
        return "Prematuro extremo"

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
