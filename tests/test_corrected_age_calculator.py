"""Pruebas de la calculadora efímera de edad corregida."""

import pytest

from pediatria_neonatal.controllers.corrected_age_calculator_controller import (
    CorrectedAgeCalculatorController,
    _format_age_from_days,
)
from pediatria_neonatal.services.neonatal import CalculadoraNeonatal


def test_formatea_edad_corregida_compacta() -> None:
    assert _format_age_from_days(0) == "0D"
    assert _format_age_from_days(35) == "1M, 5D (5S, 0D)"
    assert _format_age_from_days(-1) == "Antes de término"


def test_parse_int_requiere_valor() -> None:
    controller = CorrectedAgeCalculatorController(
        neonatal=CalculadoraNeonatal(),
        on_back_home=lambda: None,
    )

    with pytest.raises(ValueError):
        controller._parse_int("", "semanas")

    assert controller._parse_int("32", "semanas") == 32
