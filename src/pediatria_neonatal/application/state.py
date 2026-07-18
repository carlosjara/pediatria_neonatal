from dataclasses import dataclass, field
from datetime import date
from typing import Any

from pediatria_neonatal.application.session_store import SessionStore
from pediatria_neonatal.domain.models import Sexo
from pediatria_neonatal.domain.paciente import (
    DatosNeonatales,
    MedicionAntropometrica,
    Paciente,
)


@dataclass
class AppState:
    """Estado temporal compartido por las pantallas."""

    paciente_actual: Any | None = None
    medicion_actual: Any | None = None
    resultados_actuales: dict[str, Any] = field(default_factory=dict)
    historial_mediciones: list[dict[str, Any]] = field(default_factory=list)
    pacientes_sesion: list[dict[str, Any]] = field(default_factory=list)
    session_store: SessionStore = field(default_factory=SessionStore)

    def iniciar_sesion_temporal(self) -> None:
        """Recrea la sesión temporal al iniciar la aplicación."""

        self.session_store.reset()
        self.pacientes_sesion = []

    def guardar_en_historial(self) -> None:
        """Guarda la medición actual en el historial."""
        if self.paciente_actual is None or not self.resultados_actuales:
            return

        imc_data = self.resultados_actuales.get("imc", {})
        es_prematuro = self.paciente_actual.es_prematuro

        datos_neonatales = self.paciente_actual.datos_neonatales

        entrada = {
            "fecha": date.today().isoformat(),
            "paciente_nombre": self.paciente_actual.nombre,
            "paciente_sexo": self.paciente_actual.sexo.value,
            "paciente_fecha_nacimiento": (
                self.paciente_actual.fecha_nacimiento.isoformat()
            ),
            "paciente_datos_neonatales": {
                "edad_gestacional_semanas": (
                    datos_neonatales.edad_gestacional_semanas
                ),
                "edad_gestacional_dias": datos_neonatales.edad_gestacional_dias,
                "peso_nacimiento_kg": datos_neonatales.peso_nacimiento_kg,
                "talla_nacimiento_cm": datos_neonatales.talla_nacimiento_cm,
                "perimetro_cefalico_nacimiento_cm": (
                    datos_neonatales.perimetro_cefalico_nacimiento_cm
                ),
            },
            "imc": imc_data.get("valor", 0),
            "clasificacion": imc_data.get("clasificacion", ""),
            "severidad": imc_data.get("severidad", "normal"),
            "edad_texto": self.resultados_actuales.get("edad_cronologica_texto", ""),
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
        self._guardar_paciente_sesion(entrada)

    def seleccionar_registro_sesion(self, index: int) -> bool:
        """Restaura paciente y resultados desde la sesión temporal."""

        try:
            registro = self.pacientes_sesion[index]
        except IndexError:
            return False

        self.paciente_actual = self._rehidratar_paciente(registro)
        self.resultados_actuales = registro.get("resultados_completos", {})
        self.medicion_actual = self._rehidratar_medicion(self.resultados_actuales)
        return self.paciente_actual is not None and bool(self.resultados_actuales)

    def seleccionar_ultimo_resultado(self) -> bool:
        """Restaura el resultado más reciente de la sesión temporal."""

        return self.seleccionar_registro_sesion(0)

    def _guardar_paciente_sesion(self, entrada_historial: dict[str, Any]) -> None:
        registro = entrada_historial.copy()
        registro["nombre"] = entrada_historial.get("paciente_nombre", "")
        registro["edad"] = entrada_historial.get("edad_texto", "")
        registro["edad_corregida"] = entrada_historial.get("edad_corregida_texto", "")

        self.pacientes_sesion = [
            item
            for item in self.pacientes_sesion
            if item.get("paciente_nombre") != registro.get("paciente_nombre")
        ]
        self.pacientes_sesion.insert(0, registro)
        self.session_store.save(self.pacientes_sesion)

    def _rehidratar_paciente(self, registro: dict[str, Any]) -> Paciente | None:
        datos = registro.get("paciente_datos_neonatales", {})
        try:
            return Paciente(
                nombre=str(registro.get("paciente_nombre", "")),
                sexo=Sexo.normalizar(str(registro.get("paciente_sexo", ""))),
                fecha_nacimiento=date.fromisoformat(
                    str(registro.get("paciente_fecha_nacimiento", ""))
                ),
                datos_neonatales=DatosNeonatales(
                    edad_gestacional_semanas=int(
                        datos.get("edad_gestacional_semanas", 40)
                    ),
                    edad_gestacional_dias=int(datos.get("edad_gestacional_dias", 0)),
                    peso_nacimiento_kg=datos.get("peso_nacimiento_kg"),
                    talla_nacimiento_cm=datos.get("talla_nacimiento_cm"),
                    perimetro_cefalico_nacimiento_cm=datos.get(
                        "perimetro_cefalico_nacimiento_cm"
                    ),
                ),
            )
        except (TypeError, ValueError):
            return None

    def _rehidratar_medicion(
        self,
        resultados: dict[str, Any],
    ) -> MedicionAntropometrica | None:
        medicion = resultados.get("medicion_actual", {})
        if not medicion:
            return None

        try:
            return MedicionAntropometrica(
                fecha_medicion=date.fromisoformat(str(medicion["fecha_medicion"])),
                peso_kg=medicion.get("peso_kg"),
                talla_cm=medicion.get("talla_cm"),
                perimetro_cefalico_cm=medicion.get("perimetro_cefalico_cm"),
            )
        except (KeyError, TypeError, ValueError):
            return None
