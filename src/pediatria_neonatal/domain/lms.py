"""Modelos del dominio para referencias antropométricas LMS."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from pediatria_neonatal.domain.exceptions import ErrorTablaLMS
from pediatria_neonatal.domain.models import Sexo


class IndicadorCrecimiento(StrEnum):
    """Indicadores antropométricos soportados por la aplicación."""

    IMC_PARA_EDAD = "bmi_for_age"
    PESO_PARA_LONGITUD = "weight_for_length"
    PESO_PARA_TALLA = "weight_for_height"
    PESO_PARA_EDAD = "weight_for_age"
    LONGITUD_PARA_EDAD = "length_for_age"
    TALLA_PARA_EDAD = "height_for_age"
    PERIMETRO_CEFALICO_PARA_EDAD = "head_circumference_for_age"

    PESO_PARA_EDAD_GESTACIONAL = "weight_for_gestational_age"
    LONGITUD_PARA_EDAD_GESTACIONAL = "length_for_gestational_age"
    PERIMETRO_CEFALICO_PARA_EDAD_GESTACIONAL = (
        "head_circumference_for_gestational_age"
    )

    INDICE_OBESIDAD = "obesity_index"


class ReferenciaCrecimiento(StrEnum):
    """Referencias de crecimiento disponibles en el sistema."""

    OMS_2006 = "WHO_2006"
    FENTON_2025 = "FENTON_2025"
    INTERGROWTH_21 = "INTERGROWTH_21"
    CDC_2000 = "CDC_2000"
    SIN_REFERENCIA = "NONE"


class PoliticaInterpolacion(StrEnum):
    """Política usada cuando no existe una fila LMS exacta."""

    NINGUNA = "none"
    LINEAL = "linear"


@dataclass(frozen=True, slots=True)
class ParametrosLMS:
    """Parámetros LMS asociados a un indicador y una referencia.

    La metodología LMS resume una distribución antropométrica mediante:

    - L: potencia Box-Cox que modela la asimetría.
    - M: mediana esperada.
    - S: coeficiente de variación generalizado.

    La edad se almacena como un valor decimal cuya unidad se declara
    explícitamente. Para OMS normalmente será meses. Para Fenton puede
    representar semanas gestacionales.
    """

    referencia: ReferenciaCrecimiento
    indicador: IndicadorCrecimiento
    sexo: Sexo
    edad: float
    unidad_edad: str

    lambda_box_cox: float
    mediana: float
    coeficiente_variacion: float

    fuente: str | None = None
    version: str | None = None

    def __post_init__(self) -> None:
        """Valida la consistencia matemática y semántica del registro."""

        self._validar_numero_finito(
            self.edad,
            nombre_campo="edad",
        )
        self._validar_numero_finito(
            self.lambda_box_cox,
            nombre_campo="lambda_box_cox",
        )
        self._validar_numero_finito(
            self.mediana,
            nombre_campo="mediana",
        )
        self._validar_numero_finito(
            self.coeficiente_variacion,
            nombre_campo="coeficiente_variacion",
        )

        if self.edad < 0:
            raise ErrorTablaLMS(
                "La edad de la referencia no puede ser negativa."
            )

        if self.mediana <= 0:
            raise ErrorTablaLMS(
                "El parámetro M debe ser mayor que cero."
            )

        if self.coeficiente_variacion <= 0:
            raise ErrorTablaLMS(
                "El parámetro S debe ser mayor que cero."
            )

        unidad_normalizada = self.unidad_edad.strip().lower()

        if unidad_normalizada not in {
            "dias",
            "meses",
            "semanas",
            "semanas_gestacionales",
        }:
            raise ErrorTablaLMS(
                "unidad_edad debe ser dias, meses, semanas o "
                "semanas_gestacionales."
            )

        object.__setattr__(
            self,
            "unidad_edad",
            unidad_normalizada,
        )

        if self.fuente is not None:
            fuente_normalizada = self.fuente.strip()

            if not fuente_normalizada:
                raise ErrorTablaLMS(
                    "La fuente no puede contener solo espacios."
                )

            object.__setattr__(
                self,
                "fuente",
                fuente_normalizada,
            )

        if self.version is not None:
            version_normalizada = self.version.strip()

            if not version_normalizada:
                raise ErrorTablaLMS(
                    "La versión no puede contener solo espacios."
                )

            object.__setattr__(
                self,
                "version",
                version_normalizada,
            )

    @property
    def clave(self) -> tuple[
        ReferenciaCrecimiento,
        IndicadorCrecimiento,
        Sexo,
        float,
    ]:
        """Retorna la clave principal del registro LMS."""

        return (
            self.referencia,
            self.indicador,
            self.sexo,
            self.edad,
        )

    @staticmethod
    def _validar_numero_finito(
        valor: float,
        *,
        nombre_campo: str,
    ) -> None:
        """Valida que un atributo sea numérico y finito."""

        if isinstance(valor, bool) or not isinstance(valor, int | float):
            raise ErrorTablaLMS(
                f"{nombre_campo} debe ser un número real."
            )

        if not math.isfinite(float(valor)):
            raise ErrorTablaLMS(
                f"{nombre_campo} debe ser un número finito."
            )