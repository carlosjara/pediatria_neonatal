"""Modelos de presentación para curvas OMS 2006 en pantalla."""

from __future__ import annotations

import math
from dataclasses import dataclass

from pediatria_neonatal.data.lms_repository import LMSRepository
from pediatria_neonatal.domain.exceptions import ErrorTablaLMS
from pediatria_neonatal.domain.lms import IndicadorCrecimiento, ParametrosLMS
from pediatria_neonatal.domain.models import Sexo

DAYS_PER_MONTH = 30.4375


@dataclass(frozen=True, slots=True)
class OmsChartPoint:
    """Punto de una curva OMS."""

    x: float
    y: float


@dataclass(frozen=True, slots=True)
class OmsChartCurve:
    """Curva percentilar calculada desde LMS."""

    label: str
    z_score: float
    color: str
    points: tuple[OmsChartPoint, ...]


@dataclass(frozen=True, slots=True)
class OmsChartModel:
    """Datos listos para dibujar una gráfica OMS 2006."""

    title: str
    x_label: str
    y_label: str
    patient_x: float
    patient_y: float
    patient_label: str
    z_score_text: str
    percentile_text: str
    curves: tuple[OmsChartCurve, ...]

    @property
    def x_values(self) -> tuple[float, ...]:
        """Valores x de todas las curvas y el punto del paciente."""
        values = [point.x for curve in self.curves for point in curve.points]
        values.append(self.patient_x)
        return tuple(values)

    @property
    def y_values(self) -> tuple[float, ...]:
        """Valores y de todas las curvas y el punto del paciente."""
        values = [point.y for curve in self.curves for point in curve.points]
        values.append(self.patient_y)
        return tuple(values)


AGE_BASED_INDICATORS = {
    IndicadorCrecimiento.IMC_PARA_EDAD,
    IndicadorCrecimiento.PESO_PARA_EDAD,
    IndicadorCrecimiento.LONGITUD_PARA_EDAD,
    IndicadorCrecimiento.TALLA_PARA_EDAD,
    IndicadorCrecimiento.PERIMETRO_CEFALICO_PARA_EDAD,
}

CURVE_DEFINITIONS = (
    ("P1", -2.33, "#60A5FA"),
    ("P3", -1.88, "#93C5FD"),
    ("P15", -1.04, "#86EFAC"),
    ("P50", 0.0, "#22C55E"),
    ("P85", 1.04, "#FDE68A"),
    ("P97", 1.88, "#FDBA74"),
    ("P99", 2.33, "#F87171"),
)


def build_oms_chart_model(
    *,
    indicator_key: str,
    indicator: dict[str, object],
    sex: str | Sexo,
    age_days: int | float | None,
    repository: LMSRepository | None = None,
) -> OmsChartModel | None:
    """Construye curvas OMS para indicadores dependientes de edad."""

    if age_days is None:
        return None

    try:
        growth_indicator = IndicadorCrecimiento(indicator_key)
    except ValueError:
        return None

    if growth_indicator not in AGE_BASED_INDICATORS:
        return None

    try:
        normalized_sex = Sexo.normalizar(sex)
        age = max(0, int(round(float(age_days))))
        value = float(indicator["valor"])
    except (ErrorTablaLMS, KeyError, TypeError, ValueError):
        return None

    repository = repository or LMSRepository()
    sample_ages = _sample_age_days(age)
    curves = []

    for label, z_score, color in CURVE_DEFINITIONS:
        points = []
        for sample_age in sample_ages:
            try:
                lms = repository.obtener_por_edad(
                    indicador=growth_indicator,
                    sexo=normalized_sex,
                    edad_dias=sample_age,
                )
            except ErrorTablaLMS:
                continue

            points.append(
                OmsChartPoint(
                    x=sample_age / DAYS_PER_MONTH,
                    y=_measurement_from_lms(lms.parametros, z_score),
                )
            )

        if points:
            curves.append(
                OmsChartCurve(
                    label=label,
                    z_score=z_score,
                    color=color,
                    points=tuple(points),
                )
            )

    if not curves:
        return None

    unit = str(indicator.get("unidad") or "")
    return OmsChartModel(
        title=f"{indicator.get('nombre', 'Indicador OMS')} (OMS 2006)",
        x_label="Edad (meses)",
        y_label=unit,
        patient_x=age / DAYS_PER_MONTH,
        patient_y=value,
        patient_label=f"{value:.2f} {unit}".strip(),
        z_score_text=str(indicator.get("z_score_texto") or ""),
        percentile_text=str(indicator.get("percentil_texto") or ""),
        curves=tuple(curves),
    )


def _sample_age_days(patient_age_days: int) -> tuple[int, ...]:
    """Devuelve puntos mensuales suficientes para cubrir 0 a 60 meses."""

    max_age = max(60 * DAYS_PER_MONTH, patient_age_days)
    return tuple(
        int(round(month * DAYS_PER_MONTH))
        for month in range(0, int(max_age / DAYS_PER_MONTH) + 1)
    )


def _measurement_from_lms(lms: ParametrosLMS, z_score: float) -> float:
    """Convierte un Z-score a valor antropométrico usando LMS."""

    l_value = lms.lambda_box_cox
    m_value = lms.mediana
    s_value = lms.coeficiente_variacion

    if abs(l_value) < 1e-9:
        return m_value * math.exp(s_value * z_score)

    base = 1 + l_value * s_value * z_score
    if base <= 0:
        return 0
    return m_value * math.pow(base, 1 / l_value)
