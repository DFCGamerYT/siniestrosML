import logging
from fastapi import APIRouter, HTTPException, Depends
from ..services.prediction_service import MLPredictionService
from ..config import get_settings, Settings
from ..models.schemas import HealthStatus, HealthCheck, MetricsResponse
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/health",
    tags=["health"]
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

@router.get("/", summary="Check de salud del servicio")
async def health_check(
    service: MLPredictionService = Depends(get_ml_service),
    config: Settings = Depends(get_settings)
):
    try:
        is_healthy = service.health_check()
        metricas = service.get_metricas()

        if is_healthy:
            health_status = HealthStatus.HEALTHY
            logger.debug("Health check exitoso.")
        else:
            health_status = HealthStatus.UNHEALTHY
            logger.warning("Health check fallido.")
        
        return HealthCheck(
            status=health_status,
            timestamp=datetime.now(),
            service=config.app_name,
            version=config.app_version,
            uptime_seconds=metricas["uptime_seconds"],
            modelo_cargado=metricas["modelo_cargado"]
        )
    except Exception as e:
        logger.error(f"Error durante health check: {e}")
        return HealthCheck(
            status=HealthStatus.DEGRADED,
            timestamp=datetime.now(),
            service=config.app_name,
            version=config.app_version,
            modelo_cargado=False
        )

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    service: MLPredictionService = Depends(get_ml_service)
):
    try:
        metricas = service.get_metricas()
        logger.debug("Métricas obtenidas exitosamente.")
        return MetricsResponse(
            predictions_total=metricas["predictions_total"],
            predictions_success=metricas["predictions_success"],
            predictions_failed=metricas["predictions_failed"],
            avg_prediction_time_ms=metricas["avg_prediction_time_ms"],
            uptime_seconds=metricas["uptime_seconds"],
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error al obtener métricas: {e}")
        raise HTTPException(
            status_code=500,
            detail="No se pudieron obtener las métricas del servicio."
        )

@router.get("/info")
async def get_service_info(
    service: MLPredictionService = Depends(get_ml_service),
    config: Settings = Depends(get_settings)
):
    try:
        info_modelo = service.get_info_modelo()

        info_completa = {
            "servicio": {
                "nombre": config.app_name,
                "version": config.app_version,
                "host": config.host,
                "port": config.port,
                "debug": config.debug
            },
            "modelo_ml": info_modelo,
            "Configuración": {
                "ruta_modelo": config.ml_model_path,
                "umbral_confianza": config.prediction_confidence_threshold
            },
            "timestamp": datetime.now().isoformat()
        }

        logger.info("Información del servicio obtenida exitosamente.")
        return info_completa
    except Exception as e:
        logger.error(f"Error al obtener información del servicio: {e}")
        raise HTTPException(
            status_code=500,
            detail="No se pudo obtener la información del servicio."
        )