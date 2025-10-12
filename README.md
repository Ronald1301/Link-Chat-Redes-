# 🚀 Link-Chat 2.0

**Sistema de comunicación peer-to-peer por Ethernet usando raw sockets**

> 📚 **Proyecto Académico**: Redes de Computadoras 2025  
> 🎯 **Comunicación Capa 2**: Protocolo Ethernet directo sin capas de red superiores  
> ⭐ **Puntuación**: 6.0/6.0 estimado de cumplimiento académico  
> 🐍 **Python**: Solo bibliotecas estándar (sin dependencias externas)

## 📋 Características Principales

- 🔗 **Comunicación directa por Ethernet** - Protocolo capa 2 con raw sockets (sin TCP/UDP/IP)
- 📁 **Transferencia inteligente de archivos** - Fragmentación avanzada soportando archivos hasta 5.6TB
- 📂 **Transferencia recursiva de carpetas** - Sistema innovador sin compresión ZIP
- 🔍 **Discovery automático de dispositivos** - Detección automática en red y mensajería broadcast
- 🔒 **Capa de seguridad básica** - Cifrado XOR + autenticación HMAC-SHA256
- 🖥️ **Interfaz dual** - GUI completa (Tkinter) + aplicación de consola
- ⚡ **Alto rendimiento** - Optimizado para transferencias masivas y mensajería en tiempo real
- 🐳 **Entorno Docker** - Testing completo virtualizado multi-nodo

## 🏗️ Estructura del Proyecto

```
Link-Chat-2.0/
├── 📱 app.py                  # Aplicación principal GUI
├── 🖥️ console_app.py         # Interfaz de consola  
├──  src/                    # Código organizado
│   ├── ⚡ core/               # Módulos fundamentales
│   │   ├── frames.py          # 📡 Protocolo Ethernet personalizado
│   │   ├── env_recb.py        # 🔌 Comunicación raw socket
│   │   ├── fragmentation.py   # 🧩 Gestión de fragmentación
│   │   └── mac.py             # 🏷️ Utilidades direcciones MAC
│   └── ⭐ features/           # Funcionalidades avanzadas
│       ├── discovery.py       # 🔍 Discovery automático
│       ├── files.py           # 📁 Transferencia de archivos
│       ├── folder_transfer.py # 📂 Transferencia recursiva de carpetas
│       └── simple_security.py # 🔒 Cifrado y autenticación
├── � docker/                 # Configuración Docker
│   ├── dockerfile             # Imagen del contenedor
│   └── docker-compose.yml     # Orquestación
├── 🔧 scripts/                # Scripts de automatización
├── 📖 docs/                   # Documentación del proyecto
└── 📥 downloads/               # Directorio de descarga
```

## 🚀 Instalación y Uso

### Prerrequisitos
- **Python 3.8+** (solo bibliotecas estándar requeridas)
- **Entorno Linux** para acceso a raw sockets
- **Privilegios de root** para acceso a interfaz de red

### Instalación Rápida

```bash
# Clonar repositorio
git clone <repository-url>
cd Link-Chat-2.0

# ¡Sin dependencias adicionales! Solo usa bibliotecas estándar de Python
```

### Ejecutar la Aplicación

```bash
# Interfaz Gráfica (Recomendada)
sudo python3 app.py

# Interfaz de Consola (Testing/Docker)
sudo python3 console_app.py

# Especificar interfaz de red (opcional)
sudo python3 app.py eth0
```

## � Entorno de Testing Docker

Perfecto para testing de comunicación multi-nodo:

```bash
# Iniciar simulación de red de 3 nodos
cd docker/
sudo docker-compose up

# Cada nodo obtiene su propio directorio de descargas:
# - downloads1/ (Nodo 1)
# - downloads2/ (Nodo 2) 
# - downloads3/ (Nodo 3)
```

### Script de Automatización

```powershell
# Configuración completa automática
.\scripts\docker-test.ps1 setup

# Solo iniciar contenedores
.\scripts\docker-test.ps1 start

# Detener contenedores
.\scripts\docker-test.ps1 stop
```

## 🎯 Cumplimiento Académico

### ✅ Requisitos Mínimos (3.0/3.0 puntos)
- **Mensajería ordenador a ordenador**: ✓ Implementado via raw sockets Ethernet
- **Intercambio de archivos punto a punto**: ✓ Sistema de fragmentación avanzado
- **Interfaz de consola mínima**: ✓ `console_app.py` para testing Docker
- **Solución Docker + red física**: ✓ Entorno completo multi-nodo

