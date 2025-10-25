import pytest
import logging
from unittest.mock import MagicMock, patch
from datetime import datetime

from .prediction_service import MLPredictionService
from ..config import Settings
from ..models.schemas import MLFeatures, PrediccionMLResponse, TipoGravedad 

@pytest.fixture
def mock_config():
    return Settings(
        app_version="1.0.0",
        ml_model_path="/test/models",
        prediction_confidence_threshold=0.50
    )

@pytest.fixture
def valid_features():
    return MLFeatures(
        latitud=4.71,
        longitud=-74.07,
        hora_dia=14,
        dia_semana=2,
        mes=5,
        ano=2024,
        direccion="CALLE 100",
        localidad="CHAPINERO",
        clase_accidente="CHOQUE"
    )

@pytest.fixture(autouse=True)
def mock_time(mocker):
    mock_timer = mocker.patch("time.time")
    mock_timer.side_effect = [1000.0, 1000.1, 1000.2, 1000.3, 1000.4, 1000.5] 
    return mock_timer

@pytest.fixture
def prediction_service_class(mocker):
    mocker.patch("pathlib.Path.exists", return_value=True)

    mock_model = MagicMock()
    mock_model.predict.return_value = [0]
    mock_model.predict_proba.return_value = [[0.90, 0.05, 0.05]]
    
    mock_le_localidad = MagicMock()
    mock_le_gravedad = MagicMock()
    mock_le_clase_acc = MagicMock()
    
    mock_le_gravedad.inverse_transform.return_value = ["SOLO DANOS"]
    mock_le_gravedad.classes_ = ["SOLO DANOS", "CON LESION", "CON MUERTE"]
    
    mock_joblib_load = mocker.patch("joblib.load")
    mock_joblib_load.side_effect = [
        mock_model, mock_le_localidad, mock_le_gravedad, mock_le_clase_acc
    ]

    mocker.patch("logging.getLogger")

    return MLPredictionService

@pytest.fixture
def loaded_service(prediction_service_class, mock_config):
    return prediction_service_class(mock_config)

def test_cargar_modelo_success(loaded_service):
    assert loaded_service.modelo is not None
    assert loaded_service.le_localidad is not None
    assert loaded_service.health_check() is True

@patch("pathlib.Path.exists", return_value=False)
def test_cargar_modelo_file_not_found(mock_exists, prediction_service_class, mock_config, mocker):
    mocker.patch("joblib.load")
    service = prediction_service_class(mock_config)
    
    assert service.modelo is None
    assert service.health_check() is False

@patch("joblib.load", side_effect=IOError("Mock Load Error"))
@patch("pathlib.Path.exists", return_value=True)
def test_cargar_modelo_load_exception(mock_exists, mock_load, prediction_service_class, mock_config):
    service = prediction_service_class(mock_config)
    
    assert service.modelo is None
    assert service.health_check() is False

def test_health_check_healthy(loaded_service):
    assert loaded_service.health_check() is True

def test_health_check_unhealthy(loaded_service):
    loaded_service.modelo = None
    assert loaded_service.health_check() is False

def test_procesar_features_correct_encoding(loaded_service, valid_features, mocker):
    encoded_localidad = 10
    encoded_accidente = 5
    
    mocker.patch.object(loaded_service.le_localidad, "transform", return_value=[encoded_localidad])
    mocker.patch.object(loaded_service.le_clase_acc, "transform", return_value=[encoded_accidente])
    
    X = loaded_service._procesar_features(valid_features)
    
    assert X[0][6] == encoded_localidad
    assert X[0][7] == encoded_accidente

def test_procesar_features_unknown_value(loaded_service, valid_features, mocker):
    mocker.patch.object(loaded_service.le_localidad, "transform", side_effect=ValueError("Unknown label"))
    
    with pytest.raises(ValueError, match="Unknown label"):
        loaded_service._procesar_features(valid_features)

def test_predecir_high_confidence(loaded_service, valid_features, mocker):
    mock_update_metrics = mocker.patch.object(loaded_service, "_actualizar_metricas_exitosa")

    response = loaded_service.predecir(valid_features)

    assert response.gravedad_predicha == TipoGravedad.SOLO_DANOS
    assert response.confianza_porcentaje == 90.0
    assert response.tiempo_procesamiento_ms == 100.0
    mock_update_metrics.assert_called_once()
    
def test_predecir_runtime_error(loaded_service, valid_features, mocker):
    loaded_service.modelo.predict.side_effect = RuntimeError("Model failed")
    mock_update_failed_metrics = mocker.patch.object(loaded_service, "_actualizar_metricas_fallida")

    with pytest.raises(Exception, match="Error al realizar predicción"):
        loaded_service.predecir(valid_features)
        
    mock_update_failed_metrics.assert_called_once()

def test_metricas(loaded_service):
    loaded_service._actualizar_metricas_exitosa(15.0)
    
    assert loaded_service.predictions_total == 1
    assert loaded_service.predictions_success == 1
    assert loaded_service.prediction_times == [15.0]

def test_metricas_error(loaded_service):
    loaded_service._actualizar_metricas_fallida()
    
    assert loaded_service.predictions_total == 1
    assert loaded_service.predictions_failed == 1
    assert loaded_service.predictions_success == 0