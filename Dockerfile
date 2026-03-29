# Usar una imagen oficial de Python ligera
FROM python:3.10-slim

# Establecer la carpeta de trabajo
WORKDIR /app

# Prevenir la escritura de archivos .pyc e instigaciones de buffering
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instalar dependencias del sistema y limpiarlas para mantener la imagen pequeña
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar configuración de requerimientos e instalar dependencias Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . /app/

# Exponer el puerto
EXPOSE 8000

# Comando para arrancar el servidor en producción
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
