param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("setup", "start", "stop", "clean", "status", "terminals", "gui")]
    [string]$Action = "setup"
)

Write-Host "🚀 Link-Chat 3.0 - Docker Testing Automation" -ForegroundColor Cyan
Write-Host ""

function Write-Success($Message) {
    Write-Host "$Message" -ForegroundColor Green
}

function Write-Info($Message) {
    Write-Host "$Message" -ForegroundColor Blue
}

function Write-Warning($Message) {
    Write-Host "$Message" -ForegroundColor Yellow
}

function Write-Error($Message) {
    Write-Host "$Message" -ForegroundColor Red
}

function Build-DockerImage {
    Write-Info "Construyendo imagen Docker..."
    
    docker build -t link-chat -f docker/dockerfile .
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Imagen 'link-chat' construida exitosamente"
        return $true
    } else {
        Write-Error "Error construyendo la imagen Docker"
        return $false
    }
}

function Create-MacvlanNetwork {
    Write-Info "Creando red macvlan personalizada..."
    
    $networkExists = docker network ls --format "{{.Name}}" | Select-String -Pattern "^chat_macvlan$"
    
    if ($networkExists) {
        Write-Warning "Red 'chat_macvlan' ya existe, eliminándola..."
        
        $connectedContainers = docker network inspect chat_macvlan --format "{{range .Containers}}{{.Name}} {{end}}" 2>$null
        if ($connectedContainers) {
            $containerList = $connectedContainers.Split(' ')
            foreach ($container in $containerList) {
                if ($container.Trim()) {
                    docker network disconnect -f chat_macvlan $container.Trim() 2>$null
                }
            }
        }
        
        docker network rm chat_macvlan 2>$null
        Start-Sleep 2
    }
    
    docker network create --driver bridge --subnet=192.168.100.0/24 --gateway=192.168.100.1 chat_macvlan
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Red 'chat_macvlan' creada exitosamente"
        return $true
    } else {
        Write-Error "Error creando la red macvlan"
        return $false
    }
}

function Create-Containers {
    Write-Info "Creando 3 contenedores del sistema de mensajería..."
    
    docker stop link-chat-node-1 link-chat-node-2 link-chat-node-3 2>$null
    docker rm link-chat-node-1 link-chat-node-2 link-chat-node-3 2>$null
    
    # Verificar que existe la carpeta compartida
    $sharedFolder = "C:\LinkChat_SharedFiles"
    if (-not (Test-Path $sharedFolder)) {
        Write-Error "La carpeta compartida '$sharedFolder' no existe"
        return $false
    }
    
    Write-Info "Usando carpeta compartida: $sharedFolder"
    
    $containers = @(
        @{Name = "link-chat-node-1"; DisplayName = "Nodo Principal"; IP = "192.168.100.10"},
        @{Name = "link-chat-node-2"; DisplayName = "Nodo Secundario"; IP = "192.168.100.11"},
        @{Name = "link-chat-node-3"; DisplayName = "Nodo Terciario"; IP = "192.168.100.12"}
    )
    
    foreach ($container in $containers) {
        Write-Info "Creando $($container.DisplayName)..."
        
        $dockerCmd = @(
            "run", "-d", "--name", $container.Name,
            "--network", "chat_macvlan", 
            "--ip", $container.IP,
            "--privileged",
            "--cap-add", "NET_RAW",
            "--cap-add", "NET_ADMIN", 
            "--cap-add", "SYS_ADMIN",
            "-v", "${sharedFolder}:/app/shared_files",
            "-e", "NODE_NAME=$($container.DisplayName)",
            "-e", "DISPLAY=host.docker.internal:0.0",
            "-it", "link-chat"
        )
        
        & docker @dockerCmd
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "$($container.DisplayName) creado y ejecutándose"
        } else {
            Write-Error "Error creando $($container.DisplayName)"
            return $false
        }
        
        Start-Sleep 3
    }
    
    Write-Success "Los 3 contenedores han sido creados exitosamente"
    return $true
}

function Setup-XServer {
    Write-Info "Configurando servidor X11 para interfaces GUI..."
    
    $vcxsrv = Get-Command "vcxsrv.exe" -ErrorAction SilentlyContinue
    $xming = Get-Command "Xming.exe" -ErrorAction SilentlyContinue
    
    if ($vcxsrv) {
        $existingVcXsrv = Get-Process -Name "vcxsrv" -ErrorAction SilentlyContinue
        if (-not $existingVcXsrv) {
            Start-Process "vcxsrv.exe" -ArgumentList ":0", "-ac", "-terminate", "-lesspointer", "-multiwindow", "-clipboard", "-wgl" -WindowStyle Hidden
            Start-Sleep 5
            Write-Success "Servidor X11 iniciado"
        } else {
            Write-Success "Servidor X11 ya está ejecutándose"
        }
        return $true
    } elseif ($xming) {
        $existingXming = Get-Process -Name "Xming" -ErrorAction SilentlyContinue
        if (-not $existingXming) {
            Start-Process "Xming.exe" -ArgumentList ":0", "-clipboard", "-multiwindow" -WindowStyle Hidden
            Start-Sleep 5
            Write-Success "Servidor X11 iniciado"
        } else {
            Write-Success "Servidor X11 ya está ejecutándose"
        }
        return $true
    } else {
        Write-Warning "No se encontró servidor X11 (VcXsrv o Xming)"
        return $false
    }
}

