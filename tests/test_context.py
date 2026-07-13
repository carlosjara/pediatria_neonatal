"""Pruebas de integración para el contexto de servicios."""

from pediatria_neonatal.application.context import (
    ServiceContext,
    create_service_context,
)
from pediatria_neonatal.services.antropometria import CalculadoraAntropometrica
from pediatria_neonatal.services.neonatal import CalculadoraNeonatal
from pediatria_neonatal.services.zscore import CalculadoraZScore
from pediatria_neonatal.clinical.evaluacion import EvaluadorCrecimiento


class TestServiceContext:
    """Pruebas para la creación del contexto de servicios."""

    def test_create_service_context(self) -> None:
        """El contexto crea todas las dependencias."""
        context = create_service_context()

        assert isinstance(context, ServiceContext)
        assert isinstance(context.antropometria, CalculadoraAntropometrica)
        assert isinstance(context.neonatal, CalculadoraNeonatal)
        assert isinstance(context.zscore, CalculadoraZScore)
        assert isinstance(context.evaluador, EvaluadorCrecimiento)

    def test_context_is_frozen(self) -> None:
        """El contexto es inmutable."""
        context = create_service_context()

        try:
            context.antropometria = None
            assert False, "Debería fallar al modificar"
        except AttributeError:
            pass
