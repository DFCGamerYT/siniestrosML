"""
Aplicación principal FastAPI para predicción de siniestros ML.

Esta aplicación proporciona una API REST para predecir la gravedad de
siniestros de tránsito en Bogotá usando Machine Learning.

Arquitectura implementada:
- Layered Microservice con Clean Architecture
- Dependency Injection pattern
- Factory pattern para app creation
- Configuration pattern externalizado
- Health checks para Kubernetes
- Logging estructurado para observabilidad
"""

import logging, time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

# Importar configuración y servicios
from .config import get_settings
from .services.prediction_service import MLPredictionService

# Importar routers
from .routers import health, siniestros

# Configurar logging estructurado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Variable global para el servicio ML
ml_prediction_service: MLPredictionService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida de la aplicación.
    
    Maneja startup y shutdown events para:
    - Inicializar servicios ML críticos
    - Asignar servicios a routers
    - Verificar health del sistema
    - Limpiar recursos al cerrar
    """
    global ml_prediction_service
    
    # ===== STARTUP =====
    logger.info("🚀 Iniciando Siniestros ML API")
    
    try:
        # Cargar configuración
        config = get_settings()
        logger.info(f"📋 Configuración cargada: {config.app_name} v{config.app_version}")
        logger.info(f"🔧 Modo debug: {config.debug}")
        logger.info(f"📁 Ruta modelos: {config.ml_model_path}")
        
        # Inicializar servicio ML principal
        logger.info("🧠 Inicializando servicio de Machine Learning...")
        ml_prediction_service = MLPredictionService(config)
        
        # Verificar que el servicio esté saludable
        if ml_prediction_service.health_check():
            logger.info("✅ Servicio ML inicializado correctamente y saludable")
        else:
            logger.error("❌ CRÍTICO: Servicio ML no está saludable")
            raise Exception("Servicio ML no pudo inicializarse correctamente")
            
        # Asignar servicio a los routers (Dependency Injection manual)
        health.ml_service = ml_prediction_service
        siniestros.ml_service = ml_prediction_service
        logger.info("🔌 Servicios asignados a routers exitosamente")
        
        # Log de endpoints disponibles
        logger.info("📡 Endpoints principales disponibles:")
        logger.info("   • POST /ml/predecir - Predicción principal")
        logger.info("   • GET /health - Health check")
        logger.info("   • GET /health/metrics - Métricas del sistema")
        logger.info("   • GET /docs - Documentación interactiva")
        
        logger.info("🎯 Aplicación LISTA para recibir requests")
        
    except Exception as e:
        logger.error(f"💥 ERROR CRÍTICO durante startup: {e}")
        logger.error("🛑 La aplicación NO puede iniciarse correctamente")
        raise
    
    # Yield control back to FastAPI
    yield
    
    # ===== SHUTDOWN =====
    logger.info("🛑 Cerrando Siniestros ML API")
    logger.info("📊 Métricas finales del servicio:")
    
    if ml_prediction_service:
        try:
            metricas = ml_prediction_service.get_metricas()
            logger.info(f"   • Total predicciones: {metricas['predictions_total']}")
            logger.info(f"   • Predicciones exitosas: {metricas['predictions_success']}")
            logger.info(f"   • Tiempo activo: {metricas['uptime_seconds']:.1f}s")
        except:
            logger.warning("No se pudieron obtener métricas finales")
    
    logger.info("👋 Aplicación cerrada correctamente")


def create_app() -> FastAPI:
    """
    Factory pattern para crear la aplicación FastAPI.
    
    Configura middleware, routers, manejo de errores y documentación.
    Permite fácil testing y personalización según entorno.
    
    Returns:
        FastAPI: Aplicación configurada y lista para deploy
    """
    config = get_settings()
    
    # Crear aplicación FastAPI con configuración completa
    app = FastAPI(
        title=config.app_name,
        description="""
        ## 🧠 API de Predicción ML para Siniestros de Tránsito en Bogotá
        
        Esta API utiliza **Machine Learning avanzado** para predecir la gravedad de siniestros
        de tránsito basándose en características geográficas, temporales y contextuales.
        
        ### 🚀 Características Principales:
        - 🧠 **Predicción ML** con Random Forest optimizado
        - 📍 **Geolocalización específica** de Bogotá (20 localidades)
        - ⏱️ **Análisis temporal** (hora, día, mes)
        - 📊 **Métricas en tiempo real** para monitoreo
        - 🏥 **Health checks** para Kubernetes
        - 📈 **Logging estructurado** para observabilidad
        - 🔒 **Validación robusta** con Pydantic
        - 🐳 **Docker ready** para contenedores
        
        ### 📡 Endpoints Principales:
        - `POST /ml/predecir` - **Predicción principal de gravedad**
        - `GET /health` - Health check para K8s probes
        - `GET /health/metrics` - Métricas detalladas del sistema
        - `GET /ml/valores/localidades` - Localidades disponibles
        - `GET /ml/valores/tipos-siniestro` - Tipos de siniestro válidos
        
        ### 🎯 Tipos de Gravedad Predichos:
        - **SOLO DANOS** - Siniestros con daños materiales únicamente
        - **CON HERIDOS** - Siniestros con personas heridas
        - **CON MUERTOS** - Siniestros con víctimas fatales
        
        ### 🏗️ Arquitectura:
        - **Microservicio** independiente y escalable
        - **Clean Architecture** con separación de responsabilidades
        - **Dependency Injection** para fácil testing
        - **Configuration externalized** via variables de entorno
        """,
        version=config.app_version,
        debug=config.debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    return app


# Crear instancia principal de la aplicación
app = create_app()
config = get_settings()

# Configurar CORS middleware para desarrollo y producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if config.debug else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logging automático de todas las requests."""
    start_time = time.time()
    
    # Log request
    logger.info(f"📨 {request.method} {request.url.path} - Cliente: {request.client.host}")
    
    # Procesar request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"📤 {request.method} {request.url.path} - Status: {response.status_code} - Tiempo: {process_time:.3f}s")
    
    return response

