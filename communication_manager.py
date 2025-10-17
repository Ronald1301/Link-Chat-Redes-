import threading
import tkinter as tk
import time
import queue
from src.core.env_recb import Envio_recibo_frames
from src.core.frames import Tipo_Mensaje
from src.features.discovery import DiscoveryManager
from src.features.simple_security import SimpleSecurityManager
from src.features.folder_transfer import FolderTransfer

class CommunicationManager:
    def __init__(self, app):
        self.app = app
        self.com = None
        self.stop_event = None
        self.receive_thread = None
        self.discovery_manager = None
        self.security_manager = None
        self.folder_transfer = None
        self.ejecutando_recepcion = False

    def conectar(self, interfaz):
        """Conecta usando la interfaz seleccionada"""
        self.stop_event = threading.Event()
        self.com = Envio_recibo_frames(interfaz=interfaz)
        mac_propia = self.com.mac_ori
        
        # Inicializar nuevos módulos
        self.discovery_manager = DiscoveryManager(
            self.com, 
            callback_device_found=self.app.on_device_discovered
        )
        self.folder_transfer = FolderTransfer(self.app)
        self.security_manager = SimpleSecurityManager(self.app)
        
        # Iniciar discovery automático
        self.discovery_manager.start_discovery()
        
        self.receive_thread = threading.Thread(
            target=self.com.receive_thread,
            args=(self.stop_event,),  
            daemon=True
        )
        self.receive_thread.start()
        return mac_propia

    def desconectar(self):
        """Desconecta la comunicación"""
        if self.stop_event:
            self.stop_event.set()
        if self.discovery_manager:
            self.discovery_manager.stop_discovery()
        if self.security_manager:
            self.security_manager.disable_security()
        if self.com:
            self.com.stop()

    def enviar_mensaje(self, mensaje, destino):
        """Envía mensaje de texto"""
        if not self.com:
            return False

        # Verificar si se debe cifrar el mensaje
        mensaje_final = mensaje
        if (self.security_manager and 
            self.security_manager.has_secure_channel(destino) and
            destino != "FF:FF:FF:FF:FF:FF"):
            
            encrypted_msg = self.security_manager.encrypt_message(mensaje, destino)
            if encrypted_msg:
                mensaje_final = encrypted_msg
                self.app.mostrar_mensaje("Yo 🔒", f"→ {mensaje}")
            else:
                self.app.mostrar_mensaje("Yo", f"→ {mensaje}")
        else:
            self.app.mostrar_mensaje("Yo", f"→ {mensaje}")
        
        # Crear y enviar frame
        frames = self.com.crear_frame(destino, Tipo_Mensaje.texto, mensaje_final)
        
        if frames:
            self.com.enviar_frame(frames, contar_como_mensaje_usuario=True)
            return True
        return False

    def enviar_mensaje(self, mensaje, destino):
        """Envía mensaje de texto"""
        if not self.com:
            return False

        try:
            mensaje_final = mensaje
            
            # Verificar si se debe cifrar el mensaje
            if (self.security_manager and 
                self.security_manager.has_secure_channel(destino) and
                destino != "FF:FF:FF:FF:FF:FF"):  # No cifrar broadcast
                
                encrypted_msg = self.security_manager.encrypt_message(mensaje, destino)
                if encrypted_msg:
                    mensaje_final = encrypted_msg
                    self.app.mostrar_mensaje("Yo 🔒", f"→ {mensaje}")  # Mostrar mensaje original
                else:
                    self.app.mostrar_mensaje("Yo", f"→ {mensaje}")
            else:
                self.app.mostrar_mensaje("Yo", f"→ {mensaje}")

            # Crear y enviar frame
            frames = self.com.crear_frame(destino, Tipo_Mensaje.texto, mensaje_final)
            
            if frames:
                self.com.enviar_frame(frames, contar_como_mensaje_usuario=True)
                return True
            
            return False

        except Exception as e:
            self.app.mostrar_mensaje("Error", f"Error enviando mensaje: {str(e)}")
            return False
    
    def obtener_estadisticas(self):
        """Obtiene estadísticas del sistema"""
        if not self.com:
            return {}
        
        estadisticas = self.com.obtener_estadisticas()
        
        if self.discovery_manager:
            device_count = self.discovery_manager.get_device_count()
            estadisticas['dispositivos_descubiertos'] = device_count
        
        if self.security_manager:
            security_status = self.security_manager.get_security_status()
            estadisticas.update(security_status)
        
        return estadisticas

    def reiniciar_estadisticas(self):
        """Reinicia las estadísticas"""
        if self.com:
            self.com.reiniciar_estadisticas()

    def poll_incoming(self):
        """Revisa si hay frames en la cola (método del original)"""
        try:
            while not self.com.cola_mensajes.empty():
                decoded_frame = self.com.cola_mensajes.get()
                print(f"🔔 Frame obtenido de cola: tipo {decoded_frame.tipo_mensaje}")

                if decoded_frame.tipo_mensaje == Tipo_Mensaje.texto:
                    print("📝 Mensaje de texto recibido")
                    mensaje = decoded_frame.datos
                    
                    # Convertir a string si es bytes
                    if isinstance(mensaje, bytes):
                        try:
                            mensaje = mensaje.decode('utf-8')
                        except:
                            mensaje = str(mensaje)
                    
                    self.app.procesar_mensaje_recibido_mejorado(decoded_frame.mac_origen, mensaje)
                
                elif decoded_frame.tipo_mensaje == Tipo_Mensaje.archivo:
                    print("📁 Frame de archivo recibido")
                    self.app.procesar_archivo_recibido(decoded_frame)
                else:
                    print(f"❓ Tipo de mensaje desconocido: {decoded_frame.tipo_mensaje}")

        except Exception as e:
            print(f"❌ Error en poll_incoming: {e}")