"""
Schemas de Pydantic para validación de datos.

Vamos usar este .py para definir los modelos de request/response para la API
de machine learning de siniestros.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

"""HACEMOS USO DE ENUMERADOS PARA LOS CAMPOS QUE TIENEN VALORES FIJOS"""
class TipoGravedad(str, Enum):
    """Tipos de gravedad de siniestros."""
    SOLO_DANOS = "SOLO DANOS"
    CON_HERIDOS = "CON HERIDOS"
    CON_MUERTOS = "CON MUERTOS"

class TipoSiniestro(str, Enum):
    """Tipos de clase de accidentes."""
    CHOQUE = "CHOQUE"
    OTRO = "OTRO"
    ATROPELLO = "ATROPELLO"
    VOLCAMIENTO = "VOLCAMIENTO"
    CAIDA_OCUPANTE = "CAIDA DE OCUPANTE"
    AUTOLESION = "AUTOLESION"
    INCENDIO = "INCENDIO"

class LocalidadBogota(str, Enum):
    """Localidades de Bogotá."""
    USAQUEN = "USAQUEN"
    CHAPINERO = "CHAPINERO"
    SANTA_FE = "SANTA FE"
    SAN_CRISTOBAL = "SAN CRISTOBAL"
    USME = "USME"
    TUNJUELITO = "TUNJUELITO"
    BOSA = "BOSA"
    KENNEDY = "KENNEDY"
    FONTIBON = "FONTIBON"
    ENGATIVA = "ENGATIVA"
    SUBA = "SUBA"
    BARRIOS_UNIDOS = "BARRIOS UNIDOS"
    TEUSAQUILLO = "TEUSAQUILLO"
    PUENTE_ARANDA = "PUENTE ARANDA"
    CANDELARIA = "CANDELARIA"
    RAFAEL_URIBE_URIBE = "RAFAEL URIBE URIBE"
    CIUDAD_BOLIVAR = "CIUDAD BOLIVAR"
    SUMAPAZ = "SUMAPAZ"

"""ENUMERADO PARA ESTADOS DE SALUD DEL SERVICIO"""
class HealthStatus(str, Enum):
    """Estados de salud del servicio."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


"""Aclaracion de uso de Field en Pydantic:
- ... (tres puntos) indica que el campo es obligatorio.
- Si no se usa ..., el campo es opcional.
- Si se usa Optional[T], el campo puede ser None.
- Podemos usar validaciones como ge (greater equal), le (less equal), min_length, max_length, etc.
- Podemos definir valores por defecto.
- Podemos usar descripciones para documentar los campos.
"""

"""Ahora creamos el modelo para el ML Entrenado"""
class MLFeatures(BaseModel):
    """
    Para el ejemplo practico del taller K8S vamos hacer uso de solo 8 datos basicos
    """

    latitud: float = Field(
        ..., 
        ge=4.0,
        le=5.0,
        description="Latitud del siniestro, teniendo en cuenta rango de Bogota")
    
    longitud: float = Field(
        ...,
        ge=-75.0,
        le=-73.0,
        description="Longitud del siniestro, teniendo en cuenta rango de Bogota")
    
    hora_dia: int = Field(
        ...,
        ge=0,
        le=23,
        description="Hora del día del siniestro (0-23)")

    dia_semana: int = Field(
        ...,
        ge=0,
        le=6,
        description="Día de la semana del siniestro (0=Lunes, 6=Domingo)")

    mes: int = Field(
        ...,
        ge=1,
        le=12,
        description="Mes del siniestro (1=Enero, 12=Diciembre)")
    
    ano: int = Field(
        ...,
        ge=2000,
        le=2030,
        description="Año del siniestro")
    
    direccion: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="Dirección del siniestro")
    
    """Hacemos uso de los enumerados definidos arriba"""
    localidad: LocalidadBogota = Field(
        ...,
        description="Localidad del siniestro (Bogotá)")
    
    clase_accidente: TipoSiniestro = Field(
        ...,
        description="Clase de accidente (TipoSiniestro)")
    

    """Como existe la posibilidad de que el usuario envie un valor no esperado,
    Pydantic se encargará de validar que el valor este dentro de los permitidos"""

    @validator('latitud')
    def validar_latitud_bogota(cls, v):
        if not (4.0 <= v <= 5.0):
            raise ValueError('La latitud debe estar entre 4.0 y 5.0 para Bogotá')
        return v
    
    @validator('longitud')
    def validar_longitud_bogota(cls, v):
        if not (-75.0 <= v <= -73.0):
            raise ValueError('La longitud debe estar entre -75.0 y -73.0 para Bogotá')
        return v
    
    @validator('direccion')
    def validar_direccion(cls, v):
        if not v:
            raise ValueError('La dirección no puede estar vacía')
        return v.strip().upper()
    
    class Config:
        """Configuración del schema."""
        schema_extra = {
            "example": {
                "latitud": 4.7110,
                "longitud": -74.0721,
                "hora_dia": 14,
                "dia_semana": 2,
                "mes": 5,
                "ano": 2024,
                "direccion": "Calle 123 #45-67",
                "localidad": "CHAPINERO",
                "clase_accidente": "CHOQUE"
            }
        }

