#!/usr/bin/env python3
"""
Módulo de Transferencia de Carpetas para Link-Chat
Permite enviar y recibir carpetas completas con estructura de directorios
MÉTODO: Envío recursivo de archivos individuales (sin ZIP)
"""

import os
import shutil
from typing import List, Dict, Optional, Callable
import time
import json
from pathlib import Path
from ..core.frames import Tipo_Mensaje

class FolderTransfer:
    def __init__(self, chat_app):
        """
        Inicializa el gestor de transferencia de carpetas
        
        Args:
            chat_app: Instancia de la aplicación de chat
        """
        self.chat_app = chat_app
        self.carpetas_en_progreso: Dict[str, dict] = {}
        self.transferencias_activas: Dict[str, dict] = {}  # Transfer ID -> metadata
        
        # Configurar directorio de recepción
        self.receive_dir = "downloads"
        if not os.path.exists(self.receive_dir):
            os.makedirs(self.receive_dir)
        
    def send_folder(self, folder_path: str, dest_mac: str, progress_callback: Optional[Callable] = None) -> tuple:
        """
        Envía una carpeta completa usando transferencia recursiva de archivos
        
        Args:
            folder_path: Ruta de la carpeta a enviar
            dest_mac: MAC de destino
            progress_callback: Función callback para progreso
            
        Returns:
            tuple: (éxito: bool, mensaje: str)
        """
        try:
            if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
                return False, "La carpeta no existe o no es válida"
            
            folder_name = os.path.basename(folder_path)
            transfer_id = f"folder_{int(time.time())}_{hash(folder_path) % 10000}"
            
            # Escanear todos los archivos recursivamente
            file_list = self._scan_folder_recursive(folder_path)
            total_files = len(file_list)
            
            if total_files == 0:
                return False, "No hay archivos para transferir en la carpeta"
            
            # Enviar metadata de inicio de transferencia de carpeta
            folder_metadata = {
                'type': 'folder_start',
                'name': folder_name,
                'transfer_id': transfer_id,
                'total_files': total_files,
                'timestamp': int(time.time())
            }
            
            metadata_json = json.dumps(folder_metadata)
            metadata_frames = self.chat_app.com.crear_frame(
                dest_mac,
                Tipo_Mensaje.texto.value,
                f"FOLDER_START:{metadata_json}"
            )
            
            self.chat_app.com.enviar_frame(metadata_frames)
            
            # Enviar cada archivo individualmente con su ruta relativa
            files_sent = 0
            for relative_path, full_path in file_list:
                # Enviar información del archivo (ruta relativa)
                file_info = {
                    'type': 'folder_file',
                    'transfer_id': transfer_id,
                    'relative_path': relative_path,
                    'file_size': os.path.getsize(full_path)
                }
                
                file_info_json = json.dumps(file_info)
                file_info_frames = self.chat_app.com.crear_frame(
                    dest_mac,
                    Tipo_Mensaje.texto.value,
                    f"FOLDER_FILE:{file_info_json}"
                )
                
                self.chat_app.com.enviar_frame(file_info_frames)
                
                # Enviar el archivo usando el sistema existente
                success, message = self.chat_app.file_transfer.send_file(full_path, dest_mac)
                
                if not success:
                    return False, f"Error enviando archivo {relative_path}: {message}"
                
                files_sent += 1
                
                if progress_callback:
                    progress = (files_sent / total_files) * 100
                    progress_callback(progress, f"Enviando: {relative_path}")
            
            # Enviar metadata de finalización
            folder_end_metadata = {
                'type': 'folder_end',
                'transfer_id': transfer_id,
                'files_sent': files_sent
            }
            
            end_metadata_json = json.dumps(folder_end_metadata)
            end_metadata_frames = self.chat_app.com.crear_frame(
                dest_mac,
                Tipo_Mensaje.texto.value,
                f"FOLDER_END:{end_metadata_json}"
            )
            
            self.chat_app.com.enviar_frame(end_metadata_frames)
            
            if progress_callback:
                progress_callback(100, "Carpeta enviada exitosamente")
            
            return True, f"Carpeta '{folder_name}' enviada exitosamente ({files_sent} archivos)"
                
        except Exception as e:
            return False, f"Error procesando carpeta: {str(e)}"
    
    def _scan_folder_recursive(self, folder_path: str) -> list:
        """
        Escanea una carpeta recursivamente y retorna lista de archivos
        
        Args:
            folder_path: Ruta de la carpeta base
            
        Returns:
            list: Lista de tuplas (ruta_relativa, ruta_completa)
        """
        file_list = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, folder_path)
                file_list.append((relative_path, full_path))
        return file_list
    
    def handle_folder_message(self, mensaje: str, source_mac: str) -> bool:
        """
        Procesa mensajes relacionados con transferencia de carpetas
        
        Args:
            mensaje: Mensaje recibido
            source_mac: MAC del remitente
            
        Returns:
            bool: True si se procesó correctamente
        """
        try:
            if mensaje.startswith("FOLDER_START:"):
                return self._handle_folder_start(mensaje[13:], source_mac)
            elif mensaje.startswith("FOLDER_FILE:"):
                return self._handle_folder_file(mensaje[12:], source_mac)
            elif mensaje.startswith("FOLDER_END:"):
                return self._handle_folder_end(mensaje[11:], source_mac)
            
            return False
            
        except Exception as e:
            print(f"❌ Error procesando mensaje de carpeta: {e}")
            return False
    
    def _handle_folder_start(self, json_data: str, source_mac: str) -> bool:
        """Maneja el inicio de una transferencia de carpeta"""
        try:
            metadata = json.loads(json_data)
            transfer_id = metadata['transfer_id']
            
            # Crear directorio para la carpeta
            folder_name = metadata['name']
            folder_path = os.path.join(self.receive_dir, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            
            # Almacenar información de la transferencia
            self.carpetas_en_progreso[transfer_id] = {
                'name': folder_name,
                'path': folder_path,
                'total_files': metadata['total_files'],
                'files_received': 0,
                'files_info': {},
                'status': 'receiving',
                'timestamp': time.time(),
                'current_file_expected': None
            }
            
            # Notificar al usuario
            mensaje_usuario = f"📁 Recibiendo carpeta: {folder_name} ({metadata['total_files']} archivos)"
            if hasattr(self.chat_app, 'root'):
                self.chat_app.root.after(100, 
                    lambda: self.chat_app.mostrar_mensaje("Sistema", mensaje_usuario))
            
            return True
            
        except Exception as e:
            print(f"❌ Error iniciando recepción de carpeta: {e}")
            return False
    
    def _handle_folder_file(self, json_data: str, source_mac: str) -> bool:
        """Maneja información de archivo individual"""
        try:
            file_info = json.loads(json_data)
            transfer_id = file_info['transfer_id']
            
            if transfer_id in self.carpetas_en_progreso:
                folder_info = self.carpetas_en_progreso[transfer_id]
                
                # Establecer este como el archivo que estamos esperando recibir
                folder_info['current_file_expected'] = {
                    'relative_path': file_info['relative_path'],
                    'size': file_info['file_size']
                }
                
                # También almacenar en la lista general para referencia
                if 'files_info' not in folder_info:
                    folder_info['files_info'] = {}
                
                folder_info['files_info'][file_info['relative_path']] = {
                    'relative_path': file_info['relative_path'],
                    'size': file_info['file_size'],
                    'received': False
                }
            
            return True
            
        except Exception as e:
            print(f"❌ Error procesando info de archivo: {e}")
            return False
    
    def _handle_folder_end(self, json_data: str, source_mac: str) -> bool:
        """Maneja el final de una transferencia de carpeta"""
        try:
            end_info = json.loads(json_data)
            transfer_id = end_info['transfer_id']
            
            if transfer_id in self.carpetas_en_progreso:
                folder_info = self.carpetas_en_progreso[transfer_id]
                
                # Notificar finalización
                mensaje_usuario = f"✅ Carpeta '{folder_info['name']}' recibida completamente"
                if hasattr(self.chat_app, 'root'):
                    self.chat_app.root.after(100, 
                        lambda: self.chat_app.mostrar_mensaje("Sistema", mensaje_usuario))
                
                # Limpiar información temporal
                del self.carpetas_en_progreso[transfer_id]
            
            return True
            
        except Exception as e:
            print(f"❌ Error finalizando recepción de carpeta: {e}")
            return False
    
    def check_folder_file_received(self, file_path: str, source_mac: str) -> bool:
        """
        Verifica si un archivo recibido es parte de una transferencia de carpeta
        
        Args:
            file_path: Ruta del archivo recibido
            source_mac: MAC del remitente
            
        Returns:
            bool: True si se procesó como carpeta
        """
        try:
            # Buscar transferencias activas que estén esperando archivos
            for transfer_id, folder_info in self.carpetas_en_progreso.items():
                if folder_info.get('status') == 'receiving' and folder_info.get('current_file_expected'):
                    # Verificar si este es el archivo que estamos esperando
                    expected_info = folder_info['current_file_expected']
                    file_size = os.path.getsize(file_path)
                    
                    # Si el tamaño coincide, probablemente es nuestro archivo
                    if file_size == expected_info['size']:
                        return self._process_folder_file(file_path, transfer_id, folder_info, expected_info)
            
            return False
            
        except Exception as e:
            print(f"❌ Error verificando archivo de carpeta: {e}")
            return False
    
    def _process_folder_file(self, file_path: str, transfer_id: str, folder_info: dict, expected_info: dict) -> bool:
        """
        Procesa un archivo individual de una transferencia de carpeta
        """
        try:
            relative_path = expected_info['relative_path']
            
            # Crear directorio destino si es necesario
            dest_file_path = os.path.join(folder_info['path'], relative_path)
            dest_dir = os.path.dirname(dest_file_path)
            os.makedirs(dest_dir, exist_ok=True)
            
            # Mover el archivo a su ubicación final
            shutil.move(file_path, dest_file_path)
            
            # Marcar archivo como recibido
            if relative_path in folder_info['files_info']:
                folder_info['files_info'][relative_path]['received'] = True
            
            # Limpiar archivo esperado
            folder_info['current_file_expected'] = None
            
            # Actualizar contador
            folder_info['files_received'] += 1
            
            # Notificar progreso
            progress = (folder_info['files_received'] / folder_info['total_files']) * 100
            mensaje_progreso = f"📁 {folder_info['name']}: {folder_info['files_received']}/{folder_info['total_files']} archivos ({progress:.1f}%)"
            
            if hasattr(self.chat_app, 'root'):
                self.chat_app.root.after(100, 
                    lambda: self.chat_app.mostrar_mensaje("Sistema", mensaje_progreso))
            
            return True
            
        except Exception as e:
            print(f"❌ Error procesando archivo de carpeta: {e}")
            return False
    
    def get_folder_size(self, folder_path: str) -> tuple:
        """
        Obtiene información de tamaño de una carpeta
        
        Args:
            folder_path: Ruta de la carpeta
            
        Returns:
            tuple: (total_size: int, file_count: int)
        """
        try:
            total_size = 0
            file_count = 0
            
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
                        file_count += 1
            
            return total_size, file_count
            
        except Exception as e:
            print(f"❌ Error calculando tamaño de carpeta: {e}")
            return 0, 0
    
    def cleanup_temp_files(self):
        """Limpia archivos temporales antiguos"""
        try:
            current_time = time.time()
            
            # Limpiar transferencias de carpetas antigas (más de 1 hora)
            expired_transfers = []
            for transfer_id, folder_info in self.carpetas_en_progreso.items():
                if 'timestamp' in folder_info:
                    if current_time - folder_info['timestamp'] > 3600:
                        expired_transfers.append(transfer_id)
            
            for transfer_id in expired_transfers:
                del self.carpetas_en_progreso[transfer_id]
                print(f"🗑️ Transferencia de carpeta expirada eliminada: {transfer_id}")
                    
        except Exception as e:
            print(f"❌ Error limpiando archivos temporales: {e}")