#!/usr/bin/env python3
"""
Módulo de Seguridad Simplificado para Link-Chat
Implementa cifrado básico usando solo librerías estándar de Python
"""

import os
import hashlib
import hmac
import json
import time
import secrets
import base64
from typing import Optional, Dict, Tuple, Union

class SimpleSecurityManager:
    """
    Gestiona seguridad básica usando solo librerías estándar de Python
    
    Funcionalidades:
    - Cifrado XOR con clave derivada
    - Autenticación HMAC-SHA256
    - Intercambio de claves simple
    - Verificación de integridad
    """
    
    def __init__(self, chat_app):
        """
        Inicializa el gestor de seguridad
        
        Args:
            chat_app: Instancia de la aplicación de chat
        """
        self.chat_app = chat_app
        self.session_keys: Dict[str, bytes] = {}  # MAC -> clave de sesión
        self.key_exchanges: Dict[str, dict] = {}  # Intercambios de clave activos
        self.security_enabled = False
        
        # Generar clave local
        self.local_key = secrets.token_bytes(32)
        self.public_token = hashlib.sha256(self.local_key).hexdigest()
    
    def enable_security(self) -> bool:
        """
        Habilita la capa de seguridad
        
        Returns:
            bool: True si se habilitó correctamente
        """
        try:
            self.security_enabled = True
            print("🔒 Seguridad básica habilitada")
            return True
        except Exception as e:
            print(f"❌ Error habilitando seguridad: {e}")
            return False
    
    def disable_security(self):
        """Deshabilita la capa de seguridad"""
        self.security_enabled = False
        self.session_keys.clear()
        self.key_exchanges.clear()
        print("🔓 Seguridad deshabilitada")
    
    def initiate_key_exchange(self, target_mac: str) -> bool:
        """
        Inicia intercambio de claves con un dispositivo
        
        Args:
            target_mac: MAC del dispositivo de destino
            
        Returns:
            bool: True si se inició correctamente
        """
        try:
            if not self.security_enabled:
                return False
            
            # Generar token temporal para este intercambio
            exchange_token = secrets.token_hex(16)
            
            # Crear solicitud de intercambio de claves
            key_exchange_data = {
                'type': 'SIMPLE_KEY_REQUEST',
                'public_token': self.public_token,
                'exchange_token': exchange_token,
                'timestamp': time.time(),
                'sender_mac': self.chat_app.com.mac_ori
            }
            
            # Guardar intercambio pendiente
            self.key_exchanges[target_mac] = {
                'status': 'waiting_response',
                'timestamp': time.time(),
                'exchange_token': exchange_token,
                'my_key': self.local_key
            }
            
            mensaje = f"SECURITY:{json.dumps(key_exchange_data)}"
            
            # Enviar solicitud
            frames = self.chat_app.com.crear_frame(
                target_mac,
                1,  # Tipo texto
                mensaje
            )
            
            self.chat_app.com.enviar_frame(frames)
            print(f"🔑 Solicitud de intercambio de claves enviada a {target_mac}")
            return True
            
        except Exception as e:
            print(f"❌ Error iniciando intercambio de claves: {e}")
            return False
    
    def process_security_message(self, mac_origen: str, mensaje: str) -> bool:
        """
        Procesa mensajes de seguridad recibidos
        
        Args:
            mac_origen: MAC del remitente
            mensaje: Mensaje de seguridad
            
        Returns:
            bool: True si era un mensaje de seguridad
        """
        try:
            if not mensaje.startswith("SECURITY:"):
                return False
            
            if not self.security_enabled:
                print("⚠️ Mensaje de seguridad recibido pero seguridad deshabilitada")
                return True
            
            # Extraer datos JSON
            json_data = mensaje[9:]  # Quitar "SECURITY:"
            data = json.loads(json_data)
            
            msg_type = data.get('type')
            
            if msg_type == 'SIMPLE_KEY_REQUEST':
                self._handle_simple_key_request(mac_origen, data)
            elif msg_type == 'SIMPLE_KEY_RESPONSE':
                self._handle_simple_key_response(mac_origen, data)
            elif msg_type == 'SECURE_MESSAGE':
                self._handle_secure_message(mac_origen, data)
            else:
                print(f"❓ Tipo de mensaje de seguridad desconocido: {msg_type}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error procesando mensaje de seguridad: {e}")
            return False
    
    def _handle_simple_key_request(self, mac_origen: str, data: dict):
        """Maneja solicitudes de intercambio de claves"""
        try:
            remote_token = data['public_token']
            exchange_token = data['exchange_token']
            
            # Crear clave de sesión combinando tokens
            combined = self.public_token + remote_token + exchange_token
            session_key = hashlib.sha256(combined.encode()).digest()
            
            # Almacenar clave de sesión
            self.session_keys[mac_origen] = session_key
            
            # Enviar respuesta
            response_data = {
                'type': 'SIMPLE_KEY_RESPONSE',
                'public_token': self.public_token,
                'exchange_token': exchange_token,
                'timestamp': time.time(),
                'sender_mac': self.chat_app.com.mac_ori
            }
            
            mensaje = f"SECURITY:{json.dumps(response_data)}"
            
            frames = self.chat_app.com.crear_frame(
                mac_origen,
                1,  # Tipo texto
                mensaje
            )
            
            self.chat_app.com.enviar_frame(frames)
            
            print(f"🔑 Clave de sesión establecida con {mac_origen}")
            
            # Notificar al usuario
            if hasattr(self.chat_app, 'mostrar_mensaje'):
                self.chat_app.mostrar_mensaje("Seguridad", f"Canal seguro establecido con {mac_origen}")
            
        except Exception as e:
            print(f"❌ Error manejando solicitud de clave: {e}")
    
    def _handle_simple_key_response(self, mac_origen: str, data: dict):
        """Maneja respuestas de intercambio de claves"""
        try:
            if mac_origen not in self.key_exchanges:
                print(f"⚠️ Respuesta de clave no solicitada desde {mac_origen}")
                return
            
            remote_token = data['public_token']
            exchange_token = data['exchange_token']
            exchange_info = self.key_exchanges[mac_origen]
            
            # Verificar token de intercambio
            if exchange_token != exchange_info['exchange_token']:
                print(f"❌ Token de intercambio inválido desde {mac_origen}")
                return
            
            # Crear clave de sesión
            combined = self.public_token + remote_token + exchange_token
            session_key = hashlib.sha256(combined.encode()).digest()
            
            # Almacenar clave de sesión
            self.session_keys[mac_origen] = session_key
            
            # Limpiar intercambio
            del self.key_exchanges[mac_origen]
            
            print(f"🔑 Clave de sesión establecida con {mac_origen}")
            
            # Notificar al usuario
            if hasattr(self.chat_app, 'mostrar_mensaje'):
                self.chat_app.mostrar_mensaje("Seguridad", f"Canal seguro establecido con {mac_origen}")
            
        except Exception as e:
            print(f"❌ Error manejando respuesta de clave: {e}")
    
    def encrypt_message(self, mensaje: str, target_mac: str) -> Optional[str]:
        """
        Cifra un mensaje usando XOR con clave derivada
        
        Args:
            mensaje: Mensaje a cifrar
            target_mac: MAC del destinatario
            
        Returns:
            str: Mensaje cifrado en formato JSON o None si falla
        """
        try:
            if not self.security_enabled or target_mac not in self.session_keys:
                return None
            
            session_key = self.session_keys[target_mac]
            message_bytes = mensaje.encode('utf-8')
            
            # Generar nonce aleatorio
            nonce = secrets.token_bytes(16)
            
            # Derivar clave de cifrado
            cipher_key = hashlib.sha256(session_key + nonce).digest()
            
            # Cifrar con XOR (repetir clave si es necesario)
            encrypted = bytearray()
            for i, byte in enumerate(message_bytes):
                encrypted.append(byte ^ cipher_key[i % len(cipher_key)])
            
            # Calcular HMAC para integridad
            hmac_key = hashlib.sha256(session_key + b'hmac').digest()
            mac = hmac.new(hmac_key, nonce + bytes(encrypted), hashlib.sha256).digest()
            
            # Crear mensaje seguro
            secure_data = {
                'type': 'SECURE_MESSAGE',
                'nonce': base64.b64encode(nonce).decode(),
                'encrypted': base64.b64encode(encrypted).decode(),
                'mac': base64.b64encode(mac).decode(),
                'timestamp': time.time(),
                'sender_mac': self.chat_app.com.mac_ori
            }
            
            return f"SECURITY:{json.dumps(secure_data)}"
            
        except Exception as e:
            print(f"❌ Error cifrando mensaje: {e}")
            return None
    
    def _handle_secure_message(self, mac_origen: str, data: dict) -> bool:
        """
        Maneja mensajes seguros recibidos
        
        Args:
            mac_origen: MAC del remitente
            data: Datos del mensaje seguro
            
        Returns:
            bool: True si se procesó correctamente
        """
        try:
            if mac_origen not in self.session_keys:
                print(f"⚠️ Mensaje seguro recibido sin clave de sesión desde {mac_origen}")
                return False
            
            session_key = self.session_keys[mac_origen]
            
            # Extraer componentes
            nonce = base64.b64decode(data['nonce'])
            encrypted = base64.b64decode(data['encrypted'])
            received_mac = base64.b64decode(data['mac'])
            
            # Verificar HMAC
            hmac_key = hashlib.sha256(session_key + b'hmac').digest()
            calculated_mac = hmac.new(hmac_key, nonce + encrypted, hashlib.sha256).digest()
            
            if not hmac.compare_digest(received_mac, calculated_mac):
                print(f"❌ HMAC inválido en mensaje de {mac_origen}")
                return False
            
            # Derivar clave de descifrado
            cipher_key = hashlib.sha256(session_key + nonce).digest()
            
            # Descifrar con XOR
            decrypted = bytearray()
            for i, byte in enumerate(encrypted):
                decrypted.append(byte ^ cipher_key[i % len(cipher_key)])
            
            # Decodificar mensaje
            mensaje = decrypted.decode('utf-8')
            
            # Mostrar mensaje descifrado
            if hasattr(self.chat_app, 'mostrar_mensaje'):
                self.chat_app.mostrar_mensaje(f"{mac_origen} 🔒", mensaje)
            
            return True
            
        except Exception as e:
            print(f"❌ Error descifrando mensaje: {e}")
            if hasattr(self.chat_app, 'mostrar_mensaje'):
                self.chat_app.mostrar_mensaje("Error", f"No se pudo descifrar mensaje de {mac_origen}")
            return False
    
    def has_secure_channel(self, mac: str) -> bool:
        """
        Verifica si existe un canal seguro con un dispositivo
        
        Args:
            mac: MAC del dispositivo
            
        Returns:
            bool: True si existe canal seguro
        """
        return self.security_enabled and mac in self.session_keys
    
    def get_security_status(self) -> dict:
        """
        Obtiene el estado actual de la seguridad
        
        Returns:
            dict: Información del estado de seguridad
        """
        return {
            'enabled': self.security_enabled,
            'secure_channels': len(self.session_keys),
            'active_exchanges': len(self.key_exchanges),
            'channels': list(self.session_keys.keys())
        }
    
    def cleanup_old_exchanges(self):
        """Limpia intercambios de clave antiguos"""
        current_time = time.time()
        timeout = 300  # 5 minutos
        
        exchanges_to_remove = []
        for mac, info in self.key_exchanges.items():
            if current_time - info['timestamp'] > timeout:
                exchanges_to_remove.append(mac)
        
        for mac in exchanges_to_remove:
            del self.key_exchanges[mac]
            print(f"⏰ Intercambio de clave expirado con {mac}")