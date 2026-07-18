"""Evaluación antropométrica OMS 2006 para menores de cinco años."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from pediatria_neonatal.clinical.evaluacion import (
    ClasificacionCrecimiento,
    EvaluadorCrecimiento,
)
from pediatria_neonatal.data.lms_repository import LMSAudit, LMSRepository
from pediatria_neonatal.domain.exceptions import ErrorDatoAntropometrico
from pediatria_neonatal.domain.lms import IndicadorCrecimiento, ReferenciaCrecimiento
from pediatria_neonatal.domain.paciente import MedicionAntropometrica, Paciente
from pediatria_neonatal.services.antropometria import CalculadoraAntropometrica
from pediatria_neonatal.services.neonatal import CalculadoraNeonatal
from pediatria_neonatal.services.zscore import CalculadoraZScore


class PosicionMedicion(StrEnum):
    """Posición en la que se midió longitud/talla."""

    ACOSTADO = "acostado"
    DE_PIE = "de_pie"

    @classmethod
    def normalizar(cls, valor: str | "PosicionMedicion") -> "PosicionMedicion":
        if isinstance(valor, cls):
            return valor

        normalizado = str(valor).strip().lower().replace(" ", "_")
        aliases = {
            "acostado": cls.ACOSTADO,
            "recumbente": cls.ACOSTADO,
            "longitud": cls.ACOSTADO,
            "de_pie": cls.DE_PIE,
            "depie": cls.DE_PIE,
            "talla": cls.DE_PIE,
            "parado": cls.DE_PIE,
        }
        try:
            return aliases[normalizado]
        except KeyError as exc:
            raise ErrorDatoAntropometrico(
                "La posición debe ser acostado/recumbente o de pie."
            ) from exc


@dataclass(frozen=True, slots=True)
class MedidaLongitudTalla:
    """Medida normalizada según las reglas OMS de posición."""

    valor_original_cm: float
    valor_oms_cm: float
    posicion_original: PosicionMedicion
    indicador_edad: IndicadorCrecimiento
    indicador_peso: IndicadorCrecimiento
    ajuste_cm: float
    descripcion_ajuste: str


@dataclass(frozen=True, slots=True)
class AuditoriaIndicadorOMS:
    """Auditoría técnica de un indicador OMS calculado."""

    valor_observado: float
    unidad: str
    parametros_lms: dict[str, Any]
    z_score_bruto: float
    z_score: float
    percentil: float
    clasificacion: str
    severidad: str
    fuente: str
    version: str
    bandera_plausibilidad: str | None = None
    indice_lms: LMSAudit | None = None


@dataclass(frozen=True, slots=True)
class ResultadoIndicadorOMS:
    """Resultado completo para un indicador antropométrico OMS."""

    indicador: IndicadorCrecimiento
    nombre: str
    valor: float
    unidad: str
    z_score: float
    percentil: float
    clasificacion: str
    severidad: str
    interpretacion: str
    bandera_plausibilidad: str | None
    auditoria: AuditoriaIndicadorOMS

    @property
    def z_score_texto(self) -> str:
        return f"{self.z_score:+.2f} DE"

    @property
    def percentil_texto(self) -> str:
        if self.percentil < 0.1:
            return "< P0.1"
        if self.percentil > 99.9:
            return "> P99.9"
        return f"P{self.percentil:.1f}"


@dataclass(frozen=True, slots=True)
class EvaluacionOMS2006:
    """Evaluación OMS 2006 de una medición antropométrica."""

    edad_cronologica_dias: int
    edad_usada_dias: int
    tipo_edad_usada: str
    motivo_edad_usada: str
    longitud_talla: MedidaLongitudTalla | None
    resultados: dict[IndicadorCrecimiento, ResultadoIndicadorOMS]
    alertas: tuple[str, ...] = field(default_factory=tuple)

    def obtener(
        self,
        indicador: IndicadorCrecimiento,
    ) -> ResultadoIndicadorOMS | None:
        return self.resultados.get(indicador)


class EvaluadorOMS2006:
    """Calcula e interpreta indicadores OMS 2006 con tablas LMS oficiales."""

    LIMITE_EDAD_DIAS = 1856
    DIAS_24_MESES = 731

    _PLAUSIBILIDAD = {
        IndicadorCrecimiento.PESO_PARA_EDAD: (-6.0, 5.0),
        IndicadorCrecimiento.LONGITUD_PARA_EDAD: (-6.0, 6.0),
        IndicadorCrecimiento.TALLA_PARA_EDAD: (-6.0, 6.0),
        IndicadorCrecimiento.PESO_PARA_LONGITUD: (-5.0, 5.0),
        IndicadorCrecimiento.PESO_PARA_TALLA: (-5.0, 5.0),
        IndicadorCrecimiento.IMC_PARA_EDAD: (-5.0, 5.0),
        IndicadorCrecimiento.PERIMETRO_CEFALICO_PARA_EDAD: (-5.0, 5.0),
    }

    _NOMBRES = {
        IndicadorCrecimiento.PESO_PARA_EDAD: "Peso para la edad",
        IndicadorCrecimiento.LONGITUD_PARA_EDAD: "Longitud para la edad",
        IndicadorCrecimiento.TALLA_PARA_EDAD: "Talla para la edad",
        IndicadorCrecimiento.PESO_PARA_LONGITUD: "Peso para longitud",
        IndicadorCrecimiento.PESO_PARA_TALLA: "Peso para talla",
        IndicadorCrecimiento.IMC_PARA_EDAD: "IMC para la edad",
        IndicadorCrecimiento.PERIMETRO_CEFALICO_PARA_EDAD: (
            "Perímetro cefálico para la edad"
        ),
    }

    def __init__(
        self,
        *,
        repository: LMSRepository | None = None,
        neonatal: CalculadoraNeonatal | None = None,
        antropometria: CalculadoraAntropometrica | None = None,
        zscore: CalculadoraZScore | None = None,
        evaluador: EvaluadorCrecimiento | None = None,
    ) -> None:
        self.repository = repository or LMSRepository()
        self.neonatal = neonatal or CalculadoraNeonatal()
        self.antropometria = antropometria or CalculadoraAntropometrica()
        self.zscore = zscore or CalculadoraZScore()
        self.evaluador = evaluador or EvaluadorCrecimiento()

    def evaluar(
        self,
        *,
        paciente: Paciente,
        medicion: MedicionAntropometrica,
        posicion: PosicionMedicion | str = PosicionMedicion.ACOSTADO,
        usar_edad_corregida: bool = True,
    ) -> EvaluacionOMS2006:
        """Evalúa los cinco indicadores OMS 2006 solicitados."""

        edad_neonatal = self.neonatal.calcular_edad_corregida_paciente(
            paciente=paciente,
            fecha_medicion=medicion.fecha_medicion,
        )
        edad_usada, tipo_edad, motivo = self._seleccionar_edad(
            paciente=paciente,
            edad_cronologica_dias=edad_neonatal.edad_cronologica_dias,
            edad_corregida_dias=edad_neonatal.edad_corregida_total_dias,
            usar_edad_corregida=usar_edad_corregida,
        )

        if edad_usada > self.LIMITE_EDAD_DIAS:
            raise ErrorDatoAntropometrico(
                "OMS 2006 aplica hasta menores de cinco años."
            )

        resultados: dict[IndicadorCrecimiento, ResultadoIndicadorOMS] = {}
        alertas: list[str] = []

        medida_normalizada: MedidaLongitudTalla | None = None
        if medicion.talla_cm is not None:
            medida_normalizada = self.normalizar_longitud_talla(
                edad_dias=edad_usada,
                medida_cm=medicion.talla_cm,
                posicion=posicion,
            )
            if medida_normalizada.ajuste_cm != 0:
                alertas.append(medida_normalizada.descripcion_ajuste)

            resultados[medida_normalizada.indicador_edad] = self._evaluar_por_edad(
                indicador=medida_normalizada.indicador_edad,
                valor=medida_normalizada.valor_oms_cm,
                unidad="cm",
                paciente=paciente,
                edad_dias=edad_usada,
            )

        if medicion.peso_kg is not None:
            resultados[IndicadorCrecimiento.PESO_PARA_EDAD] = self._evaluar_por_edad(
                indicador=IndicadorCrecimiento.PESO_PARA_EDAD,
                valor=medicion.peso_kg,
                unidad="kg",
                paciente=paciente,
                edad_dias=edad_usada,
            )

        if medicion.peso_kg is not None and medicion.talla_cm is not None:
            assert medida_normalizada is not None
            imc = self.antropometria.calcular_imc(
                peso_kg=medicion.peso_kg,
                talla_cm=medida_normalizada.valor_oms_cm,
            )
            resultados[IndicadorCrecimiento.IMC_PARA_EDAD] = self._evaluar_por_edad(
                indicador=IndicadorCrecimiento.IMC_PARA_EDAD,
                valor=imc,
                unidad="kg/m²",
                paciente=paciente,
                edad_dias=edad_usada,
            )
            resultados[medida_normalizada.indicador_peso] = self._evaluar_por_medida(
                indicador=medida_normalizada.indicador_peso,
                valor=medicion.peso_kg,
                unidad="kg",
                paciente=paciente,
                medida_cm=medida_normalizada.valor_oms_cm,
            )

        if medicion.perimetro_cefalico_cm is not None:
            resultados[IndicadorCrecimiento.PERIMETRO_CEFALICO_PARA_EDAD] = (
                self._evaluar_por_edad(
                    indicador=IndicadorCrecimiento.PERIMETRO_CEFALICO_PARA_EDAD,
                    valor=medicion.perimetro_cefalico_cm,
                    unidad="cm",
                    paciente=paciente,
                    edad_dias=edad_usada,
                )
            )

        for resultado in resultados.values():
            if resultado.bandera_plausibilidad:
                alertas.append(resultado.bandera_plausibilidad)

        return EvaluacionOMS2006(
            edad_cronologica_dias=edad_neonatal.edad_cronologica_dias,
            edad_usada_dias=edad_usada,
            tipo_edad_usada=tipo_edad,
            motivo_edad_usada=motivo,
            longitud_talla=medida_normalizada,
            resultados=resultados,
            alertas=tuple(dict.fromkeys(alertas)),
        )

    def normalizar_longitud_talla(
        self,
        *,
        edad_dias: int,
        medida_cm: float,
        posicion: PosicionMedicion | str,
    ) -> MedidaLongitudTalla:
        """Aplica la regla OMS de 0.7 cm para longitud/talla."""

        posicion_normalizada = PosicionMedicion.normalizar(posicion)
        valor = float(medida_cm)
        if valor <= 0:
            raise ErrorDatoAntropometrico("La longitud/talla debe ser positiva.")

        if edad_dias < self.DIAS_24_MESES:
            if posicion_normalizada == PosicionMedicion.DE_PIE:
                return MedidaLongitudTalla(
                    valor_original_cm=valor,
                    valor_oms_cm=valor + 0.7,
                    posicion_original=posicion_normalizada,
                    indicador_edad=IndicadorCrecimiento.LONGITUD_PARA_EDAD,
                    indicador_peso=IndicadorCrecimiento.PESO_PARA_LONGITUD,
                    ajuste_cm=0.7,
                    descripcion_ajuste=(
                        "OMS: menor de 24 meses medido de pie; se suma 0.7 cm."
                    ),
                )
            return MedidaLongitudTalla(
                valor_original_cm=valor,
                valor_oms_cm=valor,
                posicion_original=posicion_normalizada,
                indicador_edad=IndicadorCrecimiento.LONGITUD_PARA_EDAD,
                indicador_peso=IndicadorCrecimiento.PESO_PARA_LONGITUD,
                ajuste_cm=0.0,
                descripcion_ajuste="Longitud recumbente usada sin ajuste.",
            )

        if posicion_normalizada == PosicionMedicion.ACOSTADO:
            return MedidaLongitudTalla(
                valor_original_cm=valor,
                valor_oms_cm=valor - 0.7,
                posicion_original=posicion_normalizada,
                indicador_edad=IndicadorCrecimiento.TALLA_PARA_EDAD,
                indicador_peso=IndicadorCrecimiento.PESO_PARA_TALLA,
                ajuste_cm=-0.7,
                descripcion_ajuste=(
                    "OMS: desde 24 meses medido acostado; se resta 0.7 cm."
                ),
            )
        return MedidaLongitudTalla(
            valor_original_cm=valor,
            valor_oms_cm=valor,
            posicion_original=posicion_normalizada,
            indicador_edad=IndicadorCrecimiento.TALLA_PARA_EDAD,
            indicador_peso=IndicadorCrecimiento.PESO_PARA_TALLA,
            ajuste_cm=0.0,
            descripcion_ajuste="Talla de pie usada sin ajuste.",
        )

    def _seleccionar_edad(
        self,
        *,
        paciente: Paciente,
        edad_cronologica_dias: int,
        edad_corregida_dias: int,
        usar_edad_corregida: bool,
    ) -> tuple[int, str, str]:
        if (
            usar_edad_corregida
            and paciente.es_prematuro
            and edad_corregida_dias >= 0
            and edad_cronologica_dias < 731
        ):
            return (
                edad_corregida_dias,
                "corregida",
                "Paciente prematuro menor de 24 meses; se usa edad corregida.",
            )

        return (
            edad_cronologica_dias,
            "cronologica",
            "Se usa edad cronológica para referencia OMS 2006.",
        )

    def _evaluar_por_edad(
        self,
        *,
        indicador: IndicadorCrecimiento,
        valor: float,
        unidad: str,
        paciente: Paciente,
        edad_dias: int,
    ) -> ResultadoIndicadorOMS:
        lookup = self.repository.obtener_por_edad(
            indicador=indicador,
            sexo=paciente.sexo,
            edad_dias=edad_dias,
        )
        return self._construir_resultado(
            indicador=indicador,
            valor=valor,
            unidad=unidad,
            lookup=lookup,
        )

    def _evaluar_por_medida(
        self,
        *,
        indicador: IndicadorCrecimiento,
        valor: float,
        unidad: str,
        paciente: Paciente,
        medida_cm: float,
    ) -> ResultadoIndicadorOMS:
        lookup = self.repository.obtener_por_medida(
            indicador=indicador,
            sexo=paciente.sexo,
            medida_cm=medida_cm,
        )
        return self._construir_resultado(
            indicador=indicador,
            valor=valor,
            unidad=unidad,
            lookup=lookup,
        )

    def _construir_resultado(
        self,
        *,
        indicador: IndicadorCrecimiento,
        valor: float,
        unidad: str,
        lookup: Any,
    ) -> ResultadoIndicadorOMS:
        bruto = self.zscore.calcular(valor, lookup.parametros)
        z_ajustado = self.zscore.ajustar_z_score_oms(
            valor, lookup.parametros, bruto.z_score
        )
        percentil = self.zscore.calcular_percentil(z_ajustado)
        clinico = self.evaluador.evaluar_z_score(
            indicador=indicador,
            valor=valor,
            unidad=unidad,
            z_score=z_ajustado,
            referencia=ReferenciaCrecimiento.OMS_2006,
        )
        bandera = self._evaluar_plausibilidad(indicador, z_ajustado)

        auditoria = AuditoriaIndicadorOMS(
            valor_observado=valor,
            unidad=unidad,
            parametros_lms={
                "L": lookup.parametros.lambda_box_cox,
                "M": lookup.parametros.mediana,
                "S": lookup.parametros.coeficiente_variacion,
            },
            z_score_bruto=bruto.z_score,
            z_score=z_ajustado,
            percentil=percentil,
            clasificacion=clinico.clasificacion.value,
            severidad=clinico.severidad.value,
            fuente=lookup.parametros.fuente or "",
            version=lookup.parametros.version or "",
            bandera_plausibilidad=bandera,
            indice_lms=lookup.auditoria,
        )

        return ResultadoIndicadorOMS(
            indicador=indicador,
            nombre=self._NOMBRES[indicador],
            valor=valor,
            unidad=unidad,
            z_score=z_ajustado,
            percentil=percentil,
            clasificacion=self._descripcion_clasificacion(
                clinico.clasificacion,
                indicador,
            ),
            severidad=clinico.severidad.value,
            interpretacion=clinico.interpretacion,
            bandera_plausibilidad=bandera,
            auditoria=auditoria,
        )

    def _evaluar_plausibilidad(
        self,
        indicador: IndicadorCrecimiento,
        z_score: float,
    ) -> str | None:
        limite = self._PLAUSIBILIDAD[indicador]
        if z_score < limite[0]:
            return "Bandera OMS: valor biológicamente improbable bajo."
        if z_score > limite[1]:
            return "Bandera OMS: valor biológicamente improbable alto."
        return None

    @staticmethod
    def _descripcion_clasificacion(
        clasificacion: ClasificacionCrecimiento,
        indicador: IndicadorCrecimiento,
    ) -> str:
        if indicador == IndicadorCrecimiento.PESO_PARA_EDAD:
            mapping = {
                ClasificacionCrecimiento.BAJO_PESO_SEVERO: "Peso muy bajo",
                ClasificacionCrecimiento.BAJO_PESO: "Peso bajo",
                ClasificacionCrecimiento.RIESGO_BAJO_PESO: "Riesgo bajo peso",
                ClasificacionCrecimiento.ADECUADO: "Adecuado",
            }
        elif indicador in {
            IndicadorCrecimiento.LONGITUD_PARA_EDAD,
            IndicadorCrecimiento.TALLA_PARA_EDAD,
        }:
            mapping = {
                ClasificacionCrecimiento.TALLA_BAJA_SEVERA: "Talla muy baja",
                ClasificacionCrecimiento.TALLA_BAJA: "Talla baja",
                ClasificacionCrecimiento.RIESGO_TALLA_BAJA: "Riesgo talla baja",
                ClasificacionCrecimiento.ADECUADO: "Adecuado",
            }
        elif indicador == IndicadorCrecimiento.PERIMETRO_CEFALICO_PARA_EDAD:
            mapping = {
                ClasificacionCrecimiento.PERIMETRO_CEFALICO_BAJO: "PC bajo",
                ClasificacionCrecimiento.PERIMETRO_CEFALICO_ALTO: "PC alto",
                ClasificacionCrecimiento.ADECUADO: "Adecuado",
            }
        else:
            mapping = {
                ClasificacionCrecimiento.DESNUTRICION_AGUDA_SEVERA: "Delgadez severa",
                ClasificacionCrecimiento.DESNUTRICION_AGUDA_MODERADA: "Delgadez",
                ClasificacionCrecimiento.RIESGO_DESNUTRICION_AGUDA: "Riesgo bajo peso",
                ClasificacionCrecimiento.ADECUADO: "Adecuado",
                ClasificacionCrecimiento.RIESGO_SOBREPESO: "Riesgo sobrepeso",
                ClasificacionCrecimiento.SOBREPESO: "Sobrepeso",
                ClasificacionCrecimiento.OBESIDAD: "Obesidad",
            }
        return mapping.get(clasificacion, clasificacion.value)
