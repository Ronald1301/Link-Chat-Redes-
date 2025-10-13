#!/usr/bin/env python3
"""
Módulo de Discovery Automático para Link-Chat
Implementa identificación automática de dispositivos en la red
"""

import threading
import time
import json
from typing import Dict, Callable, Optional

class DiscoveryManager:
    def __init__(self, comunicador, callback_device_found: Optional[Callable] = None):
        """
        Inicializa el manager de discovery
        
        Args:
            comunicador: Instancia de Envio_recibo_frames
            callback_device_found: Función callback cuando se encuentra un dispositivo
        """
        self.com = comunicador
        self.callback_device_found = callback_device_found
        self.discovered_devices: Dict[str, dict] = {}
        self.running = False
        self.discovery_thread = None
        self.heartbeat_interval = 30  # segundos
        self.device_timeout = 90  # segundos
        
        # Información del dispositivo local
        self.local_info = {
            'hostname': self._get_hostname(),
            'mac': self.com.mac_ori,
            'timestamp': time.time(),
            'capabilities': ['text', 'file', 'broadcast']
        }
    
    def _get_hostname(self) -> str:
        """Obtiene el nombre del host"""
        try:
            import socket
            return socket.gethostname()
        except:
            return "LinkChat-Device"
    
    def start_discovery(self):
        """Inicia el proceso de discovery automático"""
        if self.running:
            return
        
        self.running = True
        self.discovery_thread = threading.Thread(target=self._discovery_loop, daemon=True)
        self.discovery_thread.start()
        print("🔍 Discovery automático iniciado")
    
    def stop_discovery(self):
        """Detiene el proceso de discovery"""
        self.running = False
        if self.discovery_thread and self.discovery_thread.is_alive():
            self.discovery_thread.join(timeout=2)
        print("🔍 Discovery automático detenido")
    
    def _discovery_loop(self):
        """Loop principal del discovery"""
        while self.running:
            try:
                # Enviar heartbeat
                self._send_heartbeat()
                
                # Limpiar dispositivos antiguos
                self._cleanup_old_devices()
                
                # Esperar antes del siguiente heartbeat
                for _ in range(self.heartbeat_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                print(f"❌ Error en discovery loop: {e}")
                time.sleep(5)
    
    def _send_heartbeat(self):
        """Envía mensaje de heartbeat para anunciar presencia"""
        try:
            # Crear mensaje de heartbeat
            heartbeat_data = {
                'type': 'HEARTBEAT',
                'hostname': self.local_info['hostname'],
                'mac': self.local_info['mac'],
                'timestamp': time.time(),
                'capabilities': self.local_info['capabilities']
            }
            
            mensaje = f"DISCOVERY:{json.dumps(heartbeat_data)}"
            
            # Enviar como broadcast
            frames = self.com.crear_frame(
                "FF:FF:FF:FF:FF:FF",  # Broadcast
                1,  # Tipo texto
                mensaje
            )
            
            self.com.enviar_protocolo(frames)
            print(f"📡 Heartbeat enviado: {self.local_info['hostname']}")
            
        except Exception as e:
            print(f"❌ Error enviando heartbeat: {e}")
    
    def process_discovery_message(self, mac_origen: str, mensaje: str) -> bool:
        """
        Procesa mensajes de discovery recibidos
        
        Args:
            mac_origen: MAC del dispositivo origen
            mensaje: Mensaje recibido
            
        Returns:
            bool: True si era un mensaje de discovery, False si no
        """
        try:
            if not mensaje.startswith("DISCOVERY:"):
                return False
            
            # Extraer datos JSON
            json_data = mensaje[10:]  # Quitar "DISCOVERY:"
            data = json.loads(json_data)
            
            # Validar que sea un heartbeat
            if data.get('type') != 'HEARTBEAT':
                return False
            
            # No procesar nuestros propios mensajes
            if mac_origen.upper() == self.com.mac_ori.upper():
                return True
            
            # Actualizar información del dispositivo
            device_info = {
                'hostname': data.get('hostname', 'Unknown'),
                'mac': mac_origen.upper(),
                'last_seen': time.time(),
                'capabilities': data.get('capabilities', []),
                'status': 'active'
            }
            
            # Verificar si es un dispositivo nuevo
            is_new_device = mac_origen.upper() not in self.discovered_devices
            
            # Actualizar lista de dispositivos
            self.discovered_devices[mac_origen.upper()] = device_info
            
            # Notificar si es un dispositivo nuevo
            if is_new_device and self.callback_device_found:
                self.callback_device_found(device_info)
            
            print(f"📱 Dispositivo actualizado: {device_info['hostname']} ({mac_origen})")
            return True
            
        except Exception as e:
            print(f"❌ Error procesando mensaje de discovery: {e}")
            return False
    
    def _cleanup_old_devices(self):
        """Elimina dispositivos que no han respondido recientemente"""
        current_time = time.time()
        devices_to_remove = []
        
        for mac, info in self.discovered_devices.items():
            if current_time - info['last_seen'] > self.device_timeout:
                devices_to_remove.append(mac)
        
        for mac in devices_to_remove:
            device_info = self.discovered_devices[mac]
            print(f"⏰ Dispositivo desconectado: {device_info['hostname']} ({mac})")
            del self.discovered_devices[mac]
    
    def get_discovered_devices(self) -> Dict[str, dict]:
        """Retorna la lista de dispositivos descubiertos"""
        return self.discovered_devices.copy()
    
    def send_discovery_request(self):
        """Envía una solicitud activa de discovery"""
        try:
            request_data = {
                'type': 'DISCOVERY_REQUEST',
                'mac': self.local_info['mac'],
                'timestamp': time.time()
            }
            
            mensaje = f"DISCOVERY:{json.dumps(request_data)}"
            
            frames = self.com.crear_frame(
                "FF:FF:FF:FF:FF:FF",  # Broadcast
                1,  # Tipo texto
                mensaje
            )
            
            self.com.enviar_protocolo(frames)
            print("🔍 Solicitud de discovery enviada")
            
        except Exception as e:
            print(f"❌ Error enviando solicitud de discovery: {e}")
    
    def get_device_count(self) -> int:
        """Retorna el número de dispositivos activos"""
        return len(self.discovered_devices)
    
    def is_device_active(self, mac: str) -> bool:
        """Verifica si un dispositivo específico está activo"""
        mac_upper = mac.upper()
        if mac_upper not in self.discovered_devices:
            return False
        
        device = self.discovered_devices[mac_upper]
        return (time.time() - device['last_seen']) < self.device_timeout