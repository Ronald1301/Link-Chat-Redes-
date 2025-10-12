# 🚀 Guía de Testing Docker - Link-Chat 3.0

## 📋 Guía Completa para Probar Link-Chat en Docker

Esta guía te permite probar Link-Chat 3.0 en contenedores Docker de forma simple y rápida.

---

## 🔧 Requisitos Previos

- **Docker Desktop** instalado y funcionando
- **Windows 10/11** con PowerShell
- **3 terminales PowerShell** disponibles

---

## 🚀 PASO A PASO - Testing Completo

### **PASO 1: Preparar el entorno**

1. **Abrir PowerShell** como administrador (opcional pero recomendado)
2. **Navegar al directorio del proyecto:**
   ```powershell
   cd "c:\PROYECTOS GITHUB\Link-chat-2.0"
   ```

### **PASO 2: Construir la imagen Docker**

```powershell
docker build -t link-chat -f docker/dockerfile .
```

**Resultado esperado:** 
- ✅ Imagen construida exitosamente
- ✅ Sin errores de dependencias

### **PASO 3: Crear los 3 contenedores**

Ejecuta estos comandos **uno por uno:**

```powershell
# Contenedor 1 (Nodo Principal)
docker run -dt --name test-chat --privileged --cap-add NET_RAW --cap-add NET_ADMIN -e DISPLAY=host.docker.internal:0 link-chat bash

# Contenedor 2 (Nodo Secundario)  
docker run -dt --name test-chat-2 --privileged --cap-add NET_RAW --cap-add NET_ADMIN -e DISPLAY=host.docker.internal:0 link-chat bash

# Contenedor 3 (Nodo Terciario)
docker run -dt --name test-chat-3 --privileged --cap-add NET_RAW --cap-add NET_ADMIN -e DISPLAY=host.docker.internal:0 link-chat bash
```

### **PASO 4: Verificar que los contenedores estén activos**

```powershell
docker ps --filter "name=test-chat"
```

**Resultado esperado:**
```
CONTAINER ID   IMAGE       COMMAND   CREATED          STATUS         NAMES
xxxxxxxxxxxxx  link-chat   "bash"    X seconds ago    Up X seconds   test-chat-3
xxxxxxxxxxxxx  link-chat   "bash"    X seconds ago    Up X seconds   test-chat-2  
xxxxxxxxxxxxx  link-chat   "bash"    X seconds ago    Up X seconds   test-chat
```

---

## 🖥️ PASO 5: Abrir terminales para cada contenedor

**Abre 3 nuevas ventanas de PowerShell** y ejecuta **una línea en cada terminal:**

### **Terminal 1 - Nodo Principal:**
```powershell
docker exec -it test-chat bash
```

### **Terminal 2 - Nodo Secundario:**
```powershell
docker exec -it test-chat-2 bash
```

### **Terminal 3 - Nodo Terciario:**
```powershell
docker exec -it test-chat-3 bash
```

---

## 🎯 PASO 6: Ejecutar Link-Chat en cada contenedor

En **cada una de las 3 terminales de contenedor**, ejecuta:

```bash
cd /app
python3 app.py
```

**Resultado esperado:**
- ✅ Aplicación se inicia sin errores
- ✅ Interfaz Tkinter aparece (si tienes X11 configurado)
- ✅ Logs muestran inicio del sistema

---

## 🧪 Plan de Testing Manual

### **1. Verificar Discovery Automático (30-60 segundos)**
- Los nodos deberían detectarse automáticamente
- Verificar en la lista de dispositivos de cada GUI
- Observar logs de discovery en la consola

### **2. Testing de Mensajería**
```
📤 Mensajes Broadcast:
- Enviar desde cualquier nodo
- Verificar recepción en los otros 2

📤 Mensajes Unicast:
- Seleccionar destinatario específico
- Enviar mensaje directo
- Verificar recepción solo en el destino
```

### **3. Testing de Transferencia de Archivos**
- Crear archivo de prueba en Downloads
- Seleccionar archivo desde GUI
- Enviar a nodo específico
- Verificar recepción y integridad

### **4. Testing de Cifrado (Opcional)**
- Activar modo seguro entre 2 nodos
- Enviar mensajes cifrados
- Verificar que el 3er nodo no puede descifrar

---

## 🔍 Comandos Útiles de Debug

### **Ver logs de un contenedor:**
```powershell
docker logs test-chat
docker logs test-chat-2  
docker logs test-chat-3
```

### **Ver interfaces de red:**
```bash
# Dentro del contenedor
ip addr show
ifconfig
route -n
```

### **Verificar conectividad entre contenedores:**
```bash
# Desde contenedor 1 a contenedor 2
ping 172.17.0.3

# Ver tabla ARP
arp -a
```

### **Verificar archivos en el contenedor:**
```bash
ls -la /app/
ls -la /app/downloads/
```

---

## 🧹 Limpieza del Entorno

### **Detener todos los contenedores:**
```powershell
docker stop test-chat test-chat-2 test-chat-3
```

### **Eliminar contenedores:**
```powershell
docker rm test-chat test-chat-2 test-chat-3
```

### **Limpiar imagen (opcional):**
```powershell
docker rmi link-chat
```

---

## ⚠️ Solución de Problemas Comunes

### **Error: "couldn't connect to display"**
- **Problema:** GUI no puede mostrarse
- **Solución:** Instalar VcXsrv o usar modo consola
- **Alternativa:** Testing sin GUI usando logs

### **Error: "Permission denied" para raw sockets**
- **Problema:** Faltan privilegios de red
- **Solución:** Verificar flags `--privileged` y `--cap-add NET_RAW`

### **Los nodos no se detectan**
- **Problema:** Discovery no funciona
- **Solución:** Verificar interfaces eth0 en cada contenedor
- **Debug:** Revisar logs de discovery en consola

### **Containers se detienen inmediatamente**
- **Problema:** Imagen Docker mal construida
- **Solución:** Reconstruir con `docker build --no-cache`

---

## 📊 Métricas de Testing Exitoso

✅ **Discovery:** Los 3 nodos se detectan mutuamente en <60 segundos  
✅ **Mensajería:** Mensajes broadcast llegan a todos los nodos  
✅ **Unicast:** Mensajes directos llegan solo al destinatario  
✅ **Archivos:** Transferencias completas sin corrupción  
✅ **Interfaces:** eth0 disponible en cada contenedor  
✅ **Performance:** Latencia <50ms entre contenedores  

---

## 🎉 ¡Testing Completado!

Si todos los pasos funcionan correctamente:
- **Funcionalidad básica:** ✅ Verificada
- **Comunicación P2P:** ✅ Funcionando  
- **Protocolo Ethernet:** ✅ Implementado correctamente
- **Arquitectura modular:** ✅ Organizada

**¡Tu Link-Chat 3.0 está listo para presentación y evaluación!** 🚀

---

## 📞 Soporte Adicional

Si encuentras problemas:
1. Verificar logs con comandos de debug
2. Revisar configuración Docker
3. Consultar documentación del proyecto
4. Verificar permisos de red y raw sockets