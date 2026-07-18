"""Servicio de cálculos antropométricos pediátricos."""

from __future__ import annotations

import math

from pediatria_neonatal.domain.exceptions import ErrorDatoAntropometrico
from pediatria_neonatal.domain.paciente import MedicionAntropometrica


class CalculadoraAntropometrica:
    """Realiza cálculos antropométricos sobre mediciones clínicas."""

    PESO_MINIMO_KG = 0.2
    PESO_MAXIMO_KG = 250.0
    TALLA_MINIMA_CM = 20.0
    TALLA_MAXIMA_CM = 250.0
    IMC_MINIMO = 3.0
    IMC_MAXIMO = 100.0

    def calcular_imc(
        self,
        peso_kg: float,
        talla_cm: float,
    ) -> float:
        """Calcula el índice de masa corporal.

        Fórmula:

            IMC = peso_kg / talla_m²

        La talla se recibe en centímetros y se convierte a metros antes
        de elevarse al cuadrado.

        Parameters
        ----------
        peso_kg:
            Peso corporal expresado en kilogramos.

        talla_cm:
            Talla o longitud expresada en centímetros.

        Returns
        -------
        float
            Índice de masa corporal en kg/m².

        Raises
        ------
        ErrorDatoAntropometrico
            Si peso, talla o resultado están fuera de los límites técnicos.
        """

        peso = self._validar_numero_finito(
            peso_kg,
            nombre_campo="peso_kg",
        )
        talla = self._validar_numero_finito(
            talla_cm,
            nombre_campo="talla_cm",
        )

        self._validar_peso(peso)
        self._validar_talla(talla)

        talla_m = talla / 100.0
        imc = peso / (talla_m**2)

        if not self.IMC_MINIMO <= imc <= self.IMC_MAXIMO:
            raise ErrorDatoAntropometrico(
                "El IMC calculado está fuera del rango técnico permitido. "
                "Verifique el peso, la talla y sus unidades."
            )

        return imc

    def calcular_imc_medicion(
        self,
        medicion: MedicionAntropometrica,
    ) -> float:
        """Calcula el IMC usando una medición antropométrica.

        La medición debe contener tanto peso como talla.

        Parameters
        ----------
        medicion:
            Objeto clínico con fecha, peso y talla.

        Returns
        -------
        float
            Índice de masa corporal en kg/m².

        Raises
        ------
        ErrorDatoAntropometrico
            Si la medición no contiene peso o talla.
        """

        if medicion.peso_kg is None:
            raise ErrorDatoAntropometrico(
                "La medición no contiene peso para calcular el IMC."
            )

        if medicion.talla_cm is None:
            raise ErrorDatoAntropometrico(
                "La medición no contiene talla para calcular el IMC."
            )

        return self.calcular_imc(
            peso_kg=medicion.peso_kg,
            talla_cm=medicion.talla_cm,
        )

    def _validar_peso(self, peso_kg: float) -> None:
        """Valida el rango técnico permitido para el peso."""

        if not self.PESO_MINIMO_KG <= peso_kg <= self.PESO_MAXIMO_KG:
            raise ErrorDatoAntropometrico(
                "peso_kg fuera del rango técnico permitido: "
                f"{self.PESO_MINIMO_KG} a {self.PESO_MAXIMO_KG} kg."
            )

    def _validar_talla(self, talla_cm: float) -> None:
        """Valida el rango técnico permitido para la talla."""

        if not self.TALLA_MINIMA_CM <= talla_cm <= self.TALLA_MAXIMA_CM:
            raise ErrorDatoAntropometrico(
                "talla_cm fuera del rango técnico permitido: "
                f"{self.TALLA_MINIMA_CM} a {self.TALLA_MAXIMA_CM} cm."
            )

    @staticmethod
    def _validar_numero_finito(
        valor: float,
        *,
        nombre_campo: str,
    ) -> float:
        """Convierte y valida un número real finito."""

        if isinstance(valor, bool):
            raise ErrorDatoAntropometrico(f"{nombre_campo} debe ser un número real.")

        try:
            numero = float(valor)
        except (TypeError, ValueError) as exc:
            raise ErrorDatoAntropometrico(
                f"{nombre_campo} debe ser un número real."
            ) from exc

        if not math.isfinite(numero):
            raise ErrorDatoAntropometrico(f"{nombre_campo} debe ser un número finito.")

        return numero
