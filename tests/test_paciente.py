"""Pruebas unitarias para la entidad Paciente."""

from datetime import date

import pytest

from pediatria_neonatal.domain.paciente import DatosNeonatales, Paciente
from pediatria_neonatal.domain.models import Sexo
from pediatria_neonatal.domain.exceptions import ErrorEdadGestacional


class TestDatosNeonatales:
    """Pruebas para la validación de datos neonatales."""

    def test_crear_datos_neonatales_validos(self) -> None:
        """Datos neonatales válidos."""
        datos = DatosNeonatales(
            edad_gestacional_semanas=38,
            edad_gestacional_dias=3,
            peso_nacimiento_kg=3.2,
        )
        assert datos.edad_gestacional_semanas == 38
        assert datos.edad_gestacional_dias == 3
        assert datos.peso_nacimiento_kg == 3.2

    def test_edad_gestacional_total_dias(self) -> None:
        """Cálculo de edad gestacional total en días."""
        datos = DatosNeonatales(
            edad_gestacional_semanas=38,
            edad_gestacional_dias=3,
        )
        assert datos.edad_gestacional_total_dias == 38 * 7 + 3

    def test_es_prematuro(self) -> None:
        """Detección de prematuridad (< 37 semanas)."""
        prematuro = DatosNeonatales(edad_gestacional_semanas=32)
        termino = DatosNeonatales(edad_gestacional_semanas=40)

        assert prematuro.es_prematuro is True
        assert termino.es_prematuro is False

    def test_edad_gestacional_invalida(self) -> None:
        """Edad gestacional fuera de rango."""
        with pytest.raises(ErrorEdadGestacional):
            DatosNeonatales(edad_gestacional_semanas=20)


class TestPaciente:
    """Pruebas para la entidad Paciente."""

    def test_crear_paciente_valido(self) -> None:
        """Paciente con datos completos."""
        datos = DatosNeonatales(
            edad_gestacional_semanas=39,
            peso_nacimiento_kg=3.5,
        )
        paciente = Paciente(
            nombre="Juan Pérez",
            sexo=Sexo.MASCULINO,
            fecha_nacimiento=date(2024, 1, 15),
            datos_neonatales=datos,
        )
        assert paciente.nombre == "Juan Pérez"
        assert paciente.sexo == Sexo.MASCULINO
        assert paciente.fecha_nacimiento == date(2024, 1, 15)

    def test_nombre_vacio(self) -> None:
        """Nombre vacío debe fallar."""
        datos = DatosNeonatales(edad_gestacional_semanas=39)
        with pytest.raises(ValueError):
            Paciente(
                nombre="   ",
                sexo=Sexo.FEMENINO,
                fecha_nacimiento=date(2024, 1, 15),
                datos_neonatales=datos,
            )

    def test_normalizar_sexo(self) -> None:
        """Sexo se normaliza desde texto."""
        datos = DatosNeonatales(edad_gestacional_semanas=39)
        paciente = Paciente(
            nombre="María",
            sexo="femenino",
            fecha_nacimiento=date(2024, 1, 15),
            datos_neonatales=datos,
        )
        assert paciente.sexo == Sexo.FEMENINO
