# Link-Chat 3.0 - Script Automático de Testing Docker
# ====================================================
# Script completo sin dependencia de docker-compose
# Flujo: Dockerfile → Imagen → Contenedores → Red → GUI automática

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("setup", "start", "stop", "clean", "status", "terminals", "gui")]
    [string]$Action = "setup"
)

Write-Host "🚀 Link-Chat 3.0 - Docker Testing Automation" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "✨ SIN DOCKER-COMPOSE - Todo integrado en el script" -ForegroundColor Magenta
Write-Host "🖼️  CON TKINTER GUI - Interfaz automática" -ForegroundColor Green
Write-Host ""

function Write-Success($Message) {
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Info($Message) {
    Write-Host "📋 $Message" -ForegroundColor Blue
}

function Write-Warning($Message) {
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error($Message) {
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Build-DockerImage {
    Write-Info "PASO 1: Construyendo imagen Docker desde dockerfile..."
    Write-Info "Comando: docker build -t link-chat -f docker/dockerfile ."
    Write-Info "Explicación: Crea una imagen llamada 'link-chat' usando el dockerfile del directorio docker/"
    
    docker build -t link-chat -f docker/dockerfile .
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✨ Imagen 'link-chat' construida exitosamente"
        
        # Mostrar información de la imagen
        Write-Info "Información de la imagen creada:"
        docker images link-chat --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
        return $true
    } else {
        Write-Error "Error construyendo la imagen Docker"
        return $false
    }
}

function Create-MacvlanNetwork {
    Write-Info "PASO 2: Creando red macvlan personalizada..."
    
    # Limpiar red existente completamente
    Write-Info "Verificando y limpiando red existente..."
    $networkExists = docker network ls --format "{{.Name}}" | Select-String -Pattern "^chat_macvlan$"
    
    if ($networkExists) {
        Write-Warning "Red 'chat_macvlan' ya existe, eliminándola completamente..."
        
        # Desconectar todos los contenedores de la red primero
        $connectedContainers = docker network inspect chat_macvlan --format "{{range .Containers}}{{.Name}} {{end}}" 2>$null
        if ($connectedContainers) {
            $containerList = $connectedContainers.Split(' ')
            foreach ($container in $containerList) {
                if ($container.Trim()) {
                    Write-Info "Desconectando contenedor: $($container.Trim())"
                    docker network disconnect -f chat_macvlan $container.Trim() 2>$null
                }
            }
        }
        
        # Eliminar la red
        docker network rm chat_macvlan 2>$null
        Start-Sleep 2
    }
    
    Write-Info "Comando: docker network create --driver bridge --subnet=192.168.100.0/24 --gateway=192.168.100.1 chat_macvlan"
    Write-Info "Explicación: Crea una red bridge personalizada con subred 192.168.100.0/24"
    Write-Info "           - Driver bridge: Permite comunicación entre contenedores"
    Write-Info "           - Subnet: Define el rango de IPs disponibles (192.168.100.1-254)"
    Write-Info "           - Gateway: IP del router de la red (192.168.100.1)"
    
    docker network create --driver bridge --subnet=192.168.100.0/24 --gateway=192.168.100.1 chat_macvlan
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✨ Red 'chat_macvlan' creada exitosamente"
        return $true
    } else {
        Write-Error "Error creando la red macvlan"
        return $false
    }
}

function Create-Containers {
    Write-Info "PASO 3: Creando 3 contenedores del sistema de mensajería..."
    
    # Limpiar contenedores existentes primero
    Write-Info "Limpiando contenedores previos si existen..."
    docker stop link-chat-node-1 link-chat-node-2 link-chat-node-3 2>$null
    docker rm link-chat-node-1 link-chat-node-2 link-chat-node-3 2>$null
    
    # Definir configuración de contenedores
    $containers = @(
        @{
            Name = "link-chat-node-1"
            DisplayName = "Nodo Principal"
            IP = "192.168.100.10"
            VolumeDir = "downloads1"
        },
        @{
            Name = "link-chat-node-2" 
            DisplayName = "Nodo Secundario"
            IP = "192.168.100.11"
            VolumeDir = "downloads2"
        },
        @{
            Name = "link-chat-node-3"
            DisplayName = "Nodo Terciario" 
            IP = "192.168.100.12"
            VolumeDir = "downloads3"
        }
    )
    
    # Crear directorios de descarga si no existen
    foreach ($container in $containers) {
        $downloadPath = ".\downloads\$($container.VolumeDir)"
        if (-not (Test-Path $downloadPath)) {
            New-Item -ItemType Directory -Path $downloadPath -Force | Out-Null
            Write-Info "Directorio $downloadPath creado"
        }
    }
    
    # Crear cada contenedor
    foreach ($container in $containers) {
        Write-Info ""
        Write-Info "Creando $($container.DisplayName) ($($container.Name))..."
        
        $dockerCmd = @(
            "run", "-d", "--name", $container.Name,
            "--network", "chat_macvlan", 
            "--ip", $container.IP,
            "--privileged",
            "--cap-add", "NET_RAW",
            "--cap-add", "NET_ADMIN", 
            "--cap-add", "SYS_ADMIN",
            "-v", "$(Get-Location)\downloads\$($container.VolumeDir):/app/downloads",
            "-e", "NODE_NAME=$($container.DisplayName)",
            "-e", "DISPLAY=host.docker.internal:0.0",
            "-it",
            "link-chat"
        )
        
        Write-Info "Comando: docker $($dockerCmd -join ' ')"
        Write-Info "Explicación del comando:"
        Write-Info "  - run -d: Ejecuta el contenedor en segundo plano"
        Write-Info "  - --name: Asigna nombre único al contenedor"
        Write-Info "  - --network: Conecta a la red personalizada 'chat_macvlan'"
        Write-Info "  - --ip: Asigna IP fija ($($container.IP))"
        Write-Info "  - --privileged: Permite acceso completo al sistema (necesario para networking)"
        Write-Info "  - --cap-add: Añade capacidades específicas:"
        Write-Info "    * NET_RAW: Permite crear sockets raw (mensajería de bajo nivel)"
        Write-Info "    * NET_ADMIN: Permite administrar interfaces de red"
        Write-Info "    * SYS_ADMIN: Permite operaciones administrativas del sistema"
        Write-Info "  - -v: Monta volumen para compartir archivos de descarga"
        Write-Info "  - -e: Variables de entorno (NODE_NAME y DISPLAY para X11)"
        Write-Info "  - -it: Modo interactivo con terminal"
        Write-Info "  - El contenedor ejecutará automáticamente: python3 app.py"
        
        # Ejecutar el comando
        & docker @dockerCmd
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "✨ $($container.DisplayName) creado y ejecutándose con aplicación GUI"
        } else {
            Write-Error "Error creando $($container.DisplayName)"
            return $false
        }
        
        Start-Sleep 3
    }
    
    Write-Success "✨ Los 3 contenedores han sido creados exitosamente"
    return $true
}

