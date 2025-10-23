# Usar imagen base oficial de Python 3.14 slim
FROM python:3.14-slim

# Variables de entorno para Python y aplicación
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    HOST=0.0.0.0 \
    PORT=8000

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema (mínimas para ML)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar requirements y instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

RUN ls -l

RUN mkdir -p models
# Descargar modelo desde Google Drive
RUN python -m gdown --id 12AR12tQjeVdBDz7aPys8716uelsQbjGX -O models/modelo_base_rf.pkl
RUN python -m gdown --id 1t_utRXIEub1gbqHoET1hoi_43LE7L2v8 -O models/le_clase_acc_base.pkl
RUN python -m gdown --id 1joITG2gY8t0Dmz7reMi2eK5f_2m_E-SE -O models/le_gravedad_base.pkl
RUN python -m gdown --id 12AR12tQjeVdBDz7aPys8716uelsQbjGX -O models/le_localidad_base.pkl

# Copiar código fuente y modelos
COPY app/ ./app/
COPY models/ ./models/

# Crear usuario no-root para seguridad
RUN groupadd -r appgroup && useradd -r -g appgroup appuser \
    && chown -R appuser:appgroup /app
USER appuser

# Exponer puerto dinámico
EXPOSE $PORT

# Health check con puerto dinámico
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Comando flexible que usa variables de entorno
CMD ["sh", "-c", "uvicorn app.main:app --host $HOST --port $PORT"]