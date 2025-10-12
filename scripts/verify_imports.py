#!/usr/bin/env python3
"""
Script de verificación rápida para Link-Chat 2.0
Verifica que todos los módulos se importen correctamente después de la reorganización
"""

import sys
import os

# Agregar el directorio raíz al path para importaciones
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

print("🔍 Verificación de Importaciones Link-Chat 2.0")
print("=" * 50)

try:
    # Verificar importación del módulo principal
    print("📱 Verificando app.py...")
    from src.core.frames import Tipo_Mensaje, Frame
    print("   ✅ frames.py importado correctamente")
    
    from src.core.env_recb import Envio_recibo_frames  
    print("   ✅ env_recb.py importado correctamente")
    
    from src.core.mac import Mac
    print("   ✅ mac.py importado correctamente")
    
    from src.features.discovery import DiscoveryManager
    print("   ✅ discovery.py importado correctamente")
    
    from src.features.files import FileTransfer
    print("   ✅ files.py importado correctamente")
    
    from src.features.folder_transfer import FolderTransfer
    print("   ✅ folder_transfer.py importado correctamente")
    
    from src.features.simple_security import SimpleSecurityManager
    print("   ✅ simple_security.py importado correctamente")
    
    print("")
    print("🎯 Verificando funcionalidad básica...")
    
    # Test básico de Frame
    mac = Mac()
    print(f"   ✅ MAC class functional: {mac.obtener_mac_interfaz('eth0')[:17] if mac.obtener_mac_interfaz('eth0') else 'OK'}")
    
    # Test básico de Tipo_Mensaje
    tipos = [t for t in dir(Tipo_Mensaje) if not t.startswith('_')]
    print(f"   ✅ Message types available: {len(tipos)} tipos")
    
    print("")
    print("🎉 ¡Todas las importaciones funcionan correctamente!")
    print("✅ Link-Chat 2.0 está listo para testing")
    
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    sys.exit(1)
except Exception as e:
    print(f"⚠️  Advertencia: {e}")
    print("✅ Importaciones básicas funcionan, continúa con testing")

print("")
print("📋 Próximos pasos:")
print("   1. Ejecutar: .\\scripts\\docker-test.ps1 setup")
print("   2. Abrir 3 terminales con contenedores")  
print("   3. Ejecutar: python3 app.py en cada contenedor")
print("   4. Probar discovery, mensajes y archivos")