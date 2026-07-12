"""Servicio para el cálculo de edad corregida neonatal."""

from __future__ import annotations

from datetime import date, datetime

from pediatria_neonatal.domain.exceptions import (
    ErrorEdadGestacional,
    ErrorFecha,
)
from pediatria_neonatal.domain.models import EdadCorregida

FechaCompatible = date | datetime | str


class CalculadoraNeonatal:
    """Realiza cálculos relacionados con edad gestacional y corregida."""

    SEMANAS_TERMINO = 40
    DIAS_POR_SEMANA = 7

    EDAD_GESTACIONAL_MINIMA_SEMANAS = 22
    EDAD_GESTACIONAL_MAXIMA_SEMANAS = 42
    EDAD_GESTACIONAL_MAXIMA_DIAS = 6

    def calcular_edad_corregida(
        self,
        fecha_nacimiento: FechaCompatible,
        fecha_medicion: FechaCompatible,
        eg_semanas: int,
        eg_dias: int,
    ) -> EdadCorregida:
        """Calcula la edad corregida de un paciente neonatal.

        La edad corregida se obtiene restando a la edad cronológica
        los días de prematuridad.

        Fórmula:

            edad corregida =
                edad cronológica
                - días faltantes para completar 40 semanas

        La edad gestacional total al nacimiento se calcula así:

            edad gestacional en días =
                eg_semanas * 7 + eg_dias

        La prematuridad se calcula respecto de 40 semanas:

            prematuridad =
                280 días - edad gestacional al nacimiento

        Para nacimientos de 40 semanas o más, la prematuridad se
        considera igual a cero.

        Parameters
        ----------
        fecha_nacimiento:
            Fecha de nacimiento como ``date``, ``datetime`` o texto
            ISO con formato ``YYYY-MM-DD``.

        fecha_medicion:
            Fecha en la cual se realiza la medición.

        eg_semanas:
            Semanas completas de edad gestacional al nacimiento.

        eg_dias:
            Días adicionales de edad gestacional, entre 0 y 6.

        Returns
        -------
        EdadCorregida
            Objeto inmutable con edad cronológica, prematuridad y
            edad corregida.

        Raises
        ------
        ErrorFecha
            Si las fechas son inválidas o la medición es anterior
            al nacimiento.

        ErrorEdadGestacional
            Si la edad gestacional está fuera de los límites permitidos.
        """

        nacimiento = self._normalizar_fecha(
            fecha_nacimiento,
            nombre_campo="fecha_nacimiento",
        )
        medicion = self._normalizar_fecha(
            fecha_medicion,
            nombre_campo="fecha_medicion",
        )

        self._validar_fechas(
            fecha_nacimiento=nacimiento,
            fecha_medicion=medicion,
        )

        edad_gestacional_dias = self._validar_edad_gestacional(
            eg_semanas=eg_semanas,
            eg_dias=eg_dias,
        )

        edad_cronologica_dias = (medicion - nacimiento).days

        dias_termino = (
            self.SEMANAS_TERMINO
            * self.DIAS_POR_SEMANA
        )

        prematuridad_dias = max(
            0,
            dias_termino - edad_gestacional_dias,
        )

        edad_corregida_total_dias = (
            edad_cronologica_dias
            - prematuridad_dias
        )

        semanas, dias = divmod(
            abs(edad_corregida_total_dias),
            self.DIAS_POR_SEMANA,
        )

        return EdadCorregida(
            edad_cronologica_dias=edad_cronologica_dias,
            prematuridad_dias=prematuridad_dias,
            edad_corregida_total_dias=edad_corregida_total_dias,
            semanas=semanas,
            dias=dias,
            es_antes_de_termino=edad_corregida_total_dias < 0,
        )

    def _validar_edad_gestacional(
        self,
        eg_semanas: int,
        eg_dias: int,
    ) -> int:
        """Valida y convierte la edad gestacional a días."""

        if isinstance(eg_semanas, bool) or not isinstance(
            eg_semanas,
            int,
        ):
            raise ErrorEdadGestacional(
                "eg_semanas debe ser un número entero."
            )

        if isinstance(eg_dias, bool) or not isinstance(
            eg_dias,
            int,
        ):
            raise ErrorEdadGestacional(
                "eg_dias debe ser un número entero."
            )

        if not 0 <= eg_dias <= self.EDAD_GESTACIONAL_MAXIMA_DIAS:
            raise ErrorEdadGestacional(
                "eg_dias debe estar entre 0 y 6."
            )

        edad_gestacional_total_dias = (
            eg_semanas * self.DIAS_POR_SEMANA
            + eg_dias
        )

        edad_minima_dias = (
            self.EDAD_GESTACIONAL_MINIMA_SEMANAS
            * self.DIAS_POR_SEMANA
        )

        edad_maxima_dias = (
            self.EDAD_GESTACIONAL_MAXIMA_SEMANAS
            * self.DIAS_POR_SEMANA
            + self.EDAD_GESTACIONAL_MAXIMA_DIAS
        )

        if not (
            edad_minima_dias
            <= edad_gestacional_total_dias
            <= edad_maxima_dias
        ):
            raise ErrorEdadGestacional(
                "La edad gestacional debe estar entre "
                "22+0 y 42+6 semanas."
            )

        return edad_gestacional_total_dias

    @staticmethod
    def _validar_fechas(
        fecha_nacimiento: date,
        fecha_medicion: date,
    ) -> None:
        """Valida la relación cronológica entre ambas fechas."""

        if fecha_medicion < fecha_nacimiento:
            raise ErrorFecha(
                "La fecha de medición no puede ser anterior "
                "a la fecha de nacimiento."
            )

    @staticmethod
    def _normalizar_fecha(
        valor: FechaCompatible,
        *,
        nombre_campo: str,
    ) -> date:
        """Convierte una fecha compatible al tipo ``date``."""

        if isinstance(valor, datetime):
            return valor.date()

        if isinstance(valor, date):
            return valor

        if isinstance(valor, str):
            try:
                return date.fromisoformat(valor)
            except ValueError as exc:
                raise ErrorFecha(
                    f"{nombre_campo} debe tener formato ISO YYYY-MM-DD."
                ) from exc

        raise ErrorFecha(
            f"{nombre_campo} debe ser date, datetime "
            "o texto ISO YYYY-MM-DD."
        )