import os
import time
from typing import Dict, Optional
from frames import Frame, Tipo_Mensaje
class FileTransfer:
    def __init__(self, chat_app):
        self.chat_app = chat_app
        self.archivos_en_progreso: Dict[str, dict] = {}
        self.archivos_recibiendo: Dict[str, dict] = {}
    
    def send_file(self, file_path, dest_mac): #Envía un archivo fragmentado
        try:
            if not os.path.exists(file_path):
                return False, "Archivo no encontrado"
            
            nombre_archivo = os.path.basename(file_path)
            tamaño_archivo = os.path.getsize(file_path)
            
            # Leer archivo en chunks
            chunk_size = 1400  # Tamaño ajustado para dejar espacio para headers
            chunks = []
            
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    chunks.append(chunk)
            
            # Enviar metadata primero
            metadata = f"FILE_METADATA:{nombre_archivo}:{tamaño_archivo}:{len(chunks)}"
            frames_metadata = self.chat_app.com.crear_frame(
                dest_mac, 
                Tipo_Mensaje.archivo.value, 
                metadata.encode('utf-8'),
                nombre_archivo
            )
            self.chat_app.com.enviar_frame(frames_metadata)
            
            # Enviar chunks
            for i, chunk in enumerate(chunks):
                chunk_data = f"FILE_CHUNK:{i}:{len(chunks)}:".encode('utf-8') + chunk
                frames_chunk = self.chat_app.com.crear_frame(
                    dest_mac,
                    Tipo_Mensaje.archivo.value,
                    chunk_data,
                    nombre_archivo
                )
                self.chat_app.com.enviar_frame(frames_chunk)
                time.sleep(0.01)  # Pequeña pausa para no saturar
            
            # Enviar fin de transmisión
            end_data = f"FILE_END:{nombre_archivo}".encode('utf-8')
            frames_end = self.chat_app.com.crear_frame(
                dest_mac,
                Tipo_Mensaje.archivo.value,
                end_data,
                nombre_archivo
            )
            self.chat_app.com.enviar_frame(frames_end)
            
            return True, f"Archivo {nombre_archivo} enviado exitosamente"
            
        except Exception as e:
            return False, f"Error enviando archivo: {str(e)}"
    
    def receive_file(self, mensaje, source_mac): #Procesa la recepción de un archivo fragmentado
        try:
            print(f"📨 FileTransfer.receive_file llamado: {mensaje[:100]}...")
            
            if mensaje.startswith("FILE_METADATA:"):
                # Metadata del archivo
                parts = mensaje.split(":")
                if len(parts) >= 4:
                    nombre = parts[1]
                    tamaño = int(parts[2])
                    total_chunks = int(parts[3])
                    
                    self.archivos_recibiendo[source_mac] = {
                        'nombre': nombre,
                        'tamaño': tamaño,
                        'total_chunks': total_chunks,
                        'chunks_recibidos': [],
                        'datos': b'',
                        'timestamp': time.time()
                    }
                    self.chat_app.mostrar_mensaje("Sistema", f"📥 Recibiendo archivo: {nombre} de {source_mac}")
                
            elif mensaje.startswith("FILE_CHUNK:"):
                # Chunk de datos
                parts = mensaje.split(":", 3)
                if len(parts) >= 4:
                    chunk_num = int(parts[1])
                    total_chunks = int(parts[2])
                    chunk_data = parts[3]
                    
                    if source_mac not in self.archivos_recibiendo:
                        print(f"❌ Chunk {chunk_num} recibido sin metadata")
                        return
                    
                    archivo = self.archivos_recibiendo[source_mac]
                    
                    # Convertir chunk_data de string a bytes
                    if isinstance(chunk_data, str):
                        chunk_data_bytes = chunk_data.encode('latin-1')
                    else:
                        chunk_data_bytes = chunk_data
                    
                    archivo['chunks_recibidos'].append(chunk_num)
                    archivo['datos'] += chunk_data_bytes
                    
                    # Mostrar progreso
                    progreso = len(archivo['chunks_recibidos']) / archivo['total_chunks'] * 100
                    if chunk_num % 5 == 0:
                        self.chat_app.mostrar_mensaje("Sistema", 
                            f"📊 Progreso {archivo['nombre']}: {progreso:.1f}%")
                    
                    print(f"✅ Chunk {chunk_num}/{total_chunks} procesado: {len(chunk_data_bytes)} bytes")
                
            elif mensaje.startswith("FILE_END:"):
                # Fin de transmisión
                parts = mensaje.split(":")
                if len(parts) >= 2:
                    nombre = parts[1]
                    
                    if source_mac not in self.archivos_recibiendo:
                        print(f"❌ FILE_END recibido sin metadata para {nombre}")
                        return
                    
                    archivo = self.archivos_recibiendo[source_mac]
                    
                    if len(archivo['chunks_recibidos']) == archivo['total_chunks']:
                        # Guardar archivo
                        self._guardar_archivo(archivo, source_mac)
                    else:
                        self.chat_app.mostrar_mensaje("Error", 
                            f"❌ Archivo {nombre} incompleto. Recibidos: {len(archivo['chunks_recibidos'])}/{archivo['total_chunks']}")
                        print(f"❌ Archivo incompleto: {len(archivo['chunks_recibidos'])}/{archivo['total_chunks']} chunks")
                    
                    # Limpiar
                    del self.archivos_recibiendo[source_mac]
                    print(f"✅ Procesamiento completado para: {nombre}")
                    
        except Exception as e:
            error_msg = f"❌ Error en receive_file: {str(e)}"
            self.chat_app.mostrar_mensaje("Error", error_msg)
            print(error_msg)
            import traceback
            traceback.print_exc()

    def _guardar_archivo(self, archivo: dict, mac_origen: str):
        try:
            # Crear directorio de descargas si no existe
            download_dir = "descargas"
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
            
            # Mostrar mensaje de éxito
            tamaño = len(archivo['datos'])
            mensaje = f"✅ Archivo guardado: {nombre_base} ({tamaño} bytes)"
            self.chat_app.mostrar_mensaje("Sistema", mensaje)
            
            print(f"✅ Archivo guardado exitosamente: {nombre_archivo}")
            
        except Exception as e:
            error_msg = f"❌ Error guardando archivo: {str(e)}"
            self.chat_app.mostrar_mensaje("Error", error_msg)
            print(error_msg)
   