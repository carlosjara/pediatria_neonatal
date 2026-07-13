"""Pruebas unitarias para el servicio neonatal."""

from datetime import date

import pytest

from pediatria_neonatal.services.neonatal import CalculadoraNeonatal
from pediatria_neonatal.domain.exceptions import ErrorEdadGestacional, ErrorFecha


class TestCalculadoraNeonatal:
    """Pruebas para el cálculo de edad corregida."""

    def setup_method(self) -> None:
        self.calculadora = CalculadoraNeonatal()

    def test_edad_corregida_prematuro(self) -> None:
        """Prematuro de 32 semanas, medición a los 56 días."""
        resultado = self.calculadora.calcular_edad_corregida(
            fecha_nacimiento=date(2024, 1, 1),
            fecha_medicion=date(2024, 2, 26),
            eg_semanas=32,
            eg_dias=0,
        )
        assert resultado.edad_cronologica_dias == 56
        assert resultado.prematuridad_dias == 56
        assert resultado.edad_corregida_total_dias == 0

    def test_edad_corregida_termino(self) -> None:
        """Nacido a término (40 semanas), sin corrección."""
        resultado = self.calculadora.calcular_edad_corregida(
            fecha_nacimiento=date(2024, 1, 1),
            fecha_medicion=date(2024, 2, 1),
            eg_semanas=40,
            eg_dias=0,
        )
        assert resultado.prematuridad_dias == 0
        assert resultado.edad_corregida_total_dias == 31

    def test_edad_gestacional_invalida(self) -> None:
        """Edad gestacional menor a 22 semanas."""
        with pytest.raises(ErrorEdadGestacional):
            self.calculadora.calcular_edad_corregida(
                fecha_nacimiento=date(2024, 1, 1),
                fecha_medicion=date(2024, 2, 1),
                eg_semanas=20,
                eg_dias=0,
            )

    def test_fecha_medicion_anterior_nacimiento(self) -> None:
        """Fecha de medición anterior al nacimiento."""
        with pytest.raises(ErrorFecha):
            self.calculadora.calcular_edad_corregida(
                fecha_nacimiento=date(2024, 2, 1),
                fecha_medicion=date(2024, 1, 1),
                eg_semanas=38,
                eg_dias=0,
            )
