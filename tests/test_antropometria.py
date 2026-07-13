"""Pruebas unitarias para el servicio de antropometría."""

import pytest

from pediatria_neonatal.services.antropometria import CalculadoraAntropometrica
from pediatria_neonatal.domain.exceptions import ErrorDatoAntropometrico


class TestCalculadoraAntropometrica:
    """Pruebas para el cálculo de IMC."""

    def setup_method(self) -> None:
        self.calculadora = CalculadoraAntropometrica()

    def test_calcular_imc_valores_normales(self) -> None:
        """IMC = peso_kg / (talla_m)^2"""
        imc = self.calculadora.calcular_imc(peso_kg=70.0, talla_cm=175.0)
        esperado = 70.0 / (1.75**2)
        assert abs(imc - esperado) < 0.001

    def test_calcular_imc_neonato(self) -> None:
        """IMC de un recién nacido típico."""
        imc = self.calculadora.calcular_imc(peso_kg=3.5, talla_cm=50.0)
        esperado = 3.5 / (0.50**2)
        assert abs(imc - esperado) < 0.001

    def test_calcular_imc_peso_invalido(self) -> None:
        """Peso fuera de rango técnico."""
        with pytest.raises(ErrorDatoAntropometrico):
            self.calculadora.calcular_imc(peso_kg=0.1, talla_cm=50.0)

    def test_calcular_imc_talla_invalida(self) -> None:
        """Talla fuera de rango técnico."""
        with pytest.raises(ErrorDatoAntropometrico):
            self.calculadora.calcular_imc(peso_kg=3.5, talla_cm=10.0)

    def test_calcular_imc_peso_negativo(self) -> None:
        """Peso negativo debe fallar."""
        with pytest.raises(ErrorDatoAntropometrico):
            self.calculadora.calcular_imc(peso_kg=-5.0, talla_cm=50.0)
