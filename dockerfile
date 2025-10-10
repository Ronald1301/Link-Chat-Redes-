FROM python:3.9

# Instalar dependencias necesarias
RUN apt-get update && apt-get install -y \
    tcpdump \
    net-tools \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos del proyecto
COPY . .

# Crear directorio para archivos descargados
RUN mkdir -p LinkChat_Files

# Ejecutar la aplicación
CMD ["python", "app.py"]