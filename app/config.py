import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """
    Configuración principal de la aplicación.
    Usamos valores por defecto si no se proporcionan variables de entorno.
    """
    app_name: str = Field(
        default="Siniestros ML API", 
        description="Nombre de la aplicación")
    app_version: str = Field(
        default="1.0.0", 
        description="Versión de la aplicación")
    # No ponemos localhost porque docker/kubernetes necesitan acceder escuchando en todas las interfaces
    host: str = Field(
        default="0.0.0.0",
        description="Host de la aplicación")
    port: int = Field(
        default=8000,
        description="Puerto de la aplicación")
    debug: bool = Field(
        default=False,
        description="Modo de depuración")
    # Si no se proporciona, usamos una ruta por defecto
    ml_model_path: Optional[str] = Field(
        default="models/",
        description="Ruta del modelo de Machine Learning")
    prediction_confidence_threshold: float = Field(
        default=0.7,
        description="Umbral de confianza para las predicciones")

    class Config:
        """Clase de configuración para acceder a los ajustes de la aplicación."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()

def get_settings() -> Settings:
    """Factory function para obtener la configuración."""
    return settings