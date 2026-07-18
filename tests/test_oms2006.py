"""Pruebas del módulo antropométrico OMS 2006."""

from datetime import date

import pytest

from pediatria_neonatal.domain import DatosNeonatales, Paciente, Sexo
from pediatria_neonatal.domain.lms import (
    IndicadorCrecimiento,
    ParametrosLMS,
    ReferenciaCrecimiento,
)
from pediatria_neonatal.domain.paciente import MedicionAntropometrica
from pediatria_neonatal.services.oms2006 import EvaluadorOMS2006, PosicionMedicion
from pediatria_neonatal.services.zscore import CalculadoraZScore


def test_lms_valor_igual_mediana_es_z_cero() -> None:
    parametros = ParametrosLMS(
        referencia=ReferenciaCrecimiento.OMS_2006,
        indicador=IndicadorCrecimiento.PESO_PARA_EDAD,
        sexo=Sexo.MASCULINO,
        edad=365,
        unidad_edad="dias",
        lambda_box_cox=0.5,
        mediana=10.0,
        coeficiente_variacion=0.1,
    )

    resultado = CalculadoraZScore().calcular(10.0, parametros)

    assert resultado.z_score == pytest.approx(0.0)
    assert resultado.percentil == pytest.approx(50.0)


def test_lms_usa_log_cuando_l_es_cero() -> None:
    parametros = ParametrosLMS(
        referencia=ReferenciaCrecimiento.OMS_2006,
        indicador=IndicadorCrecimiento.PESO_PARA_EDAD,
        sexo=Sexo.MASCULINO,
        edad=365,
        unidad_edad="dias",
        lambda_box_cox=0.0,
        mediana=10.0,
        coeficiente_variacion=0.1,
    )

    resultado = CalculadoraZScore().calcular(11.0, parametros)

    assert resultado.z_score == pytest.approx(0.953101798, abs=1e-9)
    assert resultado.percentil == pytest.approx(82.97, abs=0.02)


def test_lms_usa_log_cuando_l_es_muy_cercano_a_cero() -> None:
    parametros = ParametrosLMS(
        referencia=ReferenciaCrecimiento.OMS_2006,
        indicador=IndicadorCrecimiento.PESO_PARA_EDAD,
        sexo=Sexo.MASCULINO,
        edad=365,
        unidad_edad="dias",
        lambda_box_cox=1e-12,
        mediana=10.0,
        coeficiente_variacion=0.1,
    )

    resultado = CalculadoraZScore().calcular(11.0, parametros)

    assert resultado.z_score == pytest.approx(0.953101798, abs=1e-9)


def test_normaliza_talla_de_pie_en_menor_de_24_meses() -> None:
    evaluador = EvaluadorOMS2006()

    medida = evaluador.normalizar_longitud_talla(
        edad_dias=365,
        medida_cm=72.3,
        posicion=PosicionMedicion.DE_PIE,
    )

    assert medida.valor_oms_cm == pytest.approx(73.0)
    assert medida.ajuste_cm == pytest.approx(0.7)
    assert medida.indicador_peso == IndicadorCrecimiento.PESO_PARA_LONGITUD


def test_normaliza_longitud_acostado_desde_24_meses() -> None:
    evaluador = EvaluadorOMS2006()

    medida = evaluador.normalizar_longitud_talla(
        edad_dias=800,
        medida_cm=86.7,
        posicion=PosicionMedicion.ACOSTADO,
    )

    assert medida.valor_oms_cm == pytest.approx(86.0)
    assert medida.ajuste_cm == pytest.approx(-0.7)
    assert medida.indicador_peso == IndicadorCrecimiento.PESO_PARA_TALLA


def test_caso_dorado_who_anthro_nina_365_dias() -> None:
    paciente = Paciente(
        nombre="Caso WHO Anthro",
        sexo=Sexo.FEMENINO,
        fecha_nacimiento=date(2025, 7, 13),
        datos_neonatales=DatosNeonatales(
            edad_gestacional_semanas=40,
            edad_gestacional_dias=0,
            peso_nacimiento_kg=3.2,
        ),
    )
    medicion = MedicionAntropometrica(
        fecha_medicion=date(2026, 7, 13),
        peso_kg=9.0,
        talla_cm=73.0,
        perimetro_cefalico_cm=45.0,
    )

    evaluacion = EvaluadorOMS2006().evaluar(
        paciente=paciente,
        medicion=medicion,
        posicion=PosicionMedicion.ACOSTADO,
    )

    wfl = evaluacion.obtener(IndicadorCrecimiento.PESO_PARA_LONGITUD)
    wfa = evaluacion.obtener(IndicadorCrecimiento.PESO_PARA_EDAD)
    lfa = evaluacion.obtener(IndicadorCrecimiento.LONGITUD_PARA_EDAD)
    bmifa = evaluacion.obtener(IndicadorCrecimiento.IMC_PARA_EDAD)
    hcfa = evaluacion.obtener(IndicadorCrecimiento.PERIMETRO_CEFALICO_PARA_EDAD)

    assert wfl is not None
    assert wfa is not None
    assert lfa is not None
    assert bmifa is not None
    assert hcfa is not None

    assert wfl.z_score == pytest.approx(0.29, abs=0.01)
    assert wfa.z_score == pytest.approx(0.05, abs=0.01)
    assert lfa.z_score == pytest.approx(-0.39, abs=0.01)
    assert bmifa.z_score == pytest.approx(0.36, abs=0.01)
    assert hcfa.z_score == pytest.approx(0.08, abs=0.01)

    assert wfl.percentil == pytest.approx(61.4, abs=0.1)
    assert wfa.percentil == pytest.approx(51.9, abs=0.1)
    assert lfa.percentil == pytest.approx(34.8, abs=0.1)
    assert bmifa.percentil == pytest.approx(64.1, abs=0.1)
    assert hcfa.percentil == pytest.approx(53.1, abs=0.1)
    assert evaluacion.tipo_edad_usada == "cronologica"
