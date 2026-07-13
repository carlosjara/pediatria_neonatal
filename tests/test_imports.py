"""Pruebas de importación correcta del paquete."""


def test_import_main_package() -> None:
    """El paquete principal se importa correctamente."""
    import pediatria_neonatal
    assert pediatria_neonatal is not None


def test_import_app() -> None:
    """El módulo app se importa correctamente."""
    from pediatria_neonatal.app import main, PediatriaNeonatalApp
    assert main is not None
    assert PediatriaNeonatalApp is not None


def test_import_domain() -> None:
    """Los modelos de dominio se importan correctamente."""
    from pediatria_neonatal.domain.paciente import Paciente, DatosNeonatales
    from pediatria_neonatal.domain.models import Sexo
    assert Paciente is not None
    assert DatosNeonatales is not None
    assert Sexo is not None


def test_import_services() -> None:
    """Los servicios se importan correctamente."""
    from pediatria_neonatal.services.antropometria import CalculadoraAntropometrica
    from pediatria_neonatal.services.neonatal import CalculadoraNeonatal
    from pediatria_neonatal.services.zscore import CalculadoraZScore
    assert CalculadoraAntropometrica is not None
    assert CalculadoraNeonatal is not None
    assert CalculadoraZScore is not None


def test_import_application() -> None:
    """Los módulos de aplicación se importan correctamente."""
    from pediatria_neonatal.application.context import create_service_context
    from pediatria_neonatal.application.state import AppState
    from pediatria_neonatal.application.navigator import Navigator
    assert create_service_context is not None
    assert AppState is not None
    assert Navigator is not None
