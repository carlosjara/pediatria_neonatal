"""Evaluación e interpretación de indicadores de crecimiento infantil."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import StrEnum

from pediatria_neonatal.domain.exceptions import ErrorDatoAntropometrico

from pediatria_neonatal.domain.lms import (
    IndicadorCrecimiento,
    ReferenciaCrecimiento,
)

class NivelSeveridad(StrEnum):
    """Nivel de relevancia clínica de un resultado."""

    NORMAL = "normal"
    OBSERVACION = "observacion"
    MODERADA = "moderada"
    ALTA = "alta"
    NO_CLASIFICADO = "no_clasificado"


class ClasificacionCrecimiento(StrEnum):
    """Clasificaciones descriptivas de los indicadores de crecimiento."""

    ADECUADO = "adecuado"

    RIESGO_BAJO_PESO = "riesgo_bajo_peso"
    BAJO_PESO = "bajo_peso"
    BAJO_PESO_SEVERO = "bajo_peso_severo"

    RIESGO_DESNUTRICION_AGUDA = "riesgo_desnutricion_aguda"
    DESNUTRICION_AGUDA_MODERADA = "desnutricion_aguda_moderada"
    DESNUTRICION_AGUDA_SEVERA = "desnutricion_aguda_severa"

    RIESGO_SOBREPESO = "riesgo_sobrepeso"
    SOBREPESO = "sobrepeso"
    OBESIDAD = "obesidad"

    RIESGO_TALLA_BAJA = "riesgo_talla_baja"
    TALLA_BAJA = "talla_baja"
    TALLA_BAJA_SEVERA = "talla_baja_severa"

    PERIMETRO_CEFALICO_BAJO = "perimetro_cefalico_bajo"
    PERIMETRO_CEFALICO_ALTO = "perimetro_cefalico_alto"

    PEQUENO_EDAD_GESTACIONAL = "pequeno_edad_gestacional"
    ADECUADO_EDAD_GESTACIONAL = "adecuado_edad_gestacional"
    GRANDE_EDAD_GESTACIONAL = "grande_edad_gestacional"

    NO_CLASIFICADO = "no_clasificado"


@dataclass(frozen=True, slots=True)
class ResultadoIndicador:
    """Resultado clínico estructurado para un indicador de crecimiento.

    Attributes
    ----------
    indicador:
        Indicador antropométrico evaluado.

    valor:
        Valor medido o calculado, por ejemplo IMC, peso o talla.

    unidad:
        Unidad del valor: kg, cm, kg/m², porcentaje, entre otras.

    z_score:
        Número de desviaciones estándar respecto de la referencia.

    percentil:
        Percentil aproximado derivado del Z-score.

    clasificacion:
        Categoría clínica asignada por el motor de reglas.

    severidad:
        Nivel de atención sugerido por el resultado.

    interpretacion:
        Explicación textual destinada al profesional de salud.

    referencia:
        Estándar de crecimiento utilizado.

    alertas:
        Advertencias adicionales que debe conocer el profesional.
    """

    indicador: IndicadorCrecimiento
    valor: float
    unidad: str
    z_score: float | None
    percentil: float | None
    clasificacion: ClasificacionCrecimiento
    severidad: NivelSeveridad
    interpretacion: str
    referencia: ReferenciaCrecimiento
    alertas: tuple[str, ...] = field(default_factory=tuple)

    @property
    def desviaciones_estandar_texto(self) -> str:
        """Representa el Z-score con signo y dos posiciones decimales."""

        if self.z_score is None:
            return "No disponible"

        return f"{self.z_score:+.2f} DE"

    @property
    def percentil_texto(self) -> str:
        """Representa el percentil con formato clínico legible."""

        if self.percentil is None:
            return "No disponible"

        if self.percentil < 0.1:
            return "< P0.1"

        if self.percentil > 99.9:
            return "> P99.9"

        return f"P{self.percentil:.1f}"


@dataclass(frozen=True, slots=True)
class EvaluacionNutricional:
    """Agrupa todos los indicadores evaluados para una medición."""

    resultados: tuple[ResultadoIndicador, ...]
    resumen_general: str
    alertas_generales: tuple[str, ...] = field(default_factory=tuple)

    def obtener(
        self,
        indicador: IndicadorCrecimiento,
    ) -> ResultadoIndicador | None:
        """Busca el resultado correspondiente a un indicador."""

        for resultado in self.resultados:
            if resultado.indicador == indicador:
                return resultado

        return None

    @property
    def requiere_atencion(self) -> bool:
        """Indica si existe algún resultado de severidad moderada o alta."""

        severidades_relevantes = {
            NivelSeveridad.MODERADA,
            NivelSeveridad.ALTA,
        }

        return any(
            resultado.severidad in severidades_relevantes
            for resultado in self.resultados
        )


class EvaluadorCrecimiento:
    """Interpreta Z-scores según el indicador y la referencia utilizada."""

    def evaluar_z_score(
        self,
        *,
        indicador: IndicadorCrecimiento,
        valor: float,
        unidad: str,
        z_score: float,
        referencia: ReferenciaCrecimiento,
    ) -> ResultadoIndicador:
        """Convierte un Z-score en un resultado clínico explicativo.

        La interpretación depende del indicador. No se utiliza la misma regla
        para IMC-para-la-edad, peso-para-longitud, peso-para-la-edad o
        longitud-para-la-edad.

        Parameters
        ----------
        indicador:
            Indicador que se desea interpretar.

        valor:
            Valor medido o calculado.

        unidad:
            Unidad correspondiente al valor.

        z_score:
            Desviaciones estándar respecto de la población de referencia.

        referencia:
            Tabla o estándar que produjo el Z-score.

        Returns
        -------
        ResultadoIndicador
            Resultado estructurado con percentil, clasificación e
            interpretación.

        Raises
        ------
        ErrorDatoAntropometrico
            Si el valor o el Z-score no son números finitos.
        """

        valor_validado = self._validar_numero_finito(
            valor,
            nombre_campo="valor",
        )
        z_validado = self._validar_numero_finito(
            z_score,
            nombre_campo="z_score",
        )

        percentil = self.calcular_percentil_desde_z(z_validado)

        if indicador in {
            IndicadorCrecimiento.IMC_PARA_EDAD,
            IndicadorCrecimiento.PESO_PARA_LONGITUD,
            IndicadorCrecimiento.PESO_PARA_TALLA,
        }:
            return self._evaluar_adiposidad_o_emaciacion(
                indicador=indicador,
                valor=valor_validado,
                unidad=unidad,
                z_score=z_validado,
                percentil=percentil,
                referencia=referencia,
            )

        if indicador == IndicadorCrecimiento.PESO_PARA_EDAD:
            return self._evaluar_peso_para_edad(
                valor=valor_validado,
                unidad=unidad,
                z_score=z_validado,
                percentil=percentil,
                referencia=referencia,
            )

        if indicador in {
            IndicadorCrecimiento.LONGITUD_PARA_EDAD,
            IndicadorCrecimiento.TALLA_PARA_EDAD,
        }:
            return self._evaluar_longitud_o_talla_para_edad(
                indicador=indicador,
                valor=valor_validado,
                unidad=unidad,
                z_score=z_validado,
                percentil=percentil,
                referencia=referencia,
            )

        if indicador == IndicadorCrecimiento.PERIMETRO_CEFALICO_PARA_EDAD:
            return self._evaluar_perimetro_cefalico(
                valor=valor_validado,
                unidad=unidad,
                z_score=z_validado,
                percentil=percentil,
                referencia=referencia,
            )

        return ResultadoIndicador(
            indicador=indicador,
            valor=valor_validado,
            unidad=unidad,
            z_score=z_validado,
            percentil=percentil,
            clasificacion=ClasificacionCrecimiento.NO_CLASIFICADO,
            severidad=NivelSeveridad.NO_CLASIFICADO,
            interpretacion=(
                "El indicador fue calculado, pero aún no dispone de una "
                "regla clínica configurada para esta referencia."
            ),
            referencia=referencia,
            alertas=(
                "No interpretar el resultado como diagnóstico automático.",
            ),
        )

    @staticmethod
    def calcular_percentil_desde_z(z_score: float) -> float:
        """Convierte un Z-score al percentil de una distribución normal.

        Se utiliza la función de distribución acumulada normal estándar:

            percentil = Φ(z) × 100

        El resultado es una aproximación matemática. La tabla clínica original
        continúa siendo la fuente de referencia.
        """

        if not math.isfinite(z_score):
            raise ErrorDatoAntropometrico(
                "El Z-score debe ser un número finito."
            )

        percentil = (
            0.5
            * (
                1.0
                + math.erf(
                    z_score / math.sqrt(2.0),
                )
            )
            * 100.0
        )

        return percentil

    def construir_evaluacion(
        self,
        resultados: list[ResultadoIndicador],
    ) -> EvaluacionNutricional:
        """Construye el resumen general de varios indicadores."""

        if not resultados:
            raise ErrorDatoAntropometrico(
                "La evaluación debe contener al menos un indicador."
            )

        severidades = {
            resultado.severidad
            for resultado in resultados
        }

        alertas: list[str] = []

        if NivelSeveridad.ALTA in severidades:
            resumen = (
                "Se identificaron uno o más indicadores con alteración "
                "importante. Los resultados deben correlacionarse con la "
                "historia clínica, la técnica de medición y la evolución."
            )
            alertas.append(
                "Revisar los indicadores marcados con severidad alta."
            )
        elif NivelSeveridad.MODERADA in severidades:
            resumen = (
                "Se identificaron indicadores que requieren valoración "
                "clínica y seguimiento del crecimiento."
            )
        elif NivelSeveridad.OBSERVACION in severidades:
            resumen = (
                "El crecimiento presenta uno o más resultados limítrofes. "
                "Se recomienda revisar la tendencia longitudinal."
            )
        else:
            resumen = (
                "Los indicadores evaluados se encuentran dentro de los "
                "rangos esperados para la referencia seleccionada."
            )

        referencias = {
            resultado.referencia
            for resultado in resultados
        }

        if len(referencias) > 1:
            alertas.append(
                "La evaluación combina más de una referencia de crecimiento."
            )

        return EvaluacionNutricional(
            resultados=tuple(resultados),
            resumen_general=resumen,
            alertas_generales=tuple(alertas),
        )

    def _evaluar_adiposidad_o_emaciacion(
        self,
        *,
        indicador: IndicadorCrecimiento,
        valor: float,
        unidad: str,
        z_score: float,
        percentil: float,
        referencia: ReferenciaCrecimiento,
    ) -> ResultadoIndicador:
        """Interpreta IMC/edad y peso/longitud o peso/talla."""

        if z_score < -3:
            clasificacion = (
                ClasificacionCrecimiento.DESNUTRICION_AGUDA_SEVERA
            )
            severidad = NivelSeveridad.ALTA
            interpretacion = (
                "El indicador se encuentra por debajo de -3 desviaciones "
                "estándar, compatible con una alteración antropométrica "
                "severa. Debe confirmarse la medición y realizar valoración "
                "clínica integral."
            )
        elif z_score < -2:
            clasificacion = (
                ClasificacionCrecimiento.DESNUTRICION_AGUDA_MODERADA
            )
            severidad = NivelSeveridad.MODERADA
            interpretacion = (
                "El indicador se encuentra entre -3 y -2 desviaciones "
                "estándar, compatible con déficit antropométrico."
            )
        elif z_score < -1:
            clasificacion = (
                ClasificacionCrecimiento.RIESGO_DESNUTRICION_AGUDA
            )
            severidad = NivelSeveridad.OBSERVACION
            interpretacion = (
                "El indicador se encuentra entre -2 y -1 desviaciones "
                "estándar. No confirma desnutrición, pero merece seguimiento "
                "de la trayectoria de crecimiento."
            )
        elif z_score <= 1:
            clasificacion = ClasificacionCrecimiento.ADECUADO
            severidad = NivelSeveridad.NORMAL
            interpretacion = (
                "El indicador se encuentra dentro del rango esperado para "
                "la referencia seleccionada."
            )
        elif z_score <= 2:
            clasificacion = ClasificacionCrecimiento.RIESGO_SOBREPESO
            severidad = NivelSeveridad.OBSERVACION
            interpretacion = (
                "El indicador se encuentra por encima de +1 y hasta +2 "
                "desviaciones estándar. Requiere seguimiento de la tendencia "
                "de crecimiento y del contexto clínico."
            )
        elif z_score <= 3:
            clasificacion = ClasificacionCrecimiento.SOBREPESO
            severidad = NivelSeveridad.MODERADA
            interpretacion = (
                "El indicador se encuentra por encima de +2 y hasta +3 "
                "desviaciones estándar, compatible con exceso de peso para "
                "la referencia utilizada."
            )
        else:
            clasificacion = ClasificacionCrecimiento.OBESIDAD
            severidad = NivelSeveridad.ALTA
            interpretacion = (
                "El indicador se encuentra por encima de +3 desviaciones "
                "estándar, compatible con obesidad según la referencia "
                "seleccionada."
            )

        return ResultadoIndicador(
            indicador=indicador,
            valor=valor,
            unidad=unidad,
            z_score=z_score,
            percentil=percentil,
            clasificacion=clasificacion,
            severidad=severidad,
            interpretacion=interpretacion,
            referencia=referencia,
        )

    def _evaluar_peso_para_edad(
        self,
        *,
        valor: float,
        unidad: str,
        z_score: float,
        percentil: float,
        referencia: ReferenciaCrecimiento,
    ) -> ResultadoIndicador:
        """Interpreta peso para la edad sin diagnosticar exceso de peso."""

        alertas: tuple[str, ...] = ()

        if z_score < -3:
            clasificacion = ClasificacionCrecimiento.BAJO_PESO_SEVERO
            severidad = NivelSeveridad.ALTA
            interpretacion = (
                "Peso para la edad inferior a -3 desviaciones estándar."
            )
        elif z_score < -2:
            clasificacion = ClasificacionCrecimiento.BAJO_PESO
            severidad = NivelSeveridad.MODERADA
            interpretacion = (
                "Peso para la edad entre -3 y -2 desviaciones estándar."
            )
        elif z_score < -1:
            clasificacion = ClasificacionCrecimiento.RIESGO_BAJO_PESO
            severidad = NivelSeveridad.OBSERVACION
            interpretacion = (
                "Peso para la edad entre -2 y -1 desviaciones estándar. "
                "Conviene revisar la evolución longitudinal."
            )
        else:
            clasificacion = ClasificacionCrecimiento.ADECUADO
            severidad = NivelSeveridad.NORMAL
            interpretacion = (
                "Peso para la edad sin evidencia de bajo peso según el "
                "punto de corte configurado."
            )

            if z_score > 2:
                alertas = (
                    "Peso para la edad elevado no diagnostica sobrepeso. "
                    "Debe evaluarse IMC/edad o peso/longitud-talla.",
                )

        return ResultadoIndicador(
            indicador=IndicadorCrecimiento.PESO_PARA_EDAD,
            valor=valor,
            unidad=unidad,
            z_score=z_score,
            percentil=percentil,
            clasificacion=clasificacion,
            severidad=severidad,
            interpretacion=interpretacion,
            referencia=referencia,
            alertas=alertas,
        )

    def _evaluar_longitud_o_talla_para_edad(
        self,
        *,
        indicador: IndicadorCrecimiento,
        valor: float,
        unidad: str,
        z_score: float,
        percentil: float,
        referencia: ReferenciaCrecimiento,
    ) -> ResultadoIndicador:
        """Interpreta longitud o talla para la edad."""

        if z_score < -3:
            clasificacion = ClasificacionCrecimiento.TALLA_BAJA_SEVERA
            severidad = NivelSeveridad.ALTA
            interpretacion = (
                "Longitud o talla para la edad inferior a -3 desviaciones "
                "estándar."
            )
        elif z_score < -2:
            clasificacion = ClasificacionCrecimiento.TALLA_BAJA
            severidad = NivelSeveridad.MODERADA
            interpretacion = (
                "Longitud o talla para la edad entre -3 y -2 desviaciones "
                "estándar."
            )
        elif z_score < -1:
            clasificacion = ClasificacionCrecimiento.RIESGO_TALLA_BAJA
            severidad = NivelSeveridad.OBSERVACION
            interpretacion = (
                "Longitud o talla para la edad entre -2 y -1 desviaciones "
                "estándar. Se recomienda seguimiento longitudinal."
            )
        else:
            clasificacion = ClasificacionCrecimiento.ADECUADO
            severidad = NivelSeveridad.NORMAL
            interpretacion = (
                "Longitud o talla para la edad dentro del rango esperado."
            )

        return ResultadoIndicador(
            indicador=indicador,
            valor=valor,
            unidad=unidad,
            z_score=z_score,
            percentil=percentil,
            clasificacion=clasificacion,
            severidad=severidad,
            interpretacion=interpretacion,
            referencia=referencia,
        )

    def _evaluar_perimetro_cefalico(
        self,
        *,
        valor: float,
        unidad: str,
        z_score: float,
        percentil: float,
        referencia: ReferenciaCrecimiento,
    ) -> ResultadoIndicador:
        """Interpreta el perímetro cefálico para la edad."""

        if z_score < -2:
            clasificacion = (
                ClasificacionCrecimiento.PERIMETRO_CEFALICO_BAJO
            )
            severidad = (
                NivelSeveridad.ALTA
                if z_score < -3
                else NivelSeveridad.MODERADA
            )
            interpretacion = (
                "Perímetro cefálico inferior a -2 desviaciones estándar. "
                "Debe confirmarse la técnica de medición y correlacionarse "
                "con la historia clínica."
            )
        elif z_score > 2:
            clasificacion = (
                ClasificacionCrecimiento.PERIMETRO_CEFALICO_ALTO
            )
            severidad = (
                NivelSeveridad.ALTA
                if z_score > 3
                else NivelSeveridad.MODERADA
            )
            interpretacion = (
                "Perímetro cefálico superior a +2 desviaciones estándar. "
                "Debe confirmarse la medición y evaluar la trayectoria."
            )
        else:
            clasificacion = ClasificacionCrecimiento.ADECUADO
            severidad = NivelSeveridad.NORMAL
            interpretacion = (
                "Perímetro cefálico dentro del rango esperado para la "
                "referencia seleccionada."
            )

        return ResultadoIndicador(
            indicador=(
                IndicadorCrecimiento.PERIMETRO_CEFALICO_PARA_EDAD
            ),
            valor=valor,
            unidad=unidad,
            z_score=z_score,
            percentil=percentil,
            clasificacion=clasificacion,
            severidad=severidad,
            interpretacion=interpretacion,
            referencia=referencia,
        )

    @staticmethod
    def _validar_numero_finito(
        valor: float,
        *,
        nombre_campo: str,
    ) -> float:
        """Valida y convierte un valor numérico finito."""

        if isinstance(valor, bool):
            raise ErrorDatoAntropometrico(
                f"{nombre_campo} debe ser un número real."
            )

        try:
            numero = float(valor)
        except (TypeError, ValueError) as exc:
            raise ErrorDatoAntropometrico(
                f"{nombre_campo} debe ser un número real."
            ) from exc

        if not math.isfinite(numero):
            raise ErrorDatoAntropometrico(
                f"{nombre_campo} debe ser un número finito."
            )

        return numero