import os
import time
from typing import Dict, Optional
from ..core.frames import Frame, Tipo_Mensaje
class FileTransfer:
    def __init__(self, chat_app):
        self.chat_app = chat_app
        self.archivos_en_progreso: Dict[str, dict] = {}
        self.archivos_recibiendo: Dict[str, dict] = {}
    
    def send_file(self, file_path, dest_mac):
        """Envía un archivo usando el sistema unificado de fragmentación"""
        try:
            if not os.path.exists(file_path):
                return False, "Archivo no encontrado"
            
            nombre_archivo = os.path.basename(file_path)
            tamaño_archivo = os.path.getsize(file_path)
            
            # Leer archivo completo en memoria (para archivos pequeños/medianos)
            # Para archivos muy grandes, se podría leer en partes más grandes
            with open(file_path, 'rb') as f:
                contenido_archivo = f.read()
            
            # Crear mensaje con metadata del archivo incluida
            metadata = f"FILE_TRANSFER:{nombre_archivo}:{tamaño_archivo}:".encode('utf-8')
            mensaje_completo = metadata + contenido_archivo
            
            print(f" Enviando archivo {nombre_archivo} ({tamaño_archivo} bytes)")
            
            # Usar el sistema unificado de fragmentación de frames
            # El sistema automáticamente fragmentará si es necesario
            # No pasamos nombre_archivo como parámetro separado porque ya está en el mensaje
            frames = self.chat_app.com.crear_frame(
                dest_mac,
                Tipo_Mensaje.archivo.value,
                mensaje_completo
            )
            
            # Enviar todos los frames (frames ya es una lista de bytes)
            self.chat_app.com.enviar_archivo(frames)
            print(f"Archivo {nombre_archivo} enviado en {len(frames)} frame(s)")
            
            return True, f"Archivo {nombre_archivo} enviado exitosamente"
            
        except Exception as e:
            return False, f"Error enviando archivo: {str(e)}"
    
    def receive_file(self, mensaje, source_mac):
        """Procesa la recepción de un archivo usando el sistema unificado"""
        
        try:
            print(f"FileTransfer.receive_file llamado: {len(mensaje)} bytes recibidos")
            
            # El mensaje ya viene reensamblado por el FragmentManager
            # Solo necesitamos procesar el contenido del archivo
            
            # Verificar si es un archivo con el nuevo formato
            if isinstance(mensaje, bytes) and mensaje.startswith(b"FILE_TRANSFER:"):
                # Manejar como bytes para preservar datos binarios
                self._procesar_archivo_unificado_bytes(mensaje, source_mac)
                return
            elif isinstance(mensaje, str) and mensaje.startswith("FILE_TRANSFER:"):
                # Manejar como string (solo para archivos de texto)
                self._procesar_archivo_unificado_str(mensaje, source_mac)
                return

            else:
                #  Formato no reconocido - solo logging, no procesamiento complejo
                print(f" Formato no reconocido. Primeros 50 bytes: {mensaje[:50]}")
                    #Limpiar
                    # del self.archivos_recibiendo[source_mac]
                    # print(f"Procesamiento completado para: {nombre}")
        except Exception as e:
            error_msg = f" Error guardando archivo: {str(e)}"
            self.chat_app.mostrar_mensaje("Error", error_msg)
            print(error_msg)

    def _guardar_archivo(self, archivo: dict, mac_origen: str):
        try:
            # Crear directorio de downloads si no existe
            download_dir = "downloads"
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
            
            # Generar nombre único
            nombre_base = archivo['nombre']
            nombre_archivo = os.path.join(download_dir, nombre_base)
            
            # Si el archivo ya existe, agregar un número
            contador = 1
            while os.path.exists(nombre_archivo):
                nombre, extension = os.path.splitext(nombre_base)
                nombre_archivo = os.path.join(download_dir, f"{nombre}_{contador}{extension}")
                contador += 1
            
            # Guardar archivo
            with open(nombre_archivo, 'wb') as f:
                f.write(archivo['datos'])
            
            # Verificar si es parte de una transferencia de carpeta
            if hasattr(self.chat_app, 'folder_transfer') and self.chat_app.folder_transfer:
                if self.chat_app.folder_transfer.check_folder_file_received(nombre_archivo, mac_origen):
                    # Era parte de una carpeta, ya fue procesado
                    return
            
            # Mostrar mensaje de éxito para archivo normal
            tamaño = len(archivo['datos'])
            mensaje = f"Archivo guardado: {nombre_base} ({tamaño} bytes)"
             # Usar after para programar la actualización de UI de forma segura
            if hasattr(self.chat_app, 'root'):
                self.chat_app.root.after(100, lambda: self.chat_app.mostrar_mensaje("Sistema", mensaje))
                
            print(f"Archivo guardado exitosamente: {nombre_archivo}")
            
        except Exception as e:
            error_msg = f"Error guardando archivo: {str(e)}"
            self.chat_app.mostrar_mensaje("Error", error_msg)
            print(error_msg)

    def _guardar_archivo_directo(self, nombre_archivo: str, contenido: bytes, mac_origen: str):
        """Guarda un archivo directamente usando el nuevo sistema unificado"""
        try:
            # Crear directorio de downloads si no existe
            download_dir = "downloads"
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
            
            # Generar nombre único
            nombre_base = nombre_archivo
            ruta_archivo = os.path.join(download_dir, nombre_base)
            
            # Si el archivo ya existe, agregar un número
            contador = 1
            while os.path.exists(ruta_archivo):
                nombre, extension = os.path.splitext(nombre_base)
                ruta_archivo = os.path.join(download_dir, f"{nombre}_{contador}{extension}")
                contador += 1
            
            # Guardar archivo
            with open(ruta_archivo, 'wb') as f:
                f.write(contenido)
            
            # Verificar si es parte de una transferencia de carpeta
            if hasattr(self.chat_app, 'folder_transfer') and self.chat_app.folder_transfer:
                if self.chat_app.folder_transfer.check_folder_file_received(ruta_archivo, mac_origen):
                    # Era parte de una carpeta, ya fue procesado
                    return
            
            # Mostrar mensaje de éxito para archivo normal
            tamaño = len(contenido)
            mensaje = f"Archivo recibido: {os.path.basename(ruta_archivo)} ({tamaño} bytes)"
            
            # Usar after para programar la actualización de UI de forma segura
            if hasattr(self.chat_app, 'root'):
                self.chat_app.root.after(100, 
                    lambda: self.chat_app.mostrar_mensaje("Sistema", mensaje))
                
            print(f"✅ Archivo guardado exitosamente: {ruta_archivo}")
            
        except Exception as e:
            error_msg = f"❌ Error guardando archivo {nombre_archivo}: {str(e)}"
            if hasattr(self.chat_app, 'root'):
                self.chat_app.root.after(100, 
                    lambda: self.chat_app.mostrar_mensaje("Error", error_msg))
            print(error_msg)
            import traceback
            traceback.print_exc()

    def _procesar_archivo_unificado_bytes(self, mensaje: bytes, source_mac: str):
        """Procesa archivo con formato FILE_TRANSFER: desde bytes (preserva datos binarios)"""
        try:
            # Buscar el fin del header para extraer metadatos
            header_end = mensaje.find(b':', 14)  # Buscar después de "FILE_TRANSFER:"
            if header_end == -1:
                print("Error: Formato FILE_TRANSFER inválido")
                return
            
            # Extraer nombre del archivo
            nombre_archivo = mensaje[14:header_end].decode('utf-8')
            
            # Buscar el siguiente ':'
            size_start = header_end + 1
            size_end = mensaje.find(b':', size_start)
            if size_end == -1:
                print(" Error: Formato FILE_TRANSFER inválido (tamaño)")
                return
            
            # Extraer tamaño del archivo
            tamaño_archivo = int(mensaje[size_start:size_end].decode('utf-8'))
            
            # El contenido empieza después del último ':'
            contenido_inicio = size_end + 1
            contenido_archivo = mensaje[contenido_inicio:]
            
            print(f" Archivo recibido: {nombre_archivo}")
            print(f"   → Tamaño esperado: {tamaño_archivo} bytes")
            print(f"   → Tamaño recibido: {len(contenido_archivo)} bytes")
            
            # Verificar integridad del tamaño
            if len(contenido_archivo) == tamaño_archivo:
                # Guardar archivo directamente
                self._guardar_archivo_directo(nombre_archivo, contenido_archivo, source_mac)
            else:
                error_msg = f"Error: Tamaño de archivo incorrecto. Esperado: {tamaño_archivo}, Recibido: {len(contenido_archivo)}"
                print(f" {error_msg}")
                if hasattr(self.chat_app, 'root'):
                    self.chat_app.root.after(100, 
                        lambda: self.chat_app.mostrar_mensaje("Error", error_msg))
        
        except Exception as e:
            print(f" Error procesando archivo desde bytes: {e}")
            import traceback
            traceback.print_exc()

    def _procesar_archivo_unificado_str(self, mensaje: str, source_mac: str):
        """Procesa archivo con formato FILE_TRANSFER: desde string (solo archivos de texto)"""
        try:
            # Buscar el separador después del tercer ':'
            parts = mensaje.split(":", 3)
            if len(parts) >= 4:
                nombre_archivo = parts[1]
                tamaño_archivo = int(parts[2])
                contenido_archivo = parts[3].encode('utf-8')  # Convertir a bytes
                
                print(f"Archivo de texto recibido: {nombre_archivo}")
                print(f"   → Tamaño esperado: {tamaño_archivo} bytes")
                print(f"   → Tamaño recibido: {len(contenido_archivo)} bytes")
                
                # Verificar integridad del tamaño
                if len(contenido_archivo) == tamaño_archivo:
                    # Guardar archivo directamente
                    self._guardar_archivo_directo(nombre_archivo, contenido_archivo, source_mac)
                else:
                    error_msg = f"Error: Tamaño de archivo incorrecto. Esperado: {tamaño_archivo}, Recibido: {len(contenido_archivo)}"
                    print(f"❌ {error_msg}")
                    if hasattr(self.chat_app, 'root'):
                        self.chat_app.root.after(100, 
                            lambda: self.chat_app.mostrar_mensaje("Error", error_msg))
        
        except Exception as e:
            print(f"❌ Error procesando archivo desde string: {e}")
            import traceback
            traceback.print_exc()