class PrediccionMLRequest(BaseModel):
    """Modelo de request para predicción ML."""
    features: MLFeatures = Field(
        ...,
        description="Características del siniestro para la predicción")
    
    class Config:
        """Configuración del schema."""
        schema_extra = {
            "example": {
                "features": {
                    "latitud": 4.7110,
                    "longitud": -74.0721,
                    "hora_dia": 14,
                    "dia_semana": 2,
                    "mes": 5,
                    "ano": 2024,
                    "direccion": "Calle 123 #45-67",
                    "localidad": "CHAPINERO",
                    "clase_accidente": "CHOQUE"
                }
            }
        }

class PrediccionMLResponse(BaseModel):
    """Modelo de response para la predicción ML."""

    """Hacemos uso del enumerado TipoGravedad"""
    gravedad_predicha: TipoGravedad = Field(
        ...,
        description="Gravedad predicha del siniestro por el modelo ML")
    
    confianza_porcentaje: float = Field(
        ...,
        ge=0,
        le=100,
        description="Confianza del modelo ML en la predicción")
    
    probabilidades_porcentaje: Dict[str, float] = Field(
        ...,
        description="Probabilidades para cada clase de gravedad")
    
    timestamp: datetime = Field(
        ...,
        default_factory=datetime.now,
        description="Momento en que se realizó la predicción")
    
    modelo_version: str = Field(
        default="1.0.0",
        description="Versión del modelo de Machine Learning utilizado")

    tiempo_procesamiento_ms: Optional[float] = Field(
        None,
        description="Tiempo de procesamiento de la predicción en milisegundos") 
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "gravedad_predicha": "SOLO DANOS",
                "confianza_porcentaje": 57.88,
                "probabilidades_porcentaje": {
                    "CON HERIDOS": 39.88,
                    "CON MUERTOS": 2.25,
                    "SOLO DANOS": 57.88
                },
                "timestamp": "2025-10-21T20:11:00.341721",
                "modelo_version": "1.0.0",
                "tiempo_procesamiento_ms": 41.55
            }
        }

class HealthCheck(BaseModel):
    """Response del health check de la API."""

    status: HealthStatus = Field(
        ...,
        description="Estado de salud del servicio")
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Momento en que se realizó el chequeo de salud")
    
    service: str = Field(
        default="siniestros-ml-api",
        description="Nombre del servicio")
    
    version: str = Field(
        default="1.0.0",
        description="Versión del servicio")
    
    uptime_seconds: Optional[float] = Field(
        None,
        description="Tiempo de actividad del servicio en segundos")
    
    modelo_cargado: Optional[bool] = Field(
        default=False,
        description="Indica si el modelo de ML está cargado correctamente")
    
    memoria_usada_mb: Optional[float] = Field(
        None,
        description="Memoria usada por el servicio en megabytes")
    
    predicciones_realizadas: Optional[int] = Field(
        None,
        description="Número total de predicciones realizadas desde el inicio del servicio")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-01T12:00:00",
                "service": "siniestros-ml-api",
                "version": "1.0.0",
                "uptime_seconds": 86400.0,
                "modelo_cargado": True,
                "memoria_usada_mb": 150.5,
                "predicciones_realizadas": 12345
            }
        }

class MetricsResponse(BaseModel):
    """Response de metricas detalladas del servicio."""

    #Las siguientes metricas van relacionadas con el resultado de las predicciones
    predictions_total: int = Field(
        default=0,
        description="Número total de predicciones realizadas")
    
    predictions_success: int = Field(
        default=0,
        description="Número total de predicciones exitosas")
    
    predictions_failed: int = Field(
        default=0,
        description="Número total de predicciones fallidas")

    avg_prediction_time_ms: Optional[float] = Field(
        None,
        description="Tiempo promedio de procesamiento de predicciones en milisegundos")

    min_prediction_time_ms: Optional[float] = Field(
        None,
        description="Tiempo mínimo de procesamiento de predicciones en milisegundos")
    
    max_prediction_time_ms: Optional[float] = Field(
        None,
        description="Tiempo máximo de procesamiento de predicciones en milisegundos")
    
    #Metricas de uso de recursos
    uptime_seconds: Optional[float] = Field(
        None,
        description="Tiempo de actividad del servicio en segundos")
    memoria_usada_mb: Optional[float] = Field(
        None,
        description="Memoria usada por el servicio en megabytes")
    cpu_usage_percent: Optional[float] = Field(
        None,
        description="Porcentaje de uso de CPU del servicio")
    
    # Timestamps de las metricas
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Momento en que se recopilaron las métricas")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "predictions_total": 15000,
                "predictions_success": 14500,
                "predictions_failed": 500,
                "avg_prediction_time_ms": 120.5,
                "min_prediction_time_ms": 80.0,
                "max_prediction_time_ms": 300.0,
                "uptime_seconds": 172800.0,
                "memoria_usada_mb": 160.0,
                "cpu_usage_percent": 25.5,
                "timestamp": "2024-01-01T12:00:00"
            }
        }
