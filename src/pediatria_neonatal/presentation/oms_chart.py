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
    view_x_min: float
    view_x_max: float

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

    @property
    def visible_y_values(self) -> tuple[float, ...]:
        """Valores y dentro del rango enfocado, incluyendo el paciente."""
        values = [
            point.y
            for curve in self.curves
            for point in curve.points
            if self.view_x_min <= point.x <= self.view_x_max
        ]
        values.append(self.patient_y)
        return tuple(values)


AGE_BASED_INDICATORS = {
    IndicadorCrecimiento.IMC_PARA_EDAD,
    IndicadorCrecimiento.PESO_PARA_EDAD,
    IndicadorCrecimiento.LONGITUD_PARA_EDAD,
    IndicadorCrecimiento.TALLA_PARA_EDAD,
    IndicadorCrecimiento.PERIMETRO_CEFALICO_PARA_EDAD,
}

MEASURE_BASED_INDICATORS = {
    IndicadorCrecimiento.PESO_PARA_LONGITUD,
    IndicadorCrecimiento.PESO_PARA_TALLA,
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
    measure_cm: int | float | None = None,
    repository: LMSRepository | None = None,
) -> OmsChartModel | None:
    """Construye curvas OMS para indicadores por edad o por longitud/talla."""

    try:
        growth_indicator = IndicadorCrecimiento(indicator_key)
    except ValueError:
        return None

    if growth_indicator in AGE_BASED_INDICATORS:
        return _build_age_based_chart_model(
            growth_indicator=growth_indicator,
            indicator=indicator,
            sex=sex,
            age_days=age_days,
            repository=repository,
        )

    if growth_indicator in MEASURE_BASED_INDICATORS:
        return _build_measure_based_chart_model(
            growth_indicator=growth_indicator,
            indicator=indicator,
            sex=sex,
            measure_cm=measure_cm,
            repository=repository,
        )

    return None


def _build_age_based_chart_model(
    *,
    growth_indicator: IndicadorCrecimiento,
    indicator: dict[str, object],
    sex: str | Sexo,
    age_days: int | float | None,
    repository: LMSRepository | None,
) -> OmsChartModel | None:
    """Construye modelo para curvas dependientes de edad."""

    if age_days is None:
        return None

    try:
        age = max(0, int(round(float(age_days))))
    except (TypeError, ValueError):
        return None

    repository = repository or LMSRepository()
    return _build_curve_model(
        growth_indicator=growth_indicator,
        indicator=indicator,
        sex=sex,
        patient_x=age / DAYS_PER_MONTH,
        x_label="Edad (meses)",
        sample_values=_sample_age_days(age),
        view_x_range=_age_view_range(age / DAYS_PER_MONTH),
        lookup=lambda sample: repository.obtener_por_edad(
            indicador=growth_indicator,
            sexo=sex,
            edad_dias=int(sample),
        ),
        point_x=lambda sample: float(sample) / DAYS_PER_MONTH,
    )


def _build_measure_based_chart_model(
    *,
    growth_indicator: IndicadorCrecimiento,
    indicator: dict[str, object],
    sex: str | Sexo,
    measure_cm: int | float | None,
    repository: LMSRepository | None,
) -> OmsChartModel | None:
    """Construye modelo para curvas dependientes de longitud/talla."""

    if measure_cm is None:
        return None

    try:
        measure = float(measure_cm)
    except (TypeError, ValueError):
        return None

    repository = repository or LMSRepository()
    label = (
        "Longitud (cm)"
        if growth_indicator == IndicadorCrecimiento.PESO_PARA_LONGITUD
        else "Talla (cm)"
    )
    return _build_curve_model(
        growth_indicator=growth_indicator,
        indicator=indicator,
        sex=sex,
        patient_x=measure,
        x_label=label,
        sample_values=_sample_measure_cm(growth_indicator, measure),
        view_x_range=_measure_view_range(growth_indicator, measure),
        lookup=lambda sample: repository.obtener_por_medida(
            indicador=growth_indicator,
            sexo=sex,
            medida_cm=float(sample),
        ),
        point_x=float,
    )


def _build_curve_model(
    *,
    growth_indicator: IndicadorCrecimiento,
    indicator: dict[str, object],
    sex: str | Sexo,
    patient_x: float,
    x_label: str,
    sample_values: tuple[int | float, ...],
    view_x_range: tuple[float, float],
    lookup,
    point_x,
) -> OmsChartModel | None:
    """Construye curvas percentilares desde una función LMS."""

    try:
        Sexo.normalizar(sex)
        value = float(indicator["valor"])
    except (ErrorTablaLMS, KeyError, TypeError, ValueError):
        return None

    curves = []

    for label, z_score, color in CURVE_DEFINITIONS:
        points = []
        for sample in sample_values:
            try:
                lms = lookup(sample)
            except ErrorTablaLMS:
                continue

            points.append(
                OmsChartPoint(
                    x=point_x(sample),
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
        x_label=x_label,
        y_label=unit,
        patient_x=patient_x,
        patient_y=value,
        patient_label=f"{value:.2f} {unit}".strip(),
        z_score_text=str(indicator.get("z_score_texto") or ""),
        percentile_text=str(indicator.get("percentil_texto") or ""),
        curves=tuple(curves),
        view_x_min=view_x_range[0],
        view_x_max=view_x_range[1],
    )


def _sample_age_days(patient_age_days: int) -> tuple[int, ...]:
    """Devuelve puntos suficientes para curvas suaves en edades pequeñas."""

    max_age = max(60 * DAYS_PER_MONTH, patient_age_days)
    return tuple(
        int(round(day))
        for day in range(0, int(max_age) + 1, 15)
    )


def _sample_measure_cm(
    indicator: IndicadorCrecimiento,
    patient_measure_cm: float,
) -> tuple[float, ...]:
    """Devuelve puntos de longitud/talla dentro del rango OMS disponible."""

    if indicator == IndicadorCrecimiento.PESO_PARA_LONGITUD:
        min_cm, max_cm = 45.0, 110.0
    else:
        min_cm, max_cm = 65.0, 120.0

    max_cm = max(max_cm, min(max(patient_measure_cm, min_cm), max_cm))
    steps = int(round((max_cm - min_cm) / 1.0)) + 1
    return tuple(round(min_cm + index, 1) for index in range(steps))


def _age_view_range(patient_months: float) -> tuple[float, float]:
    """Rango visible por edad para facilitar lectura en lactantes."""

    if patient_months <= 6:
        return 0.0, 6.0
    if patient_months <= 12:
        return 0.0, 12.0
    if patient_months <= 24:
        return 0.0, 24.0
    return 0.0, max(60.0, patient_months)


def _measure_view_range(
    indicator: IndicadorCrecimiento,
    patient_measure_cm: float,
) -> tuple[float, float]:
    """Rango visible por longitud/talla centrado alrededor del paciente."""

    if indicator == IndicadorCrecimiento.PESO_PARA_LONGITUD:
        min_cm, max_cm = 45.0, 110.0
    else:
        min_cm, max_cm = 65.0, 120.0

    window = 12.0
    start = max(min_cm, patient_measure_cm - window / 2)
    end = min(max_cm, patient_measure_cm + window / 2)

    if end - start < window:
        if start == min_cm:
            end = min(max_cm, start + window)
        else:
            start = max(min_cm, end - window)

    return start, end


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
