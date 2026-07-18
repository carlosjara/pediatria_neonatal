"""Presentación de resultados OMS 2006 para la pantalla de resumen."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pediatria_neonatal.domain.lms import IndicadorCrecimiento

COLOR_NORMAL = "#16A34A"
COLOR_RISK = "#CA8A04"
COLOR_OVERWEIGHT = "#D97706"
COLOR_DANGER = "#DC2626"
COLOR_LOW = "#1D4ED8"
COLOR_MUTED = "#6B7280"


@dataclass(frozen=True, slots=True)
class IndicatorSummaryCard:
    """Datos listos para pintar una tarjeta de indicador OMS."""

    key: str
    label: str
    z_score_text: str
    percentile_text: str
    classification_text: str
    semantic_color: str
    has_result: bool
    accessibility_label: str


@dataclass(frozen=True, slots=True)
class MainResultCard:
    """Datos listos para pintar el indicador principal."""

    title: str
    value_text: str
    unit: str
    z_score_text: str
    percentile_text: str
    classification_text: str
    semantic_color: str
    has_result: bool
    accessibility_label: str


@dataclass(frozen=True, slots=True)
class ResultsSummaryGrid:
    """Modelo completo de presentación para el resumen de resultados."""

    main_result: MainResultCard
    indicators: tuple[IndicatorSummaryCard, ...]


INDICATOR_ORDER: tuple[tuple[str, str], ...] = (
    ("weight_for_length_or_height", "Peso/Talla"),
    ("length_or_height_for_age", "Talla/Edad"),
    (IndicadorCrecimiento.PESO_PARA_EDAD.value, "Peso/Edad"),
    (
        IndicadorCrecimiento.PERIMETRO_CEFALICO_PARA_EDAD.value,
        "Per. Cef./Edad",
    ),
)


def build_results_summary(resultados: dict[str, Any]) -> ResultsSummaryGrid:
    """Construye el view-model de resumen desde resultados clínicos serializados."""

    oms_indicators = resultados.get("oms2006", {}).get("indicadores", {})
    imc = resultados.get("imc", {})

    main_result = _build_main_result(imc)
    cards = tuple(
        _build_indicator_card(
            key=key,
            label=label,
            indicators=oms_indicators,
        )
        for key, label in INDICATOR_ORDER
    )

    return ResultsSummaryGrid(
        main_result=main_result,
        indicators=cards,
    )


def format_z_score(value: Any) -> str:
    """Formatea z-score con signo y dos decimales."""

    if value is None:
        return "Sin datos"
    return f"{float(value):+.2f} DE"


def format_percentile(value: Any) -> str:
    """Formatea percentil para lectura clínica compacta."""

    if value is None:
        return "Sin datos"

    percentile = float(value)
    if percentile < 0.1:
        return "< P0.1"
    if percentile > 99.9:
        return "> P99.9"
    return f"P{percentile:.1f}"


def semantic_color_for_classification(
    classification: str,
    severity: str = "normal",
) -> str:
    """Selecciona color semántico estable sin depender del texto exacto."""

    normalized = _normalize(classification)
    severity_norm = _normalize(severity)

    if not normalized:
        return COLOR_MUTED
    if "obesidad" in normalized:
        return COLOR_DANGER
    if any(word in normalized for word in ("riesgo", "observacion")):
        return COLOR_RISK
    if "sobrepeso" in normalized:
        return COLOR_OVERWEIGHT
    if any(
        word in normalized
        for word in ("bajo", "baja", "delgadez", "desnutricion")
    ):
        return COLOR_LOW if severity_norm != "alta" else COLOR_DANGER
    if any(word in normalized for word in ("normal", "adecuado", "eutrofia")):
        return COLOR_NORMAL

    severity_color = {
        "normal": COLOR_NORMAL,
        "observacion": COLOR_RISK,
        "moderada": COLOR_OVERWEIGHT,
        "alta": COLOR_DANGER,
    }
    return severity_color.get(severity_norm, COLOR_MUTED)


def _build_main_result(imc: dict[str, Any]) -> MainResultCard:
    has_result = bool(imc)
    classification = str(imc.get("clasificacion") or "Sin datos")
    color = semantic_color_for_classification(
        classification,
        str(imc.get("severidad") or ""),
    )
    value = imc.get("valor")
    value_text = f"{float(value):.2f}" if value is not None else "--"
    z_score = imc.get("z_score_valor")
    percentile = imc.get("percentil_valor")

    return MainResultCard(
        title="IMC para la edad (OMS 2006)",
        value_text=value_text,
        unit="kg/m²",
        z_score_text=format_z_score(z_score),
        percentile_text=format_percentile(percentile),
        classification_text=classification,
        semantic_color=color,
        has_result=has_result,
        accessibility_label=(
            "IMC para la edad OMS 2006. "
            f"Valor {value_text} kg/m². "
            f"{format_z_score(z_score)}. "
            f"{format_percentile(percentile)}. "
            f"Clasificación {classification}."
        ),
    )


def _build_indicator_card(
    *,
    key: str,
    label: str,
    indicators: dict[str, dict[str, Any]],
) -> IndicatorSummaryCard:
    source_key = _resolve_indicator_key(key, indicators)
    item = indicators.get(source_key) if source_key else None

    if not item:
        return IndicatorSummaryCard(
            key=key,
            label=label,
            z_score_text="Sin datos",
            percentile_text="Sin datos",
            classification_text="Sin datos",
            semantic_color=COLOR_MUTED,
            has_result=False,
            accessibility_label=f"{label}. Sin datos disponibles.",
        )

    classification = str(item.get("clasificacion") or "Sin datos")
    z_score = item.get("z_score")
    percentile = item.get("percentil")
    z_score_text = format_z_score(z_score)
    percentile_text = format_percentile(percentile)

    return IndicatorSummaryCard(
        key=source_key,
        label=label,
        z_score_text=z_score_text,
        percentile_text=percentile_text,
        classification_text=classification,
        semantic_color=semantic_color_for_classification(
            classification,
            str(item.get("severidad") or ""),
        ),
        has_result=True,
        accessibility_label=(
            f"{label}. {z_score_text}. {percentile_text}. "
            f"Clasificación {classification}."
        ),
    )


def _resolve_indicator_key(
    key: str,
    indicators: dict[str, dict[str, Any]],
) -> str | None:
    if key != "weight_for_length_or_height":
        if key != "length_or_height_for_age":
            return key

        if IndicadorCrecimiento.LONGITUD_PARA_EDAD.value in indicators:
            return IndicadorCrecimiento.LONGITUD_PARA_EDAD.value
        if IndicadorCrecimiento.TALLA_PARA_EDAD.value in indicators:
            return IndicadorCrecimiento.TALLA_PARA_EDAD.value
        return None

    if IndicadorCrecimiento.PESO_PARA_LONGITUD.value in indicators:
        return IndicadorCrecimiento.PESO_PARA_LONGITUD.value
    if IndicadorCrecimiento.PESO_PARA_TALLA.value in indicators:
        return IndicadorCrecimiento.PESO_PARA_TALLA.value
    return None


def _normalize(value: str) -> str:
    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
        "ñ": "n",
    }
    normalized = value.strip().lower()
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    return normalized
