import os
import base64
import hashlib
import json

class FileTransfer:
    def __init__(self, chat_app):
        self.chat_app = chat_app
        self.MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB límite
        self.CHUNK_SIZE = 1000  # Tamaño de fragmento ajustado para MTU
    
    def send_file(self, file_path, dest_mac):
        """Envía un archivo fragmentado"""
        try:
            if not os.path.exists(file_path):
                return False, "Archivo no existe"
            
            file_size = os.path.getsize(file_path)
            if file_size > self.MAX_FILE_SIZE:
                return False, f"Archivo muy grande (> {self.MAX_FILE_SIZE} bytes)"
            
            file_name = os.path.basename(file_path)
            file_hash = self.calculate_file_hash(file_path)
            
            # Enviar metadatos del archivo
            metadata = {
                'type': 'file_start',
                'name': file_name,
                'size': file_size,
                'hash': file_hash,
                'chunks': (file_size + self.CHUNK_SIZE - 1) // self.CHUNK_SIZE
            }
            
            # Enviar metadata
            self.chat_app.send_message(f"FILE_METADATA:{json.dumps(metadata)}", dest_mac)
            
            # Enviar archivo por chunks
            with open(file_path, 'rb') as f:
                chunk_index = 0
                while True:
                    chunk = f.read(self.CHUNK_SIZE)
                    if not chunk:
                        break
                    
                    chunk_data = {
                        'type': 'file_chunk',
                        'index': chunk_index,
                        'data': base64.b64encode(chunk).decode('utf-8'),
                        'hash': file_hash
                    }
                    
                    # Enviar chunk
                    self.chat_app.send_message(f"FILE_CHUNK:{json.dumps(chunk_data)}", dest_mac)
                    chunk_index += 1
            
            # Enviar fin de archivo
            self.chat_app.send_message(f"FILE_END:{file_hash}", dest_mac)
            return True, "Archivo enviado exitosamente"
            
        except Exception as e:
            return False, f"Error enviando archivo: {str(e)}"
    
    def receive_file(self, message, source_mac):
        """Maneja la recepción de archivos"""
        if message.startswith("FILE_METADATA:"):
            self.handle_file_metadata(message, source_mac)
        elif message.startswith("FILE_CHUNK:"):
            self.handle_file_chunk(message, source_mac)
        elif message.startswith("FILE_END:"):
            self.handle_file_end(message, source_mac)
    
    def handle_file_metadata(self, message, source_mac):
        try:
            metadata_str = message.split("FILE_METADATA:")[1]
            metadata = json.loads(metadata_str)
            
            # Inicializar recepción
            self.current_file = {
                'name': metadata['name'],
                'size': metadata['size'],
                'hash': metadata['hash'],
                'total_chunks': metadata['chunks'],
                'received_chunks': 0,
                'data': bytearray(),
                'source_mac': source_mac
            }
            
            print(f"Recibiendo archivo: {metadata['name']} ({metadata['size']} bytes)")
            
        except Exception as e:
            print(f"Error procesando metadata: {e}")
    
    def handle_file_chunk(self, message, source_mac):
        try:
            chunk_str = message.split("FILE_CHUNK:")[1]
            chunk_data = json.loads(chunk_str)
            
            if hasattr(self, 'current_file') and self.current_file['hash'] == chunk_data['hash']:
                chunk = base64.b64decode(chunk_data['data'])
                self.current_file['data'].extend(chunk)
                self.current_file['received_chunks'] += 1
                
                # Mostrar progreso
                progress = (self.current_file['received_chunks'] / self.current_file['total_chunks']) * 100
                print(f"Progreso: {progress:.1f}%")
                
        except Exception as e:
            print(f"Error procesando chunk: {e}")
    
    def handle_file_end(self, message, source_mac):
        try:
            file_hash = message.split("FILE_END:")[1]
            
            if hasattr(self, 'current_file') and self.current_file['hash'] == file_hash:
                # Verificar integridad
                received_hash = self.calculate_data_hash(bytes(self.current_file['data']))
                
                if received_hash == file_hash and len(self.current_file['data']) == self.current_file['size']:
                    # Guardar archivo
                    safe_name = f"recibido_{self.current_file['name']}"
                    with open(safe_name, 'wb') as f:
                        f.write(self.current_file['data'])
                    
                    print(f"Archivo guardado como: {safe_name}")
                    del self.current_file
                else:
                    print("Error: Archivo corrupto o incompleto")
                    
        except Exception as e:
            print(f"Error finalizando recepción: {e}")
    
    def calculate_file_hash(self, file_path):
        """Calcula hash SHA256 de un archivo"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def calculate_data_hash(self, data):
        """Calcula hash SHA256 de datos en memoria"""
        return hashlib.sha256(data).hexdigest()