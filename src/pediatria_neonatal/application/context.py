from dataclasses import dataclass

from pediatria_neonatal.clinical.evaluacion import EvaluadorCrecimiento
from pediatria_neonatal.services.antropometria import CalculadoraAntropometrica
from pediatria_neonatal.services.neonatal import CalculadoraNeonatal
from pediatria_neonatal.services.zscore import CalculadoraZScore


@dataclass(frozen=True)
class ServiceContext:
    """Servicios disponibles para la aplicación."""

    antropometria: CalculadoraAntropometrica
    neonatal: CalculadoraNeonatal
    zscore: CalculadoraZScore
    evaluador: EvaluadorCrecimiento


def create_service_context() -> ServiceContext:
    """Construye las dependencias de la aplicación."""

    return ServiceContext(
        antropometria=CalculadoraAntropometrica(),
        neonatal=CalculadoraNeonatal(),
        zscore=CalculadoraZScore(),
        evaluador=EvaluadorCrecimiento(),
    )
