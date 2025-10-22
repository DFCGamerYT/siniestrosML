"""
Servicio de predicción que carga un modelo ML y realiza predicciones.

Este servicio se encarga de:
- Cargar el modelo de Machine Learning desde la ruta configurada.
- Realizar predicciones basadas en los datos de entrada usando MLFeatures.
- Aplicar un umbral de confianza para filtrar predicciones poco fiables.
- Devolver PrediccionMLResponse con probabilidades.
- Mantener metricas de rendimiento y uso del modelo.
"""

import logging
import joblib
import time

from datetime import datetime
from pathlib import Path
from ..models.schemas import MLFeatures, PrediccionMLResponse, TipoGravedad
from ..config import Settings

logger = logging.getLogger(__name__)

class MLPredictionService:
    """Servicio para manejar predicciones de Machine Learning."""

    def __init__(self, config: Settings):
        # Inicializar el servicio de predicción
        # Nos estamos basando en la configuración proporcionada
        self.config = config

        # Inicializar variables del modelo base junto con sus codificadores
        self.modelo = None
        self.le_localidad = None
        self.le_gravedad = None
        self.le_clase_acc = None

        #Metricas del servicio
        self.predictions_total = 0
        self.predictions_success = 0
        self.predictions_failed = 0
        self.start_time = datetime.now()
        self.prediction_times = []

        self.cargar_modelo()

        logger.info("Servicio de predicción ML inicializado.")

    def cargar_modelo(self) -> bool:
        """
        Cargamos el modelo de Machine Learning desde la ruta configurada.
        Mediante Try/Except para manejar errores de carga. y devolvemos booleano.
        """

        try:
            models_path = Path(self.config.ml_model_path or "models/")

            modelo_path = models_path / "modelo_base_rf.pkl"
            if not modelo_path.exists():
                logger.error(f"El archivo del modelo no existe en la ruta: {modelo_path}")
                return False

            self.modelo = joblib.load(modelo_path)
            logger.info(f"Modelo cargado correctamente desde {modelo_path}")

            # Cargar los codificadores de etiquetas
            self.le_localidad = joblib.load(models_path / "le_localidad_base.pkl")
            self.le_gravedad = joblib.load(models_path / "le_gravedad_base.pkl")
            self.le_clase_acc = joblib.load(models_path / "le_clase_acc_base.pkl")

            logger.info("Codificadores de etiquetas cargados correctamente.")
            return True
        except Exception as e:
            logger.error(f"Error al cargar el modelo de ML: {e}")
            return False

    def predecir(self, features: MLFeatures) -> PrediccionMLResponse:
        """
        Realizamos una predicción usando el modelo cargado.
        Aplicamos el umbral de confianza y devolvemos la respuesta con porcentajes.
        Usamos el MLFeatures como entrada y devolvemos PrediccionMLResponse.
        """

        start_time = time.time()

        try:
            # Para el uso del modelo, tomamos las features y las preprocesamos
            X_procesada = self._procesar_features(features)

            # Realizar prediccion
            prediccion_num = self.modelo.predict(X_procesada)[0]
            probabilidades_array = self.modelo.predict_proba(X_procesada)[0]

            # Traemos el resultado numerico como gravedad
            gravedad_predicha = self.le_gravedad.inverse_transform([prediccion_num])[0]

            # Mapear probabilidades a clases de gravedad CON PORCENTAJES
            clases_gravedad = self.le_gravedad.classes_
            probabilidades_porcentaje = {
                clase: round(float(prob) * 100, 2)  # Convertir a porcentaje con 2 decimales
                for clase, prob in zip(clases_gravedad, probabilidades_array)
            }

            # Confianza en porcentaje (probabilidad de la clase predicha)
            confianza_porcentaje = round(float(probabilidades_array[prediccion_num]) * 100, 2)

            # Verificar umbral de confianza (convertir umbral a porcentaje para comparar)
            umbral_porcentaje = self.config.prediction_confidence_threshold * 100
            
            if confianza_porcentaje < umbral_porcentaje:
                logger.warning(f"⚠️ Predicción con baja confianza: {confianza_porcentaje:.2f}% < {umbral_porcentaje}%")

            # Calcular tiempo de procesamiento
            tiempo_ms = round((time.time() - start_time) * 1000, 2)

            # Previo a la respuesta, actualizamos métricas
            self._actualizar_metricas_exitosa(tiempo_ms)

            # Construir la respuesta CON PORCENTAJES
            respuesta = PrediccionMLResponse(
                gravedad_predicha=TipoGravedad(gravedad_predicha),
                confianza_porcentaje=confianza_porcentaje,
                probabilidades_porcentaje=probabilidades_porcentaje,
                timestamp=datetime.now(),
                modelo_version=self.config.app_version,
                tiempo_procesamiento_ms=tiempo_ms
            )

            logger.info(f"✅ Predicción exitosa: {gravedad_predicha} ({confianza_porcentaje:.2f}%)")
            return respuesta
        
        except Exception as e:
            # En caso de error, actualizamos métricas de fallo
            self._actualizar_metricas_fallida()
            logger.error(f"❌ Error durante la predicción: {e}")
            raise Exception(f"Error al realizar predicción: {e}")

    def _procesar_features(self, features: MLFeatures):
        """Procesamos las features de entrada para el modelo ML."""

        try:
            # Codificar variables categóricas
            localidad_encoded = self.le_localidad.transform([features.localidad.value])[0]
            clase_accidente_encoded = self.le_clase_acc.transform([features.clase_accidente.value])[0]  

            # Crear array con las 8 características básicas exactas del modelo:
            # 1. LATITUD, 2. LONGITUD, 3. HORA, 4. DIA_SEMANA, 5. MES, 6. ANO, 7. LOCALIDAD_COD, 8. CLASE_ACC_COD
            X = [[
                features.latitud,           # LATITUD
                features.longitud,          # LONGITUD  
                features.hora_dia,          # HORA
                features.dia_semana,        # DIA_SEMANA
                features.mes,               # MES
                features.ano,               # ANO
                localidad_encoded,          # LOCALIDAD_COD
                clase_accidente_encoded     # CLASE_ACC_COD
            ]]

            logger.debug(f"Features procesadas para el modelo: {X}")
            return X
        
        except Exception as e:
            logger.error(f"Error al procesar features: {e}")
            raise
    
    def _actualizar_metricas_exitosa(self, tiempo_ms: float):

        """Actualizamos las métricas tras una predicción exitosa."""
        self.predictions_total += 1
        self.predictions_success += 1
        self.prediction_times.append(tiempo_ms)

        if len(self.prediction_times) > 1000:
            self.prediction_times = self.prediction_times[-1000:]

        logger.debug(f"Métricas actualizadas tras predicción exitosa. Total: {self.predictions_total}, Éxitos: {self.predictions_success}") 

    def _actualizar_metricas_fallida(self):
        """Actualizamos las métricas tras una predicción fallida."""
        self.predictions_total += 1
        self.predictions_failed += 1

        logger.debug(f"Métricas actualizadas tras predicción fallida. Total: {self.predictions_total}, Fallos: {self.predictions_failed}")

    def get_metricas(self) -> dict:
        """Obtener las metricas actuales del servicio de predicción."""

        uptime_seconds = (datetime.now() -self.start_time).total_seconds()

        avg_time = (
            sum(self.prediction_times) / len(self.prediction_times)
            if self.prediction_times else 0.0
        )

        metricas = {
            "predictions_total": self.predictions_total,
            "predictions_success": self.predictions_success,
            "predictions_failed": self.predictions_failed,
            "avg_prediction_time_ms": avg_time,
            "uptime_seconds": uptime_seconds,
            "modelo_cargado": self.modelo is not None,
            "timestamp": datetime.now().isoformat()
        }

        logger.debug(f"Métricas obtenidas: {metricas}")
        return metricas
    
    def health_check(self) -> bool:
        """Verificar si el servicio de predicción está saludable."""
        estado_saludable = (
            self.modelo is not None and
            self.le_localidad is not None and
            self.le_gravedad is not None and
            self.le_clase_acc is not None
        )

        if estado_saludable:
            logger.info("Health check: Servicio de predicción ML está saludable.")
        else:
            logger.warning("Health check: Servicio de predicción ML NO está saludable.")
        
        return estado_saludable
    
    def get_info_modelo(self) -> dict:
        """Obtener información sobre el modelo cargado."""
        return {
            "modelo_cargado": self.modelo is not None,
            "modelo_version": self.config.app_version,
            "ruta_modelo": self.config.ml_model_path,
            "umbral_confianza": self.config.prediction_confidence_threshold,
            "features_esperadas": 8,
            "tipos_gravedad": [tg.value for tg in TipoGravedad],
            "features_modelo": ["LATITUD", "LONGITUD", "HORA", "DIA_SEMANA", "MES", "ANO", "LOCALIDAD_COD", "CLASE_ACC_COD"],
            "servicio_iniciado_en": self.start_time.isoformat()
        }