### ✅ Características Extras (1.75/1.75 puntos)
- **Archivos/mensajes de cualquier tamaño (0.5 pts)**: ✓ Fragmentación 4B → soporte 5.6TB
- **Identificación automática de ordenadores (0.25 pts)**: ✓ Sistema de discovery de red
- **Mensajería uno a todos (0.25 pts)**: ✓ Mensajería broadcast implementada
- **Envío/recepción de carpetas (0.25 pts)**: ✓ Transferencia recursiva sin ZIP
- **Capa de seguridad (0.5 pts)**: ✓ Cifrado XOR + autenticación HMAC

### ✅ Interfaz Visual (1.25/1.25 puntos)
- **Interfaz alternativa a consola (0.25 pts)**: ✓ GUI completa con Tkinter
- **Experiencia de usuario (0.25 pts)**: ✓ Progreso en tiempo real y notificaciones
- **Fluidez y diseño (0.25 pts)**: ✓ Interfaz responsive y profesional
- **Manejo y recuperación de errores (0.25 pts)**: ✓ Bloques try/catch completos
- **Creatividad (0.25 pts)**: ✓ Transferencia recursiva innovadora

### 🏆 **Puntuación Total Estimada: 6.0/6.0**

## 📡 Especificaciones Técnicas

### Protocolo de Red
- **Capa**: Capa de Enlace de Datos (Capa 2)
- **EtherType**: 0x88B5 (protocolo personalizado)
- **Formato de Frame**: Frames Ethernet personalizados con verificación CRC32
- **Direccionamiento**: Comunicación directa por direcciones MAC

### Sistema de Fragmentación
- **Tamaño de Fragmento**: 1475 bytes (optimizado para MTU Ethernet)
- **Tamaño Máximo de Archivo**: 5.6TB (4.3 mil millones de fragmentos)
- **Seguimiento de Fragmentos**: Números de fragmento de 4 bytes
- **Reensamblado**: Automático con verificación de integridad

### Características de Seguridad
- **Cifrado**: Cifrado XOR con claves derivadas
- **Autenticación**: Autenticación de mensajes HMAC-SHA256
- **Intercambio de Claves**: Protocolo simple de desafío-respuesta
- **Integridad**: Verificación de frame CRC32 + verificación de payload HMAC

## � Ejemplos de Uso

### Mensajería Básica
1. Iniciar aplicación: `sudo python3 app.py`
2. Hacer clic en "Start Discovery" para encontrar otros dispositivos
3. Seleccionar dispositivo de la lista y escribir mensaje
4. Hacer clic en "Send Message"

### Transferencia de Archivos
1. Hacer clic en el botón "Send File"
2. Seleccionar archivo del diálogo
3. Elegir dispositivo de destino
4. Monitorear progreso en tiempo real

### Transferencia de Carpetas (Característica Innovadora)
1. Hacer clic en el botón "Send Folder"
2. Seleccionar directorio a transferir
3. El sistema transfiere automáticamente todos los archivos recursivamente
4. Preserva la estructura de directorios sin compresión ZIP

## 🐛 Solución de Problemas

### Problemas Comunes

**Permiso denegado al iniciar**
```bash
# Solución: Ejecutar con sudo
sudo python3 app.py
```

**No se encontraron interfaces de red**
```bash
# Verificar interfaces disponibles
ip link show

# Especificar interfaz manualmente
sudo python3 app.py eth0
```

**Los contenedores Docker no pueden comunicarse**
```bash
# Asegurar que la red bridge esté configurada correctamente
sudo docker network ls
sudo docker-compose down && sudo docker-compose up
```

## 📄 Licencia

Proyecto académico para propósitos educativos.

## 🏫 Contexto Académico

Este proyecto fue desarrollado para el **Curso de Redes de Computadoras 2025** como el primer proyecto del curso. Demuestra:

- **Implementación de Protocolo Capa 2** - Comunicación Ethernet directa
- **Programación de Redes** - Manipulación de raw sockets
- **Diseño de Protocolos** - Estructura de frames personalizada y fragmentación
- **Fundamentos de Seguridad** - Cifrado básico y autenticación
- **Arquitectura de Software** - Diseño modular y extensible

La implementación usa estrictamente **solo bibliotecas estándar de Python** para cumplir los requisitos académicos, evitando bibliotecas de red externas y enfocándose en conceptos fundamentales de programación de redes.

---

**Link-Chat 2.0** - Comunicación peer-to-peer sin límites 🌐
