"""Repositorio local de tablas LMS OMS 2006.

Los datos se cargan desde CSV empaquetados con la aplicación. El runtime usa
solo la librería estándar para mantener compatibilidad y tamaño razonable en
iOS.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import NamedTuple

from pediatria_neonatal.domain.exceptions import ErrorTablaLMS
from pediatria_neonatal.domain.lms import (
    IndicadorCrecimiento,
    ParametrosLMS,
    ReferenciaCrecimiento,
)
from pediatria_neonatal.domain.models import Sexo


@dataclass(frozen=True, slots=True)
class LMSAudit:
    """Metadatos de consulta de una fila LMS."""

    indice_solicitado: float
    indice_usado: float
    unidad_indice: str
    metodo: str


class LMSLookupResult(NamedTuple):
    """Resultado de consulta LMS con auditoría técnica."""

    parametros: ParametrosLMS
    auditoria: LMSAudit


@dataclass(frozen=True, slots=True)
class _TablaConfig:
    archivo: str
    columna_indice: str
    unidad_edad: str


class LMSRepository:
    """Consulta parámetros LMS oficiales OMS 2006 incluidos localmente."""

    FUENTE = "WHO anthro R package"
    VERSION = "1.1.0 / WHO Child Growth Standards 2006"

    _CONFIG: dict[IndicadorCrecimiento, _TablaConfig] = {
        IndicadorCrecimiento.PESO_PARA_EDAD: _TablaConfig(
            "weight_for_age.csv", "age", "dias"
        ),
        IndicadorCrecimiento.LONGITUD_PARA_EDAD: _TablaConfig(
            "length_height_for_age.csv", "age", "dias"
        ),
        IndicadorCrecimiento.TALLA_PARA_EDAD: _TablaConfig(
            "length_height_for_age.csv", "age", "dias"
        ),
        IndicadorCrecimiento.PESO_PARA_LONGITUD: _TablaConfig(
            "weight_for_length.csv", "length", "cm"
        ),
        IndicadorCrecimiento.PESO_PARA_TALLA: _TablaConfig(
            "weight_for_height.csv", "height", "cm"
        ),
        IndicadorCrecimiento.IMC_PARA_EDAD: _TablaConfig(
            "bmi_for_age.csv", "age", "dias"
        ),
        IndicadorCrecimiento.PERIMETRO_CEFALICO_PARA_EDAD: _TablaConfig(
            "head_circumference_for_age.csv", "age", "dias"
        ),
    }

    def obtener_por_edad(
        self,
        *,
        indicador: IndicadorCrecimiento,
        sexo: Sexo | str,
        edad_dias: int,
    ) -> LMSLookupResult:
        """Obtiene LMS para un indicador dependiente de edad exacta en días."""

        if edad_dias < 0:
            raise ErrorTablaLMS("La edad en días no puede ser negativa.")

        return self._buscar(
            indicador=indicador,
            sexo=Sexo.normalizar(sexo),
            indice=float(edad_dias),
        )

    def obtener_por_medida(
        self,
        *,
        indicador: IndicadorCrecimiento,
        sexo: Sexo | str,
        medida_cm: float,
    ) -> LMSLookupResult:
        """Obtiene LMS para peso/longitud o peso/talla por cm."""

        if medida_cm <= 0:
            raise ErrorTablaLMS("La medida en cm debe ser positiva.")

        return self._buscar(
            indicador=indicador,
            sexo=Sexo.normalizar(sexo),
            indice=round(float(medida_cm), 1),
        )

    def _buscar(
        self,
        *,
        indicador: IndicadorCrecimiento,
        sexo: Sexo,
        indice: float,
    ) -> LMSLookupResult:
        config = self._CONFIG.get(indicador)
        if config is None:
            raise ErrorTablaLMS(f"Indicador OMS 2006 no soportado: {indicador}")

        filas = self._cargar_tabla(config.archivo)
        sex_code = 1 if sexo == Sexo.MASCULINO else 2
        candidatas = [fila for fila in filas if int(fila["sex"]) == sex_code]

        if not candidatas:
            raise ErrorTablaLMS("No existen filas LMS para el sexo solicitado.")

        indice_min = float(candidatas[0][config.columna_indice])
        indice_max = float(candidatas[-1][config.columna_indice])
        if not indice_min <= indice <= indice_max:
            raise ErrorTablaLMS(
                "El índice solicitado está fuera de la tabla OMS 2006: "
                f"{indice} ({indice_min} a {indice_max})."
            )

        fila = min(
            candidatas,
            key=lambda item: abs(float(item[config.columna_indice]) - indice),
        )
        indice_usado = float(fila[config.columna_indice])

        parametros = ParametrosLMS(
            referencia=ReferenciaCrecimiento.OMS_2006,
            indicador=indicador,
            sexo=sexo,
            edad=indice_usado,
            unidad_edad=config.unidad_edad,
            lambda_box_cox=float(fila["l"]),
            mediana=float(fila["m"]),
            coeficiente_variacion=float(fila["s"]),
            fuente=self.FUENTE,
            version=self.VERSION,
        )

        return LMSLookupResult(
            parametros=parametros,
            auditoria=LMSAudit(
                indice_solicitado=indice,
                indice_usado=indice_usado,
                unidad_indice=config.unidad_edad,
                metodo="exacto" if indice == indice_usado else "vecino_mas_cercano",
            ),
        )

    @staticmethod
    @lru_cache(maxsize=None)
    def _cargar_tabla(archivo: str) -> tuple[dict[str, str], ...]:
        paquete = resources.files("pediatria_neonatal.data.who_2006")
        ruta = paquete.joinpath(archivo)

        with ruta.open("r", encoding="utf-8", newline="") as handle:
            return tuple(csv.DictReader(handle))