function Open-ContainerTerminals {
    Write-Info "Abriendo 3 terminales para acceso directo a contenedores..."
    
    $containers = @("link-chat-node-1", "link-chat-node-2", "link-chat-node-3")
    $nodeNames = @("Nodo Principal", "Nodo Secundario", "Nodo Terciario")
    
    for ($i = 0; $i -lt $containers.Length; $i++) {
        $containerName = $containers[$i]
        $nodeName = $nodeNames[$i]
        
        $dockerExecCmd = "docker exec -it $containerName bash"
        $terminalTitle = "Link-Chat 3.0 - $nodeName"
        
        $psCommand = @"
`$Host.UI.RawUI.WindowTitle = '$terminalTitle'
Write-Host '🚀 $terminalTitle' -ForegroundColor Cyan
Write-Host 'Conectando al contenedor...' -ForegroundColor Blue
$dockerExecCmd
"@
        
        Start-Process "pwsh.exe" -ArgumentList "-NoExit", "-Command", $psCommand
        Start-Sleep 2
    }
    
    Write-Success "Las 3 terminales han sido abiertas exitosamente"
    return $true
}

function Start-Applications {
    Write-Info "Iniciando aplicaciones en cada contenedor..."
    
    $containers = @(
        @{ Name = "link-chat-node-1"; DisplayName = "Nodo Principal" },
        @{ Name = "link-chat-node-2"; DisplayName = "Nodo Secundario" },
        @{ Name = "link-chat-node-3"; DisplayName = "Nodo Terciario" }
    )
    
    foreach ($container in $containers) {
        try {
            docker exec -d $container.Name python3 app.py
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Aplicación iniciada en $($container.DisplayName)"
            }
        }
        catch {
            Write-Error "Error al iniciar aplicación en $($container.DisplayName)"
        }
        Start-Sleep 1
    }
    
    Write-Success "Aplicaciones iniciadas en todos los contenedores"
    return $true
}

function Wait-ForApplications {
    Write-Info "Esperando que las aplicaciones GUI se inicien..."
    
    for ($i = 5; $i -gt 0; $i--) {
        Write-Host "⏳ Esperando $i segundos..." -ForegroundColor Yellow
        Start-Sleep 1
    }
    
    docker ps --filter "name=link-chat-node" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    return $true
}

function Stop-Containers {
    Write-Info "Deteniendo todos los contenedores..."
    docker stop link-chat-node-1 link-chat-node-2 link-chat-node-3 2>$null
    Write-Success "Contenedores detenidos"
}

function Remove-Everything {
    Write-Info "Limpiando entorno completo..."
    
    docker stop link-chat-node-1 link-chat-node-2 link-chat-node-3 2>$null
    docker rm link-chat-node-1 link-chat-node-2 link-chat-node-3 2>$null
    docker rmi link-chat 2>$null
    
    $networkExists = docker network ls --format "{{.Name}}" | Select-String -Pattern "^chat_macvlan$"
    if ($networkExists) {
        docker network rm chat_macvlan 2>$null
    }
    
    $downloadDirs = @(".\downloads\downloads1", ".\downloads\downloads2", ".\downloads\downloads3")
    foreach ($dir in $downloadDirs) {
        if (Test-Path $dir) {
            Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    
    Write-Success "Entorno completamente limpio"
}

function Show-Status {
    Write-Info "ESTADO ACTUAL DEL ENTORNO"
    
    Write-Info "CONTENEDORES:"
    docker ps -a --filter "name=link-chat-node" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}" 2>$null
    
    Write-Info "IMÁGENES:"
    docker images link-chat --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" 2>$null
    
    Write-Info "REDES:"
    docker network ls --filter "name=chat_macvlan" --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}" 2>$null
}

function Start-FullSetup {
    Write-Info "INICIANDO CONFIGURACIÓN COMPLETA AUTOMÁTICA"
    
    if (-not (Build-DockerImage)) { return $false }
    if (-not (Create-MacvlanNetwork)) { return $false }
    
    Setup-XServer
    
    if (-not (Create-Containers)) { return $false }
    if (-not (Open-ContainerTerminals)) { return $false }
    if (-not (Start-Applications)) { return $false }
    Wait-ForApplications
    
    Write-Success "CONFIGURACIÓN COMPLETA EXITOSA"
    Write-Info "Red configurada: 192.168.100.10, 192.168.100.11, 192.168.100.12"
    
    return $true
}

Write-Info "Verificando Docker..."
try {
    docker --version | Out-Null
    Write-Success "Docker está disponible ✓"
} catch {
    Write-Error "Docker no está instalado o no está ejecutándose"
    exit 1
}

switch ($Action) {
    "setup" {
        Write-Info "Ejecutando configuración completa automática con GUI..."
        Start-FullSetup
    }
    "start" {
        Write-Info "Iniciando solo contenedores..."
        if (-not (Create-Containers)) {
            Write-Error "Error iniciando contenedores"
            exit 1
        }
    }
    "stop" {
        Write-Info "Deteniendo contenedores..."
        Stop-Containers
    }
    "clean" {
        Write-Info "Limpiando entorno completo..."
        Remove-Everything
    }
    "status" {
        Write-Info "Mostrando estado del sistema..."
        Show-Status
    }
    "terminals" {
        Write-Info "Abriendo solo terminales..."
        Open-ContainerTerminals
    }
    default {
        Write-Warning "Acción no reconocida: $Action"
        Show-Status
    }
}

Write-Info "Script completado - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"