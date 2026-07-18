"""Pruebas del modelo de gráfica OMS 2006."""

from pediatria_neonatal.presentation.oms_chart import build_oms_chart_model


def test_build_oms_chart_model_generates_bmi_curves() -> None:
    model = build_oms_chart_model(
        indicator_key="bmi_for_age",
        indicator={
            "nombre": "IMC para la edad",
            "valor": 19.56,
            "unidad": "kg/m²",
            "z_score_texto": "+2.23 DE",
            "percentil_texto": "P98.7",
        },
        sex="M",
        age_days=150,
    )

    assert model is not None
    assert model.title == "IMC para la edad (OMS 2006)"
    assert model.patient_x > 0
    assert model.patient_y == 19.56
    assert model.view_x_min == 0.0
    assert model.view_x_max == 6.0
    assert [curve.label for curve in model.curves] == [
        "P1",
        "P3",
        "P15",
        "P50",
        "P85",
        "P97",
        "P99",
    ]
    assert all(curve.points for curve in model.curves)


def test_build_oms_chart_model_generates_weight_for_length_curves() -> None:
    model = build_oms_chart_model(
        indicator_key="weight_for_length",
        indicator={
            "nombre": "Peso para longitud",
            "valor": 6.9,
            "unidad": "kg",
            "z_score_texto": "+1.20 DE",
            "percentil_texto": "P88.5",
        },
        sex="M",
        age_days=150,
        measure_cm=56.0,
    )

    assert model is not None
    assert model.x_label == "Longitud (cm)"
    assert model.patient_x == 56.0
    assert model.patient_y == 6.9
    assert model.view_x_min == 50.0
    assert model.view_x_max == 62.0
    assert all(curve.points for curve in model.curves)
