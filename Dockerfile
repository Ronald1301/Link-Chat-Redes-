FROM python:3.9

# Instalar Tkinter y herramientas de red
RUN apt-get update && apt-get install -y \
    python3-tk \
    tk \
    iputils-ping \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN mkdir -p descargas
ENV PYTHONUNBUFFERED=1
CMD ["sleep", "infinity"]