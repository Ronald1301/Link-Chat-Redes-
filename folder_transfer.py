#!/usr/bin/env python3
"""
Módulo de Transferencia de Carpetas para Link-Chat
Permite enviar y recibir carpetas completas con estructura de directorios
"""

import os
import zipfile
import tempfile
import shutil
from typing import List, Dict, Optional, Callable
import time
import json

class FolderTransfer:
    def __init__(self, chat_app):
        """
        Inicializa el gestor de transferencia de carpetas
        
        Args:
            chat_app: Instancia de la aplicación de chat
        """
        self.chat_app = chat_app
        self.temp_dir = tempfile.gettempdir()
        self.carpetas_en_progreso: Dict[str, dict] = {}
        
    def send_folder(self, folder_path: str, dest_mac: str, progress_callback: Optional[Callable] = None) -> tuple:
        """
        Envía una carpeta completa comprimida
        
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
            
            # Crear archivo ZIP temporal
            zip_filename = f"{folder_name}_{int(time.time())}.zip"
            zip_path = os.path.join(self.temp_dir, zip_filename)
            
            # Comprimir carpeta
            total_files = self._count_files(folder_path)
            files_processed = 0
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_name = os.path.relpath(file_path, folder_path)
                        zipf.write(file_path, arc_name)
                        
                        files_processed += 1
                        if progress_callback:
                            progress = (files_processed / total_files) * 50  # 50% para compresión
                            progress_callback(progress, f"Comprimiendo: {file}")
            
            # Obtener información del archivo comprimido
            zip_size = os.path.getsize(zip_path)
            
            # Enviar metadata de carpeta
            folder_metadata = {
                'type': 'FOLDER_METADATA',
                'original_name': folder_name,
                'zip_name': zip_filename,
                'total_files': total_files,
                'compressed_size': zip_size,
                'timestamp': time.time()
            }
            
            metadata_msg = f"FOLDER_TRANSFER:{json.dumps(folder_metadata)}"
            
            # Enviar metadata
            frames_metadata = self.chat_app.com.crear_frame(
                dest_mac,
                2,  # Tipo archivo
                metadata_msg.encode('utf-8'),
                zip_filename
            )
            self.chat_app.com.enviar_frame(frames_metadata)
            
            if progress_callback:
                progress_callback(60, "Enviando archivo comprimido...")
            
            # Enviar el archivo ZIP usando FileTransfer existente
            success, message = self.chat_app.file_transfer.send_file(zip_path, dest_mac)
            
            # Limpiar archivo temporal
            try:
                os.remove(zip_path)
            except:
                pass
            
            if success:
                if progress_callback:
                    progress_callback(100, "Carpeta enviada exitosamente")
                return True, f"Carpeta '{folder_name}' enviada exitosamente"
            else:
                return False, f"Error enviando carpeta: {message}"
                
        except Exception as e:
            return False, f"Error procesando carpeta: {str(e)}"
    
    def _count_files(self, folder_path: str) -> int:
        """Cuenta el total de archivos en una carpeta"""
        count = 0
        for root, dirs, files in os.walk(folder_path):
            count += len(files)
        return count
    
    def receive_folder_metadata(self, mensaje: str, source_mac: str) -> bool:
        """
        Procesa metadata de carpeta recibida
        
        Args:
            mensaje: Mensaje con metadata
            source_mac: MAC del remitente
            
        Returns:
            bool: True si se procesó correctamente
        """
        try:
            if not mensaje.startswith("FOLDER_TRANSFER:"):
                return False
            
            # Extraer metadata JSON
            json_data = mensaje[16:]  # Quitar "FOLDER_TRANSFER:"
            metadata = json.loads(json_data)
            
            if metadata.get('type') != 'FOLDER_METADATA':
                return False
            
            # Almacenar información de la carpeta esperada
            self.carpetas_en_progreso[source_mac] = {
                'original_name': metadata['original_name'],
                'zip_name': metadata['zip_name'],
                'total_files': metadata['total_files'],
                'compressed_size': metadata['compressed_size'],
                'timestamp': time.time(),
                'status': 'waiting_zip'
            }
            
            # Notificar al usuario
            mensaje_usuario = f"Recibiendo carpeta: {metadata['original_name']} ({metadata['total_files']} archivos)"
            if hasattr(self.chat_app, 'root'):
                self.chat_app.root.after(100, 
                    lambda: self.chat_app.mostrar_mensaje("Sistema", mensaje_usuario))
            
            return True
            
        except Exception as e:
            print(f"❌ Error procesando metadata de carpeta: {e}")
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
            if source_mac not in self.carpetas_en_progreso:
                return False
            
            folder_info = self.carpetas_en_progreso[source_mac]
            file_name = os.path.basename(file_path)
            
            # Verificar si es el archivo ZIP esperado
            if file_name == folder_info['zip_name'] and file_path.endswith('.zip'):
                # Extraer la carpeta
                success = self._extract_folder(file_path, folder_info, source_mac)
                
                # Limpiar información temporal
                del self.carpetas_en_progreso[source_mac]
                
                return success
            
            return False
            
        except Exception as e:
            print(f"❌ Error verificando archivo de carpeta: {e}")
            return False
    
    def _extract_folder(self, zip_path: str, folder_info: dict, source_mac: str) -> bool:
        """
        Extrae el contenido de la carpeta recibida
        
        Args:
            zip_path: Ruta del archivo ZIP
            folder_info: Información de la carpeta
            source_mac: MAC del remitente
            
        Returns:
            bool: True si se extrajo correctamente
        """
        try:
            # Crear directorio de destino
            downloads_dir = "descargas"
            folder_name = folder_info['original_name']
            extract_path = os.path.join(downloads_dir, folder_name)
            
            # Si la carpeta ya existe, agregar un número
            contador = 1
            original_extract_path = extract_path
            while os.path.exists(extract_path):
                extract_path = f"{original_extract_path}_{contador}"
                contador += 1
            
            # Crear directorio
            os.makedirs(extract_path, exist_ok=True)
            
            # Extraer contenido
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(extract_path)
            
            # Eliminar archivo ZIP temporal
            try:
                os.remove(zip_path)
            except:
                pass
            
            # Notificar éxito
            extracted_files = self._count_files(extract_path)
            mensaje = f"Carpeta extraída: {folder_name} ({extracted_files} archivos) en {os.path.basename(extract_path)}"
            
            if hasattr(self.chat_app, 'root'):
                self.chat_app.root.after(100,
                    lambda: self.chat_app.mostrar_mensaje("Sistema", mensaje))
            
            print(f"✅ Carpeta extraída exitosamente: {extract_path}")
            return True
            
        except Exception as e:
            error_msg = f"Error extrayendo carpeta: {str(e)}"
            if hasattr(self.chat_app, 'root'):
                self.chat_app.root.after(100,
                    lambda: self.chat_app.mostrar_mensaje("Error", error_msg))
            print(f"❌ {error_msg}")
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
            temp_pattern = os.path.join(self.temp_dir, "*.zip")
            
            import glob
            for temp_file in glob.glob(temp_pattern):
                try:
                    file_time = os.path.getmtime(temp_file)
                    # Eliminar archivos temporales más antiguos de 1 hora
                    if current_time - file_time > 3600:
                        os.remove(temp_file)
                        print(f"🗑️ Archivo temporal eliminado: {temp_file}")
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Error limpiando archivos temporales: {e}")