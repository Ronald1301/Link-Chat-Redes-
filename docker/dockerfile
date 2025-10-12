FROM ubuntu:22.04

# Evitar prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias para networking de bajo nivel
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-tk \
    tcpdump \
    net-tools \
    iproute2 \
    iputils-ping \
    macchanger \
    bridge-utils \
    vlan \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Crear directorios necesarios
RUN mkdir -p downloads LinkChat_Files

# Script de inicio que acepta interfaz como parámetro
RUN echo '#!/bin/bash\nINTERFACE=${1:-eth0}\necho "Usando interfaz: $INTERFACE"\npython3 app.py $INTERFACE' > /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]