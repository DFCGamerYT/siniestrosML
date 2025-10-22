import logging
from fastapi import APIRouter, HTTPException, Depends, status
from ..services.prediction_service import MLPredictionService
from ..config import get_settings, Settings
from ..models.schemas import HealthStatus, HealthCheck, MetricsResponse, PrediccionMLRequest, PrediccionMLResponse

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/ml",
    tags=["Machine Learning Predictions"]
)

ml_service: MLPredictionService = None

def get_ml_service() -> MLPredictionService:

    if ml_service is None:
        logger.error("MLPredictionService no está inicializado en health router.")
        raise HTTPException(
            status_code=500,
            detail="Servicio de predicción no disponible."
        )
    return ml_service

@router.post("/predecir", response_model=PrediccionMLResponse, summary="Realizar una predicción de gravedad de siniestro")
async def predecir_siniestro(
    request: PrediccionMLRequest,
    service: MLPredictionService = Depends(get_ml_service),
    config: Settings = Depends(get_settings)
):
    try:
        logger.debug(f"Solicitud de predicción recibida: {request}")

        features = request.features
        resultado = service.predecir(features)

        if config.prediction_confidence_threshold:
            if resultado.confianza_porcentaje < config.prediction_confidence_threshold:
                logger.warning(f"Predicción con baja confianza: {resultado.confianza_porcentaje}")

        logger.info(f"Predicción realizada con éxito: {resultado}"
                    f"confianza resultado: {resultado.confianza_porcentaje}")

        return resultado
    
    except ValueError as ve:
        logger.error(f"Error de validación en la solicitud de predicción: {ve}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error de validación: {ve}"
        )
    
    except Exception as e:
        logger.error(f"Error al realizar la predicción: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al procesar la predicción."
        )