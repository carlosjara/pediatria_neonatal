from dataclasses import dataclass

from pediatria_neonatal.clinical.evaluacion import EvaluadorCrecimiento
from pediatria_neonatal.services.antropometria import CalculadoraAntropometrica
from pediatria_neonatal.data.lms_repository import LMSRepository
from pediatria_neonatal.services.neonatal import CalculadoraNeonatal
from pediatria_neonatal.services.oms2006 import EvaluadorOMS2006
from pediatria_neonatal.services.zscore import CalculadoraZScore


@dataclass(frozen=True)
class ServiceContext:
    """Servicios disponibles para la aplicación."""

    antropometria: CalculadoraAntropometrica
    neonatal: CalculadoraNeonatal
    zscore: CalculadoraZScore
    evaluador: EvaluadorCrecimiento
    lms_repository: LMSRepository
    oms2006: EvaluadorOMS2006


def create_service_context() -> ServiceContext:
    """Construye las dependencias de la aplicación."""

    lms_repository = LMSRepository()
    antropometria = CalculadoraAntropometrica()
    neonatal = CalculadoraNeonatal()
    zscore = CalculadoraZScore()
    evaluador = EvaluadorCrecimiento()

    return ServiceContext(
        antropometria=antropometria,
        neonatal=neonatal,
        zscore=zscore,
        evaluador=evaluador,
        lms_repository=lms_repository,
        oms2006=EvaluadorOMS2006(
            repository=lms_repository,
            neonatal=neonatal,
            antropometria=antropometria,
            zscore=zscore,
            evaluador=evaluador,
        ),
    )
