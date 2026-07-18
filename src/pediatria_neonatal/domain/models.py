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
            raise ErrorTablaLMS("Sexo inválido. Use M/masculino o F/femenino.") from exc


@dataclass(frozen=True, slots=True)
class EdadCorregida:
    """Resultado del cálculo de edad corregida neonatal.

    La edad corregida se conserva internamente en días y semanas.

    Para la presentación en meses se utiliza la equivalencia clínica
    aproximada:

        1 mes = 4 semanas = 28 días

    Esta conversión no representa meses calendario, debido a que estos
    pueden tener entre 28 y 31 días.
    """

    edad_cronologica_dias: int
    prematuridad_dias: int
    edad_corregida_total_dias: int
    semanas: int
    dias: int
    es_antes_de_termino: bool

    SEMANAS_POR_MES = 4

    @property
    def meses(self) -> int:
        """Retorna los meses aproximados completos de edad corregida."""

        return self.semanas // self.SEMANAS_POR_MES

    @property
    def semanas_restantes(self) -> int:
        """Retorna las semanas restantes después de calcular los meses."""

        return self.semanas % self.SEMANAS_POR_MES

    @property
    def texto(self) -> str:
        """Retorna la edad corregida incluyendo meses aproximados."""

        prefijo = "-" if self.es_antes_de_termino else ""

        return (
            f"{prefijo}{self.meses} meses, "
            f"{self.semanas_restantes} semanas y "
            f"{self.dias} días "
            f"({self.semanas} semanas totales)"
        )
