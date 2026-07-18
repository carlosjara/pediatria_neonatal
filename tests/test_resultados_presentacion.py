"""Pruebas del modelo de presentación del resumen de resultados."""

from pediatria_neonatal.presentation.resultados import (
    COLOR_DANGER,
    COLOR_MUTED,
    COLOR_NORMAL,
    COLOR_OVERWEIGHT,
    COLOR_RISK,
    build_results_summary,
    format_percentile,
    format_z_score,
    semantic_color_for_classification,
)


def test_formatea_z_score_con_signo_y_dos_decimales() -> None:
    assert format_z_score(1.234) == "+1.23 DE"
    assert format_z_score(-0.245) == "-0.24 DE"
    assert format_z_score(None) == "Sin datos"


def test_formatea_percentiles_extremos_y_normales() -> None:
    assert format_percentile(0.05) == "< P0.1"
    assert format_percentile(99.95) == "> P99.9"
    assert format_percentile(95.123) == "P95.1"
    assert format_percentile(None) == "Sin datos"


def test_selecciona_color_semantico_por_clasificacion() -> None:
    assert semantic_color_for_classification("Adecuado") == COLOR_NORMAL
    assert semantic_color_for_classification("Riesgo sobrepeso") == COLOR_RISK
    assert semantic_color_for_classification("Sobrepeso") == COLOR_OVERWEIGHT
    assert semantic_color_for_classification("Obesidad") == COLOR_DANGER
    assert semantic_color_for_classification("") == COLOR_MUTED


def test_construye_indicadores_en_orden_visual() -> None:
    summary = build_results_summary(
        {
            "imc": {
                "valor": 19.56,
                "z_score_valor": 2.23,
                "percentil_valor": 98.7,
                "clasificacion": "Sobrepeso",
                "severidad": "observacion",
            },
            "oms2006": {
                "indicadores": {
                    "weight_for_length": _indicator(1.65, 95.1, "Adecuado"),
                    "height_for_age": _indicator(-0.25, 40.1, "Adecuado"),
                    "weight_for_age": _indicator(1.2, 88.5, "Adecuado"),
                    "head_circumference_for_age": _indicator(
                        0.35,
                        63.7,
                        "Adecuado",
                    ),
                }
            },
        }
    )

    labels = [indicator.label for indicator in summary.indicators]

    assert labels == [
        "Peso/Talla",
        "Talla/Edad",
        "Peso/Edad",
        "Per. Cef./Edad",
    ]
    assert summary.indicators[0].z_score_text == "+1.65 DE"
    assert summary.indicators[1].z_score_text == "-0.25 DE"
    assert summary.main_result.classification_text == "Sobrepeso"


def test_indicador_incompleto_muestra_sin_datos() -> None:
    summary = build_results_summary(
        {
            "imc": {},
            "oms2006": {
                "indicadores": {
                    "weight_for_age": _indicator(1.2, 88.5, "Adecuado"),
                }
            },
        }
    )

    first_card = summary.indicators[0]

    assert first_card.label == "Peso/Talla"
    assert first_card.has_result is False
    assert first_card.z_score_text == "Sin datos"
    assert first_card.percentile_text == "Sin datos"
    assert first_card.classification_text == "Sin datos"
    assert first_card.semantic_color == COLOR_MUTED


def _indicator(
    z_score: float,
    percentile: float,
    classification: str,
) -> dict[str, object]:
    return {
        "z_score": z_score,
        "percentil": percentile,
        "clasificacion": classification,
        "severidad": "normal",
    }