# Registrar routers con tags organizados
app.include_router(
    health.router
)

app.include_router(
    siniestros.router
)


# Manejo global de errores de validación Pydantic
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """
    Manejo personalizado de errores de validación.
    Devuelve respuestas JSON amigables con detalles específicos.
    """
    logger.error(f"❌ Error de validación en {request.url.path}: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Datos de entrada inválidos",
            "details": exc.errors(),
            "message": "Por favor revisa los datos enviados según la documentación",
            "docs": "/docs"
        }
    )


# Manejo global de errores internos
@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """Manejo de errores internos del servidor."""
    logger.error(f"💥 Error interno en {request.url.path}: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Error interno del servidor",
            "message": "Ha ocurrido un error inesperado. Por favor intenta nuevamente.",
            "request_id": str(hash(str(request.url)))[:8]
        }
    )


# Endpoint raíz informativo
@app.get("/", tags=["📋 Info"])
async def root():
    """
    Endpoint raíz con información básica y navegación de la API.
    Punto de entrada amigable para desarrolladores.
    """
    return {
        "🚀 servicio": f"{config.app_name} v{config.app_version}",
        "📊 status": "✅ Activo y funcionando",
        "🧠 ml_modelo": "Random Forest - Gravedad de Siniestros",
        "📍 cobertura": "Bogotá, Colombia (20 localidades)",
        "📡 endpoints": {
            "prediccion": "/ml/predecir",
            "health": "/health", 
            "metricas": "/health/metrics",
            "documentacion": "/docs",
            "localidades": "/ml/valores/localidades",
            "tipos_siniestro": "/ml/valores/tipos-siniestro"
        },
        "🐳 docker": "docker run -p 8000:8000 siniestros-ml:latest",
        "📚 docs_interactivas": f"http://{config.host}:{config.port}/docs",
        "🔧 config": {
            "debug": config.debug,
            "host": config.host,
            "port": config.port
        }
    }


# Punto de entrada para ejecutar directamente con Python
if __name__ == "__main__":
    import uvicorn
    import time
    
    logger.info("=" * 60)
    logger.info(f"🎯 INICIANDO {config.app_name} v{config.app_version}")
    logger.info(f"🌐 Servidor: http://{config.host}:{config.port}")
    logger.info(f"📚 Documentación: http://{config.host}:{config.port}/docs")
    logger.info(f"🏥 Health check: http://{config.host}:{config.port}/health")
    logger.info("=" * 60)
    
    uvicorn.run(
        "app.main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="info",
        access_log=True
    )