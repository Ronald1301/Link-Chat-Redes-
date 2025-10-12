#!/usr/bin/env python3
"""
Link-Chat 2.0 - Modo Consola (Sin GUI)
Para testing rápido en contenedores Docker sin X11
"""

import sys
import os
import time
import threading

# Agregar path para importaciones
sys.path.insert(0, '/app')

from src.core.frames import Tipo_Mensaje
from src.core.env_recb import Envio_recibo_frames
from src.features.files import FileTransfer
from src.core.mac import Mac
from src.features.discovery import DiscoveryManager
from src.features.folder_transfer import FolderTransfer
from src.features.simple_security import SimpleSecurityManager

class LinkChatConsole:
    def __init__(self, interface="eth0"):
        print("🚀 Link-Chat 2.0 - Modo Consola")
        print("=" * 40)
        
        self.interface = interface
        self.running = True
        self.nodo_nombre = os.environ.get('NODE_NAME', f'Contenedor-{os.getpid()}')
        
        # Inicializar componentes
        self.mac_manager = Mac()
        self.mi_mac = self.mac_manager.obtener_mac_interfaz(interface)
        
        print(f"📡 Interfaz: {interface}")
        print(f"🏷️  MAC: {self.mi_mac}")
        print(f"👤 Nombre: {self.nodo_nombre}")
        print("-" * 40)
        
        # Inicializar comunicación
        self.env_recb = Envio_recibo_frames(interface, self.procesar_mensaje)
        
        # Inicializar discovery
        self.discovery = DiscoveryManager(
            self.mi_mac, 
            self.nodo_nombre,
            self.env_recb.enviar_frame,
            self.actualizar_dispositivos
        )
        
        # Lista de dispositivos detectados
        self.dispositivos = {}
        
    def procesar_mensaje(self, frame_data, mac_origen):
        """Procesa mensajes recibidos"""
        try:
            frame = self.env_recb.deserializar_frame(frame_data)
            tipo = frame.tipo_mensaje
            
            if tipo == Tipo_Mensaje.TEXTO:
                mensaje = frame.datos.decode('utf-8', errors='ignore')
                timestamp = time.strftime('%H:%M:%S')
                print(f"📨 [{timestamp}] {mac_origen}: {mensaje}")
                
            elif tipo == Tipo_Mensaje.DISCOVERY:
                # El discovery manager maneja esto
                pass
                
            elif tipo == Tipo_Mensaje.HEARTBEAT:
                # Actualizar último contacto
                if mac_origen in self.dispositivos:
                    self.dispositivos[mac_origen]['ultimo_contacto'] = time.time()
                    
        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}")
    
    def actualizar_dispositivos(self, dispositivos):
        """Callback para actualizar lista de dispositivos detectados"""
        self.dispositivos = dispositivos
        print(f"🔍 Dispositivos detectados: {len(dispositivos)}")
        for mac, info in dispositivos.items():
            print(f"   • {info['nombre']} ({mac})")
    
    def enviar_mensaje(self, mensaje, mac_destino=None):
        """Envía mensaje broadcast o unicast"""
        try:
            if mac_destino:
                # Mensaje unicast
                self.env_recb.enviar_mensaje_texto(mensaje, mac_destino)
                print(f"📤 Enviado a {mac_destino}: {mensaje}")
            else:
                # Mensaje broadcast  
                self.env_recb.enviar_mensaje_broadcast(mensaje)
                print(f"📢 Broadcast: {mensaje}")
                
        except Exception as e:
            print(f"❌ Error enviando mensaje: {e}")
    
    def mostrar_ayuda(self):
        """Muestra comandos disponibles"""
        print("\n📋 Comandos disponibles:")
        print("  /help          - Mostrar esta ayuda")
        print("  /devices       - Lista dispositivos detectados")
        print("  /broadcast <msg> - Enviar mensaje broadcast")
        print("  /send <mac> <msg> - Enviar mensaje a MAC específica")
        print("  /status        - Estado del sistema")
        print("  /quit          - Salir")
        print("")
    
    def mostrar_dispositivos(self):
        """Muestra dispositivos detectados"""
        print(f"\n🔍 Dispositivos detectados ({len(self.dispositivos)}):")
        if not self.dispositivos:
            print("   (Ninguno detectado aún - espera 30-60 segundos)")
        else:
            for mac, info in self.dispositivos.items():
                ultimo = time.time() - info.get('ultimo_contacto', 0)
                print(f"   • {info['nombre']} ({mac}) - hace {ultimo:.0f}s")
        print("")
    
    def mostrar_status(self):
        """Muestra estado del sistema"""
        print(f"\n📊 Estado del Sistema:")
        print(f"   Interfaz: {self.interface}")
        print(f"   MAC: {self.mi_mac}")
        print(f"   Nombre: {self.nodo_nombre}")
        print(f"   Dispositivos: {len(self.dispositivos)}")
        print(f"   Discovery: {'✅ Activo' if self.discovery else '❌ Inactivo'}")
        print("")
    
    def run(self):
        """Bucle principal de la aplicación"""
        print("\n🎯 Link-Chat iniciado. Escribe /help para comandos.")
        print("⏳ Esperando discovery automático (30-60 segundos)...")
        print("")
        
        # Iniciar discovery
        self.discovery.iniciar()
        
        try:
            while self.running:
                try:
                    entrada = input(f"{self.nodo_nombre}> ").strip()
                    
                    if entrada.startswith('/'):
                        # Procesar comandos
                        partes = entrada.split(' ', 2)
                        comando = partes[0].lower()
                        
                        if comando == '/help':
                            self.mostrar_ayuda()
                        elif comando == '/devices':
                            self.mostrar_dispositivos()
                        elif comando == '/status':
                            self.mostrar_status()
                        elif comando == '/quit':
                            break
                        elif comando == '/broadcast':
                            if len(partes) > 1:
                                mensaje = ' '.join(partes[1:])
                                self.enviar_mensaje(mensaje)
                            else:
                                print("❌ Uso: /broadcast <mensaje>")
                        elif comando == '/send':
                            if len(partes) > 2:
                                mac_destino = partes[1]
                                mensaje = ' '.join(partes[2:])
                                self.enviar_mensaje(mensaje, mac_destino)
                            else:
                                print("❌ Uso: /send <mac> <mensaje>")
                        else:
                            print(f"❌ Comando desconocido: {comando}")
                            
                    elif entrada:
                        # Mensaje broadcast por defecto
                        self.enviar_mensaje(entrada)
                        
                except KeyboardInterrupt:
                    break
                except EOFError:
                    break
                    
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Limpieza al salir"""
        print("\n🛑 Cerrando Link-Chat...")
        self.running = False
        if self.discovery:
            self.discovery.detener()
        if self.env_recb:
            self.env_recb.detener()
        print("✅ Link-Chat cerrado")

if __name__ == "__main__":
    interface = sys.argv[1] if len(sys.argv) > 1 else "eth0"
    
    try:
        chat = LinkChatConsole(interface)
        chat.run()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)