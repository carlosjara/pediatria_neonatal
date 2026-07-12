"""Entidades principales para representar pacientes y mediciones clínicas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from pediatria_neonatal.domain.exceptions import (
    ErrorDatoAntropometrico,
    ErrorEdadGestacional,
    ErrorFecha,
)
from pediatria_neonatal.domain.models import Sexo

FechaCompatible = date | datetime | str


def normalizar_fecha(
    valor: FechaCompatible,
    *,
    nombre_campo: str,
) -> date:
    """Convierte un valor compatible a ``datetime.date``.

    Se aceptan:

    - ``date``
    - ``datetime``
    - texto en formato ISO ``YYYY-MM-DD``

    Parameters
    ----------
    valor:
        Fecha que se desea normalizar.

    nombre_campo:
        Nombre utilizado al construir los mensajes de error.

    Returns
    -------
    date
        Fecha normalizada.

    Raises
    ------
    ErrorFecha
        Si el tipo o formato de la fecha no es válido.
    """

    if isinstance(valor, datetime):
        return valor.date()

    if isinstance(valor, date):
        return valor

    if isinstance(valor, str):
        try:
            return date.fromisoformat(valor)
        except ValueError as exc:
            raise ErrorFecha(
                f"{nombre_campo} debe tener formato ISO YYYY-MM-DD."
            ) from exc

    raise ErrorFecha(
        f"{nombre_campo} debe ser date, datetime "
        "o texto ISO YYYY-MM-DD."
    )


def validar_numero_positivo_opcional(
    valor: float | None,
    *,
    nombre_campo: str,
) -> None:
    """Valida una medición clínica opcional mayor que cero."""

    if valor is None:
        return

    if isinstance(valor, bool) or not isinstance(valor, int | float):
        raise ErrorDatoAntropometrico(
            f"{nombre_campo} debe ser un número."
        )

    if valor <= 0:
        raise ErrorDatoAntropometrico(
            f"{nombre_campo} debe ser mayor que cero."
        )


@dataclass(frozen=True, slots=True)
class DatosNeonatales:
    """Información clínica registrada al momento del nacimiento.

    Attributes
    ----------
    edad_gestacional_semanas:
        Semanas completas de gestación al nacimiento.

    edad_gestacional_dias:
        Días adicionales de gestación, entre 0 y 6.

    peso_nacimiento_kg:
        Peso al nacimiento expresado en kilogramos.

    talla_nacimiento_cm:
        Talla al nacimiento expresada en centímetros.

    perimetro_cefalico_nacimiento_cm:
        Perímetro cefálico al nacimiento en centímetros.
    """

    edad_gestacional_semanas: int
    edad_gestacional_dias: int = 0
    peso_nacimiento_kg: float | None = None
    talla_nacimiento_cm: float | None = None
    perimetro_cefalico_nacimiento_cm: float | None = None

    EDAD_GESTACIONAL_MINIMA_SEMANAS = 22
    EDAD_GESTACIONAL_MAXIMA_SEMANAS = 42
    EDAD_GESTACIONAL_MAXIMA_DIAS = 6

    def __post_init__(self) -> None:
        """Valida los datos gestacionales y antropométricos del nacimiento."""

        self._validar_edad_gestacional()

        validar_numero_positivo_opcional(
            self.peso_nacimiento_kg,
            nombre_campo="peso_nacimiento_kg",
        )
        validar_numero_positivo_opcional(
            self.talla_nacimiento_cm,
            nombre_campo="talla_nacimiento_cm",
        )
        validar_numero_positivo_opcional(
            self.perimetro_cefalico_nacimiento_cm,
            nombre_campo="perimetro_cefalico_nacimiento_cm",
        )

    @property
    def edad_gestacional_total_dias(self) -> int:
        """Retorna la edad gestacional total expresada en días."""

        return (
            self.edad_gestacional_semanas * 7
            + self.edad_gestacional_dias
        )

    @property
    def es_prematuro(self) -> bool:
        """Indica si el nacimiento ocurrió antes de 37 semanas."""

        return self.edad_gestacional_total_dias < 37 * 7

    def _validar_edad_gestacional(self) -> None:
        """Valida que la edad gestacional esté entre 22+0 y 42+6."""

        semanas = self.edad_gestacional_semanas
        dias = self.edad_gestacional_dias

        if isinstance(semanas, bool) or not isinstance(semanas, int):
            raise ErrorEdadGestacional(
                "edad_gestacional_semanas debe ser un número entero."
            )

        if isinstance(dias, bool) or not isinstance(dias, int):
            raise ErrorEdadGestacional(
                "edad_gestacional_dias debe ser un número entero."
            )

        if not 0 <= dias <= self.EDAD_GESTACIONAL_MAXIMA_DIAS:
            raise ErrorEdadGestacional(
                "edad_gestacional_dias debe estar entre 0 y 6."
            )

        edad_total_dias = semanas * 7 + dias
        edad_minima_dias = (
            self.EDAD_GESTACIONAL_MINIMA_SEMANAS * 7
        )
        edad_maxima_dias = (
            self.EDAD_GESTACIONAL_MAXIMA_SEMANAS * 7
            + self.EDAD_GESTACIONAL_MAXIMA_DIAS
        )

        if not edad_minima_dias <= edad_total_dias <= edad_maxima_dias:
            raise ErrorEdadGestacional(
                "La edad gestacional debe estar entre "
                "22+0 y 42+6 semanas."
            )


@dataclass(frozen=True, slots=True)
class MedicionAntropometrica:
    """Representa una medición antropométrica realizada al paciente.

    Los campos son opcionales porque una consulta puede registrar solo
    algunas mediciones. Sin embargo, debe proporcionarse por lo menos una.

    Attributes
    ----------
    fecha_medicion:
        Fecha en la que se tomaron las medidas.

    peso_kg:
        Peso expresado en kilogramos.

    talla_cm:
        Longitud o talla expresada en centímetros.

    perimetro_cefalico_cm:
        Perímetro cefálico expresado en centímetros.
    """

    fecha_medicion: date
    peso_kg: float | None = None
    talla_cm: float | None = None
    perimetro_cefalico_cm: float | None = None

    def __post_init__(self) -> None:
        """Normaliza la fecha y valida las mediciones registradas."""

        fecha_normalizada = normalizar_fecha(
            self.fecha_medicion,
            nombre_campo="fecha_medicion",
        )

        object.__setattr__(
            self,
            "fecha_medicion",
            fecha_normalizada,
        )

        if (
            self.peso_kg is None
            and self.talla_cm is None
            and self.perimetro_cefalico_cm is None
        ):
            raise ErrorDatoAntropometrico(
                "Debe proporcionar al menos una medición antropométrica."
            )

        validar_numero_positivo_opcional(
            self.peso_kg,
            nombre_campo="peso_kg",
        )
        validar_numero_positivo_opcional(
            self.talla_cm,
            nombre_campo="talla_cm",
        )
        validar_numero_positivo_opcional(
            self.perimetro_cefalico_cm,
            nombre_campo="perimetro_cefalico_cm",
        )


@dataclass(frozen=True, slots=True)
class Paciente:
    """Entidad que representa la información básica de un paciente.

    El paciente contiene información relativamente estable. Las mediciones
    antropométricas se representan por separado porque pueden existir varias
    a lo largo del tiempo.

    Attributes
    ----------
    nombre:
        Nombre o identificador visible del paciente.

    sexo:
        Sexo requerido para seleccionar las tablas antropométricas.

    fecha_nacimiento:
        Fecha de nacimiento.

    datos_neonatales:
        Información gestacional y antropométrica del nacimiento.

    identificador:
        Identificador opcional para integraciones futuras.
    """

    nombre: str
    sexo: Sexo
    fecha_nacimiento: date
    datos_neonatales: DatosNeonatales
    identificador: str | None = None

    def __post_init__(self) -> None:
        """Normaliza y valida los datos principales del paciente."""

        nombre_normalizado = self.nombre.strip()

        if not nombre_normalizado:
            raise ValueError(
                "El nombre del paciente no puede estar vacío."
            )

        fecha_normalizada = normalizar_fecha(
            self.fecha_nacimiento,
            nombre_campo="fecha_nacimiento",
        )

        sexo_normalizado = Sexo.normalizar(self.sexo)

        object.__setattr__(
            self,
            "nombre",
            nombre_normalizado,
        )
        object.__setattr__(
            self,
            "fecha_nacimiento",
            fecha_normalizada,
        )
        object.__setattr__(
            self,
            "sexo",
            sexo_normalizado,
        )

        if self.identificador is not None:
            identificador_normalizado = self.identificador.strip()

            if not identificador_normalizado:
                raise ValueError(
                    "El identificador no puede contener solo espacios."
                )

            object.__setattr__(
                self,
                "identificador",
                identificador_normalizado,
            )

    @property
    def es_prematuro(self) -> bool:
        """Indica si el paciente nació antes de las 37 semanas."""

        return self.datos_neonatales.es_prematuro

    def validar_fecha_medicion(
        self,
        fecha_medicion: FechaCompatible,
    ) -> date:
        """Valida que una medición no sea anterior al nacimiento."""

        fecha_normalizada = normalizar_fecha(
            fecha_medicion,
            nombre_campo="fecha_medicion",
        )

        if fecha_normalizada < self.fecha_nacimiento:
            raise ErrorFecha(
                "La fecha de medición no puede ser anterior "
                "a la fecha de nacimiento."
            )

        return fecha_normalizada