"""Modelos y objetos de valor del dominio pediátrico y neonatal."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pediatria_neonatal.domain.exceptions import ErrorTablaLMS


class Sexo(StrEnum):
    """Sexo utilizado por las tablas antropométricas LMS."""

    MASCULINO = "M"
    FEMENINO = "F"

    @classmethod
    def normalizar(cls, valor: str | Sexo) -> Sexo:
        """Convierte diferentes representaciones al valor estándar M o F.

        Parameters
        ----------
        valor:
            Texto o instancia de ``Sexo``.

        Returns
        -------
        Sexo
            Valor normalizado del enum.

        Raises
        ------
        ErrorTablaLMS
            Si el valor no corresponde a masculino o femenino.
        """

        if isinstance(valor, cls):
            return valor

        valor_normalizado = str(valor).strip().upper()

        alias = {
            "M": cls.MASCULINO,
            "MASCULINO": cls.MASCULINO,
            "MALE": cls.MASCULINO,
            "HOMBRE": cls.MASCULINO,
            "NIÑO": cls.MASCULINO,
            "NINO": cls.MASCULINO,
            "F": cls.FEMENINO,
            "FEMENINO": cls.FEMENINO,
            "FEMALE": cls.FEMENINO,
            "MUJER": cls.FEMENINO,
            "NIÑA": cls.FEMENINO,
            "NINA": cls.FEMENINO,
        }

        try:
            return alias[valor_normalizado]
        except KeyError as exc:
            raise ErrorTablaLMS(
                "Sexo inválido. Use M/masculino o F/femenino."
            ) from exc


@dataclass(frozen=True, slots=True)
class EdadCorregida:
    """Resultado del cálculo de edad corregida neonatal.

    Attributes
    ----------
    edad_cronologica_dias:
        Días transcurridos desde el nacimiento hasta la medición.

    prematuridad_dias:
        Días faltantes desde la edad gestacional al nacimiento hasta
        completar 40 semanas.

    edad_corregida_total_dias:
        Edad cronológica menos los días de prematuridad.

    semanas:
        Semanas completas de la edad corregida.

    dias:
        Días restantes después de calcular las semanas completas.

    es_antes_de_termino:
        Indica si la fecha de medición ocurre antes de la fecha teórica
        de término.
    """

    edad_cronologica_dias: int
    prematuridad_dias: int
    edad_corregida_total_dias: int
    semanas: int
    dias: int
    es_antes_de_termino: bool

    @property
    def texto(self) -> str:
        """Retorna la edad corregida en formato legible."""

        prefijo = "-" if self.es_antes_de_termino else ""
        return f"{prefijo}{self.semanas} semanas y {self.dias} días"


@dataclass(frozen=True, slots=True)
class ParametrosLMS:
    """Parámetros LMS utilizados en el cálculo de puntuación Z.

    La metodología LMS representa la distribución de una medida
    antropométrica mediante tres parámetros:

    ``lambda_box_cox``:
        Parámetro L. Potencia Box-Cox utilizada para corregir la
        asimetría de la distribución.

    ``mediana``:
        Parámetro M. Mediana esperada para un sexo y una edad
        determinados.

    ``coeficiente_variacion``:
        Parámetro S. Coeficiente de variación generalizado.
    """

    sexo: Sexo
    edad_meses: float
    lambda_box_cox: float
    mediana: float
    coeficiente_variacion: float
    fuente: str | None = None

    def __post_init__(self) -> None:
        """Valida que los parámetros LMS sean matemáticamente válidos."""

        if self.edad_meses < 0:
            raise ErrorTablaLMS(
                "La edad en meses no puede ser negativa."
            )

        if self.mediana <= 0:
            raise ErrorTablaLMS(
                "El parámetro M debe ser mayor que cero."
            )

        if self.coeficiente_variacion <= 0:
            raise ErrorTablaLMS(
                "El parámetro S debe ser mayor que cero."
            )