from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class AppState:
    """Estado temporal compartido por las pantallas."""

    paciente_actual: Any | None = None
    medicion_actual: Any | None = None
    resultados_actuales: dict[str, Any] = field(default_factory=dict)
    historial_mediciones: list[dict[str, Any]] = field(default_factory=list)

    def guardar_en_historial(self) -> None:
        """Guarda la medición actual en el historial."""
        if self.paciente_actual is None or not self.resultados_actuales:
            return

        imc_data = self.resultados_actuales.get("imc", {})
        edad_corregida = self.resultados_actuales.get("edad_corregida", {})

        es_prematuro = self.paciente_actual.es_prematuro

        entrada = {
            "fecha": date.today().isoformat(),
            "paciente_nombre": self.paciente_actual.nombre,
            "paciente_sexo": self.paciente_actual.sexo.value,
            "paciente_fecha_nacimiento": self.paciente_actual.fecha_nacimiento.isoformat(),
            "paciente_datos_neonatales": {
                "edad_gestacional_semanas": self.paciente_actual.datos_neonatales.edad_gestacional_semanas,
                "edad_gestacional_dias": self.paciente_actual.datos_neonatales.edad_gestacional_dias,
                "peso_nacimiento_kg": self.paciente_actual.datos_neonatales.peso_nacimiento_kg,
                "talla_nacimiento_cm": self.paciente_actual.datos_neonatales.talla_nacimiento_cm,
                "perimetro_cefalico_nacimiento_cm": self.paciente_actual.datos_neonatales.perimetro_cefalico_nacimiento_cm,
            },
            "imc": imc_data.get("valor", 0),
            "clasificacion": imc_data.get("clasificacion", ""),
            "severidad": imc_data.get("severidad", "normal"),
            "edad_texto": self.resultados_actuales.get(
                "edad_cronologica_texto", ""
            ),
            "es_prematuro": es_prematuro,
            "edad_corregida_texto": self.resultados_actuales.get(
                "edad_corregida_texto", ""
            )
            if es_prematuro
            else "",
            # Guardar clasificación de prematuro tardío si aplica
            "clasificacion_prematuro": self.resultados_actuales.get(
                "clasificacion_prematuro", ""
            )
            if es_prematuro
            else "",
            # Guardar datos completos para vista detallada
            "resultados_completos": self.resultados_actuales.copy(),
        }

        self.historial_mediciones.insert(0, entrada)