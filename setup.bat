@echo off
echo Configurando Link-Chat para Docker en Windows...

:: Crear directorio para archivos compartidos
if not exist LinkChat_Files mkdir LinkChat_Files

:: Construir y ejecutar el contenedor
echo Construyendo la imagen de Docker...
docker-compose build

echo.
echo Ejecutar con: docker-compose up
echo.
echo IMPORTANTE: Necesitas Xming o VcXsrv para la interfaz grafica
echo.
pause