# Utilice la imagen de Python más reciente para asegurar la compatibilidad con AMD64
FROM --platform=linux/amd64 python:3.9 as base

# Actualice el sistema e instale dependencias básicas
RUN apt-get update && \
    apt-get install -y build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Establezca el directorio de trabajo en /app
WORKDIR /app

# Copie el archivo requirements.txt en el directorio de trabajo y luego instale las dependencias
COPY api/requirements.txt .
RUN pip install -U pip && pip install -r requirements.txt

# Copie los archivos de la aplicación en el directorio de trabajo
COPY api/ ./api

# Establecer el PYTHONPATH
ENV PYTHONPATH /app/api

# Exponga el puerto necesario
EXPOSE 8000

# Ejecute Gunicorn como el proceso principal del contenedor
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "api.main:app", "-w", "4", "--timeout", "300", "-k", "uvicorn.workers.UvicornWorker"]
