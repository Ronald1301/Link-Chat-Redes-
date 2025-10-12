# Link-Chat 2.0 - Script Automático de Testing Docker
# ====================================================

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("setup", "start", "stop", "clean", "status")]
    [string]$Action = "setup"
)

Write-Host "🚀 Link-Chat 2.0 - Docker Testing Automation" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
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

function Setup-Environment {
    Write-Info "Configurando entorno de testing..."
    
    # Limpiar contenedores existentes
    Write-Info "Limpiando contenedores previos..."
    docker stop test-chat test-chat-2 test-chat-3 2>$null
    docker rm test-chat test-chat-2 test-chat-3 2>$null
    
    # Construir imagen
    Write-Info "Construyendo imagen Docker..."
    docker build -t link-chat -f docker/dockerfile .
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Imagen construida exitosamente"
    } else {
        Write-Error "Error construyendo imagen"
        return $false
    }
    
    return $true
}

function Start-Containers {
    Write-Info "Iniciando contenedores..."
    
    # Crear contenedores
    $containers = @(
        @{Name="test-chat"; DisplayName="Nodo Principal"},
        @{Name="test-chat-2"; DisplayName="Nodo Secundario"},
        @{Name="test-chat-3"; DisplayName="Nodo Terciario"}
    )
    
    foreach ($container in $containers) {
        Write-Info "Creando $($container.DisplayName)..."
        docker run -dt --name $container.Name --privileged --cap-add NET_RAW --cap-add NET_ADMIN -e DISPLAY=host.docker.internal:0 link-chat bash
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "$($container.DisplayName) iniciado"
        } else {
            Write-Error "Error iniciando $($container.DisplayName)"
            return $false
        }
        
        Start-Sleep 1
    }
    
    # Verificar estado
    Write-Info "Verificando estado de contenedores..."
    docker ps --filter "name=test-chat" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    Write-Success "Todos los contenedores están activos"
    Write-Info ""
    Write-Info "PRÓXIMOS PASOS:"
    Write-Info "==============="
    Write-Info ""
    Write-Info "Abre 3 nuevas terminales PowerShell y ejecuta:"
    Write-Info ""
    Write-Info "Terminal 1: docker exec -it test-chat bash"
    Write-Info "Terminal 2: docker exec -it test-chat-2 bash" 
    Write-Info "Terminal 3: docker exec -it test-chat-3 bash"
    Write-Info ""
    Write-Info "En cada terminal del contenedor ejecuta:"
    Write-Info "cd /app && python3 app.py"
    
    return $true
}

function Stop-Containers {
    Write-Info "Deteniendo contenedores..."
    docker stop test-chat test-chat-2 test-chat-3
    Write-Success "Contenedores detenidos"
}

function Clean-Environment {
    Write-Info "Limpiando entorno completo..."
    docker stop test-chat test-chat-2 test-chat-3 2>$null
    docker rm test-chat test-chat-2 test-chat-3 2>$null
    docker rmi link-chat 2>$null
    Write-Success "Entorno limpiado"
}

function Show-Status {
    Write-Info "Estado actual del entorno:"
    Write-Info ""
    
    Write-Info "Contenedores activos:"
    docker ps --filter "name=test-chat" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>$null
    
    Write-Info ""
    Write-Info "Imágenes disponibles:"
    docker images | Select-String "link-chat"
    
    Write-Info ""
    Write-Info "Comandos disponibles:"
    Write-Info "  .\scripts\docker-test.ps1 setup   - Configurar entorno completo"
    Write-Info "  .\scripts\docker-test.ps1 start   - Solo iniciar contenedores"
    Write-Info "  .\scripts\docker-test.ps1 stop    - Detener contenedores"
    Write-Info "  .\scripts\docker-test.ps1 clean   - Limpiar todo"
    Write-Info "  .\scripts\docker-test.ps1 status  - Ver estado actual"
}

# Ejecutar acción solicitada
switch ($Action) {
    "setup" {
        if (Setup-Environment) {
            Start-Containers
        }
    }
    "start" {
        Start-Containers
    }
    "stop" {
        Stop-Containers
    }
    "clean" {
        Clean-Environment
    }
    "status" {
        Show-Status
    }
    default {
        Write-Warning "Acción no reconocida: $Action"
        Show-Status
    }
}

Write-Info ""
Write-Info "Script completado - $(Get-Date)"