function Setup-XServer {
    Write-Info "🖼️  PASO 4: Configurando servidor X11 para interfaces GUI..."
    Write-Info "Explicación: Windows necesita un servidor X11 para mostrar aplicaciones Linux GUI"
    
    # Verificar si VcXsrv está instalado
    $vcxsrv = Get-Command "vcxsrv.exe" -ErrorAction SilentlyContinue
    $xming = Get-Command "Xming.exe" -ErrorAction SilentlyContinue
    
    if ($vcxsrv) {
        Write-Info "✅ VcXsrv encontrado, iniciando servidor X11..."
        Write-Info "Comando: vcxsrv.exe :0 -ac -terminate -lesspointer -multiwindow -clipboard -wgl"
        Write-Info "Explicación:"
        Write-Info "  - :0: Display número 0"
        Write-Info "  - -ac: Permitir conexiones de cualquier host"
        Write-Info "  - -terminate: Terminar cuando se cierre la última aplicación"
        Write-Info "  - -multiwindow: Cada ventana Linux como ventana Windows separada"
        Write-Info "  - -clipboard: Compartir clipboard entre Windows y Linux"
        
        # Verificar si ya hay un proceso VcXsrv ejecutándose
        $existingVcXsrv = Get-Process -Name "vcxsrv" -ErrorAction SilentlyContinue
        if (-not $existingVcXsrv) {
            Start-Process "vcxsrv.exe" -ArgumentList ":0", "-ac", "-terminate", "-lesspointer", "-multiwindow", "-clipboard", "-wgl" -WindowStyle Hidden
            Start-Sleep 5
            Write-Success "✨ Servidor X11 iniciado"
        } else {
            Write-Success "✨ Servidor X11 ya está ejecutándose"
        }
        return $true
        
    } elseif ($xming) {
        Write-Info "✅ Xming encontrado, iniciando servidor X11..."
        $existingXming = Get-Process -Name "Xming" -ErrorAction SilentlyContinue
        if (-not $existingXming) {
            Start-Process "Xming.exe" -ArgumentList ":0", "-clipboard", "-multiwindow" -WindowStyle Hidden
            Start-Sleep 5
            Write-Success "✨ Servidor X11 iniciado"
        } else {
            Write-Success "✨ Servidor X11 ya está ejecutándose"
        }
        return $true
        
    } else {
        Write-Warning "❌ No se encontró servidor X11 (VcXsrv o Xming)"
        Write-Info "💡 Para ver las interfaces GUI, instala VcXsrv desde:"
        Write-Info "   https://sourceforge.net/projects/vcxsrv/"
        Write-Info "💡 O instala Xming desde:"
        Write-Info "   https://sourceforge.net/projects/xming/"
        Write-Info ""
        Write-Info "🔄 Las aplicaciones se ejecutarán pero las ventanas no se mostrarán"
        Write-Info "🔄 Puedes instalar X11 después y usar las terminales para relanzar"
        return $false
    }
}

