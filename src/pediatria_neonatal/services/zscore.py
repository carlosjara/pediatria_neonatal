"""Cálculo de Z-score y percentiles mediante el método LMS."""

from __future__ import annotations

import math
from dataclasses import dataclass

from pediatria_neonatal.domain.exceptions import (
    ErrorDatoAntropometrico,
    ErrorTablaLMS,
)
from pediatria_neonatal.domain.lms import ParametrosLMS

@dataclass(frozen=True, slots=True)
class ResultadoZScore:
    """Resultado matemático del cálculo LMS.

    Esta clase no contiene interpretación clínica. Su responsabilidad es
    conservar el resultado cuantitativo que posteriormente utilizará el
    motor de evaluación clínica.

    Attributes
    ----------
    valor:
        Valor antropométrico evaluado, por ejemplo IMC, peso o talla.

    z_score:
        Distancia respecto de la mediana expresada en desviaciones estándar.

    percentil:
        Percentil aproximado derivado de la distribución normal estándar.

    parametros:
        Parámetros LMS utilizados durante el cálculo.
    """

    valor: float
    z_score: float
    percentil: float
    parametros: ParametrosLMS

    @property
    def desviaciones_estandar_texto(self) -> str:
        """Retorna el Z-score con signo y dos posiciones decimales."""

        return f"{self.z_score:+.2f} DE"

    @property
    def percentil_texto(self) -> str:
        """Retorna una representación clínica legible del percentil."""

        if self.percentil < 0.1:
            return "< P0.1"

        if self.percentil > 99.9:
            return "> P99.9"

        return f"P{self.percentil:.1f}"


class CalculadoraZScore:
    """Calcula puntuaciones Z mediante la metodología LMS."""

    TOLERANCIA_LAMBDA_CERO = 1e-12
    Z_SCORE_MINIMO_TECNICO = -20.0
    Z_SCORE_MAXIMO_TECNICO = 20.0

    def calcular(
        self,
        valor: float,
        parametros: ParametrosLMS,
    ) -> ResultadoZScore:
        """Calcula el Z-score mediante la transformación Box-Cox LMS.

        Para un parámetro L distinto de cero se utiliza:

            Z = (((X / M) ** L) - 1) / (L * S)

        donde:

        - X es el valor antropométrico observado.
        - L es la potencia Box-Cox.
        - M es la mediana de la población de referencia.
        - S es el coeficiente de variación generalizado.

        Cuando L es cero, la expresión anterior presenta una división por
        cero. En ese caso se utiliza su límite matemático:

            Z = ln(X / M) / S

        Parameters
        ----------
        valor:
            Valor antropométrico positivo que se desea comparar.

        parametros:
            Parámetros LMS correspondientes al indicador, sexo y edad.

        Returns
        -------
        ResultadoZScore
            Resultado matemático con Z-score y percentil aproximado.

        Raises
        ------
        ErrorDatoAntropometrico
            Si el valor no es positivo, finito o produce un resultado inválido.

        ErrorTablaLMS
            Si los parámetros LMS no permiten realizar el cálculo.
        """

        valor_validado = self._validar_valor(valor)

        razon = valor_validado / parametros.mediana

        if razon <= 0:
            raise ErrorTablaLMS(
                "La relación entre el valor y la mediana debe ser positiva."
            )

        if math.isclose(
            parametros.lambda_box_cox,
            0.0,
            abs_tol=self.TOLERANCIA_LAMBDA_CERO,
        ):
            z_score = (
                math.log(razon)
                / parametros.coeficiente_variacion
            )
        else:
            numerador = (
                razon**parametros.lambda_box_cox
                - 1.0
            )
            denominador = (
                parametros.lambda_box_cox
                * parametros.coeficiente_variacion
            )

            if math.isclose(denominador, 0.0, abs_tol=1e-15):
                raise ErrorTablaLMS(
                    "El denominador LMS no puede ser igual a cero."
                )

            z_score = numerador / denominador

        self._validar_z_score(z_score)

        percentil = self.calcular_percentil(z_score)

        return ResultadoZScore(
            valor=valor_validado,
            z_score=z_score,
            percentil=percentil,
            parametros=parametros,
        )

    @staticmethod
    def calcular_percentil(z_score: float) -> float:
        """Convierte un Z-score al percentil normal estándar.

        Se utiliza la función de distribución acumulada normal:

            percentil = Φ(Z) × 100

        Esta conversión es una aproximación descriptiva. La interpretación
        clínica debe realizarse usando los puntos de corte definidos para cada
        indicador y referencia.
        """

        if isinstance(z_score, bool):
            raise ErrorDatoAntropometrico(
                "El Z-score debe ser un número real."
            )

        try:
            z_validado = float(z_score)
        except (TypeError, ValueError) as exc:
            raise ErrorDatoAntropometrico(
                "El Z-score debe ser un número real."
            ) from exc

        if not math.isfinite(z_validado):
            raise ErrorDatoAntropometrico(
                "El Z-score debe ser un número finito."
            )

        return (
            0.5
            * (
                1.0
                + math.erf(
                    z_validado / math.sqrt(2.0),
                )
            )
            * 100.0
        )

    @staticmethod
    def _validar_valor(valor: float) -> float:
        """Valida que el valor antropométrico sea positivo y finito."""

        if isinstance(valor, bool):
            raise ErrorDatoAntropometrico(
                "El valor antropométrico debe ser un número real."
            )

        try:
            valor_validado = float(valor)
        except (TypeError, ValueError) as exc:
            raise ErrorDatoAntropometrico(
                "El valor antropométrico debe ser un número real."
            ) from exc

        if not math.isfinite(valor_validado):
            raise ErrorDatoAntropometrico(
                "El valor antropométrico debe ser finito."
            )

        if valor_validado <= 0:
            raise ErrorDatoAntropometrico(
                "El valor antropométrico debe ser mayor que cero."
            )

        return valor_validado

    def _validar_z_score(self, z_score: float) -> None:
        """Valida que el resultado matemático sea finito y razonable."""

        if not math.isfinite(z_score):
            raise ErrorDatoAntropometrico(
                "El cálculo LMS produjo un Z-score no finito."
            )

        if not (
            self.Z_SCORE_MINIMO_TECNICO
            <= z_score
            <= self.Z_SCORE_MAXIMO_TECNICO
        ):
            raise ErrorDatoAntropometrico(
                "El Z-score calculado está fuera del rango técnico "
                "permitido. Verifique las unidades, la edad, el sexo y "
                "los parámetros LMS utilizados."
            )