function Open-ContainerTerminals {
    Write-Info "PASO 5: Abriendo 3 terminales para acceso directo a contenedores..."
    Write-Info "Cada terminal te permitirá interactuar directamente con un nodo"
    
    $containers = @("link-chat-node-1", "link-chat-node-2", "link-chat-node-3")
    $nodeNames = @("Nodo Principal", "Nodo Secundario", "Nodo Terciario")
    
    for ($i = 0; $i -lt $containers.Length; $i++) {
        $containerName = $containers[$i]
        $nodeName = $nodeNames[$i]
        
        Write-Info "Abriendo terminal para $nodeName ($containerName)..."
        
        # Comando que se ejecutará en la nueva terminal
        $dockerExecCmd = "docker exec -it $containerName bash"
        $terminalTitle = "Link-Chat 3.0 - $nodeName"
        
        Write-Info "Comando: $dockerExecCmd"
        Write-Info "Explicación:"
        Write-Info "  - docker exec: Ejecuta comando en contenedor en ejecución"
        Write-Info "  - -it: Modo interactivo con terminal"
        Write-Info "  - ${containerName}: Nombre del contenedor objetivo"
        Write-Info "  - bash: Shell que se abrirá para interactuar"
        
        # Abrir nueva terminal PowerShell con el comando
        $psCommand = @"
`$Host.UI.RawUI.WindowTitle = '$terminalTitle'
Write-Host '🚀 $terminalTitle' -ForegroundColor Cyan
Write-Host '================================' -ForegroundColor Cyan
Write-Host 'La aplicación Link-Chat debería estar ejecutándose automáticamente' -ForegroundColor Green
Write-Host 'Si no aparece la interfaz gráfica:' -ForegroundColor Yellow
Write-Host '1. Instala VcXsrv (servidor X11 para Windows)' -ForegroundColor Yellow
Write-Host '2. Ejecuta: cd /app && python3 app.py' -ForegroundColor Yellow
Write-Host '' 
Write-Host 'Conectando al contenedor...' -ForegroundColor Blue
$dockerExecCmd
"@
        
        Start-Process "pwsh.exe" -ArgumentList "-NoExit", "-Command", $psCommand
        
        Write-Success "✨ Terminal abierta para $nodeName"
        Start-Sleep 2
    }
    
    Write-Success "✨ Las 3 terminales han sido abiertas exitosamente"
    return $true
}

function Start-Applications {
    Write-Info "🚀 PASO 5.5: Iniciando aplicaciones en cada contenedor..."
    Write-Info "Ejecutando 'python3 app.py' automáticamente en cada nodo..."
    
    $containers = @(
        @{ Name = "link-chat-node-1"; DisplayName = "Nodo Principal" },
        @{ Name = "link-chat-node-2"; DisplayName = "Nodo Secundario" },
        @{ Name = "link-chat-node-3"; DisplayName = "Nodo Terciario" }
    )
    
    foreach ($container in $containers) {
        Write-Info "Iniciando aplicación en $($container.DisplayName) ($($container.Name))..."
        Write-Info "Comando: docker exec -d $($container.Name) python3 app.py"
        Write-Info "Explicación: Ejecuta la aplicación de mensajería en segundo plano"
        
        try {
            docker exec -d $container.Name python3 app.py
            if ($LASTEXITCODE -eq 0) {
                Write-Success "✨ Aplicación iniciada en $($container.DisplayName)"
            } else {
                Write-Warning "⚠️  Posible problema al iniciar en $($container.DisplayName)"
            }
        }
        catch {
            Write-Error "❌ Error al iniciar aplicación en $($container.DisplayName): $_"
        }
        Start-Sleep 1
    }
    
    Write-Success "✨ Aplicaciones iniciadas en todos los contenedores"
    Write-Info "💡 Las interfaces GUI deberían aparecer en unos segundos..."
    return $true
}

function Wait-ForApplications {
    Write-Info "PASO 6: Esperando que las aplicaciones GUI se inicien..."
    Write-Info "Las aplicaciones deberían aparecer en unos momentos..."
    
    # Esperar un poco para que las aplicaciones se inicien
    for ($i = 10; $i -gt 0; $i--) {
        Write-Host "⏳ Esperando $i segundos para que aparezcan las ventanas..." -ForegroundColor Yellow
        Start-Sleep 1
    }
    
    Write-Info ""
    Write-Info "🖼️  VERIFICACIÓN DE INTERFACES GUI:"
    Write-Info "=================================="
    Write-Info "✅ Si ves 3 ventanas de Link-Chat: ¡Todo funcionó perfecto!"
    Write-Info "❌ Si no aparecen las ventanas:"
    Write-Info "   1. Instala VcXsrv: https://sourceforge.net/projects/vcxsrv/"
    Write-Info "   2. Ejecuta VcXsrv con configuración por defecto"
    Write-Info "   3. Usa las terminales abiertas para ejecutar: python3 app.py"
    Write-Info ""
    Write-Info "📱 ESTADO DE LOS CONTENEDORES:"
    docker ps --filter "name=link-chat-node" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    return $true
}

function Stop-Containers {
    Write-Info "Deteniendo todos los contenedores..."
    Write-Info "Comando: docker stop link-chat-node-1 link-chat-node-2 link-chat-node-3"
    Write-Info "Explicación: Detiene graciosamente los 3 contenedores del sistema"
    
    docker stop link-chat-node-1 link-chat-node-2 link-chat-node-3 2>$null
    Write-Success "✨ Contenedores detenidos"
}

function Remove-Everything {
    Write-Info "Limpiando entorno completo..."
    
    # Detener contenedores
    Write-Info "Deteniendo contenedores..."
    docker stop link-chat-node-1 link-chat-node-2 link-chat-node-3 2>$null
    
    # Eliminar contenedores
    Write-Info "Eliminando contenedores..."
    docker rm link-chat-node-1 link-chat-node-2 link-chat-node-3 2>$null
    
    # Eliminar imagen
    Write-Info "Eliminando imagen link-chat..."
    docker rmi link-chat 2>$null
    
    # Eliminar red macvlan
    $networkExists = docker network ls --format "{{.Name}}" | Select-String -Pattern "^chat_macvlan$"
    if ($networkExists) {
        Write-Info "Eliminando red chat_macvlan..."
        docker network rm chat_macvlan 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Red chat_macvlan eliminada"
        }
    }
    
    # Limpiar directorios de descarga
    $downloadDirs = @(".\downloads\downloads1", ".\downloads\downloads2", ".\downloads\downloads3")
    foreach ($dir in $downloadDirs) {
        if (Test-Path $dir) {
            Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
            Write-Info "Directorio $dir eliminado"
        }
    }
    
    Write-Success "✨ Entorno completamente limpiado"
}

function Show-Status {
    Write-Info "📊 ESTADO ACTUAL DEL ENTORNO"
    Write-Info "============================"
    Write-Info ""
    
    # Estado de contenedores
    Write-Info "🐳 CONTENEDORES:"
    $containers = docker ps -a --filter "name=link-chat-node" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}" 2>$null
    if ($containers) {
        $containers
    } else {
        Write-Warning "No hay contenedores de Link-Chat"
    }
    
    Write-Info ""
    Write-Info "🖼️  IMÁGENES:"
    $images = docker images link-chat --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" 2>$null
    if ($images) {
        $images
    } else {
        Write-Warning "No hay imagen link-chat"
    }
    
    Write-Info ""
    Write-Info "🌐 REDES:"
    $network = docker network ls --filter "name=chat_macvlan" --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}" 2>$null
    if ($network) {
        $network
        Write-Info ""
        Write-Info "Detalles de la red chat_macvlan:"
        docker network inspect chat_macvlan --format "Subnet: {{range .IPAM.Config}}{{.Subnet}}{{end}}" 2>$null
        docker network inspect chat_macvlan --format "Gateway: {{range .IPAM.Config}}{{.Gateway}}{{end}}" 2>$null
    } else {
        Write-Warning "No hay red chat_macvlan"
    }
    
    Write-Info ""
    Write-Info "🛠️  COMANDOS DISPONIBLES:"
    Write-Info "========================"
    Write-Info "  .\scripts\docker-test.ps1 setup      - 🚀 Configuración completa automática con GUI"
    Write-Info "  .\scripts\docker-test.ps1 start      - ▶️  Solo iniciar contenedores"
    Write-Info "  .\scripts\docker-test.ps1 stop       - ⏹️  Detener contenedores"
    Write-Info "  .\scripts\docker-test.ps1 clean      - 🧹 Limpiar todo completamente"
    Write-Info "  .\scripts\docker-test.ps1 status     - 📊 Ver estado actual"
    Write-Info "  .\scripts\docker-test.ps1 terminals  - 🖥️  Solo abrir terminales"
}

function Start-FullSetup {
    Write-Info "🚀 INICIANDO CONFIGURACIÓN COMPLETA AUTOMÁTICA"
    Write-Info "=============================================="
    Write-Info "Flujo completo:"
    Write-Info "1. 🏗️  Construir imagen Docker desde dockerfile"
    Write-Info "2. 🌐 Crear red macvlan personalizada"  
    Write-Info "3. 🐳 Crear 3 contenedores"
    Write-Info "4. 🖼️  Configurar servidor X11 para interfaces GUI"
    Write-Info "5. 🖥️  Abrir 3 terminales para acceso directo"
    Write-Info "6. 🚀 Ejecutar aplicaciones automáticamente en cada contenedor"
    Write-Info "7. ⏳ Esperar que aparezcan las interfaces Tkinter"
    Write-Info ""
    
    # Ejecutar todos los pasos
    if (-not (Build-DockerImage)) { return $false }
    if (-not (Create-MacvlanNetwork)) { return $false }
    
    # Configurar X11 ANTES de crear contenedores
    Setup-XServer
    
    if (-not (Create-Containers)) { return $false }
    if (-not (Open-ContainerTerminals)) { return $false }
    if (-not (Start-Applications)) { return $false }
    Wait-ForApplications
    
    Write-Success ""
    Write-Success "🎉 ¡CONFIGURACIÓN COMPLETA EXITOSA!"
    Write-Success "===================================="
    Write-Success "✨ 3 Contenedores ejecutándose con Link-Chat"
    Write-Success "✨ 3 Terminales abiertas para acceso directo"
    Write-Success "✨ Aplicaciones GUI iniciadas automáticamente"
    Write-Success ""
    Write-Info "🖼️  Las interfaces de Tkinter deberían aparecer ahora"
    Write-Info "🌐 Red configurada:"
    Write-Info "   - Nodo Principal:   192.168.100.10"
    Write-Info "   - Nodo Secundario:  192.168.100.11"
    Write-Info "   - Nodo Terciario:   192.168.100.12"
    Write-Info ""
    Write-Info "🔧 Si las ventanas no aparecen:"
    Write-Info "   1. Instala VcXsrv desde: https://sourceforge.net/projects/vcxsrv/"
    Write-Info "   2. Ejecuta VcXsrv con configuración por defecto"
    Write-Info "   3. Las aplicaciones se relanzarán automáticamente"
    
    return $true
}

# ====================================================================
# EJECUCIÓN PRINCIPAL DEL SCRIPT
# ====================================================================

Write-Info "Verificando Docker..."
try {
    docker --version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker no está disponible"
    }
    Write-Success "Docker está disponible ✓"
} catch {
    Write-Error "❌ Docker no está instalado o no está ejecutándose"
    Write-Error "Por favor instala Docker Desktop y asegúrate de que esté ejecutándose"
    exit 1
}

Write-Info ""

# Ejecutar acción solicitada
switch ($Action) {
    "setup" {
        Write-Info "🎯 Ejecutando configuración completa automática con GUI..."
        Start-FullSetup
    }
    "start" {
        Write-Info "🎯 Iniciando solo contenedores..."
        if (-not (Create-Containers)) {
            Write-Error "Error iniciando contenedores"
            exit 1
        }
    }
    "stop" {
        Write-Info "🎯 Deteniendo contenedores..."
        Stop-Containers
    }
    "clean" {
        Write-Info "🎯 Limpiando entorno completo..."
        Remove-Everything
    }
    "status" {
        Write-Info "🎯 Mostrando estado del sistema..."
        Show-Status
    }
    "terminals" {
        Write-Info "🎯 Abriendo solo terminales..."
        Open-ContainerTerminals
    }
    default {
        Write-Warning "Acción no reconocida: $Action"
        Show-Status
    }
}

Write-Info ""
Write-Info "✨ Script completado - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Info ""
Write-Info "💡 RESUMEN DE LO QUE HACE EL SCRIPT:"
Write-Info "==================================="
Write-Info "🏗️  docker build     - Construye imagen desde dockerfile"
Write-Info "🌐 docker network   - Crea red personalizada para comunicación"
Write-Info "🐳 docker run       - Crea contenedores que ejecutan automáticamente app.py"
Write-Info "🖼️  vcxsrv/xming    - Configura servidor X11 para mostrar GUI en Windows"
Write-Info "🖥️  Start-Process   - Abre terminales PowerShell para acceso directo"
Write-Info "⚡ El dockerfile ejecuta automáticamente: python3 app.py"
