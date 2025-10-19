import threading
import os
import time
from tkinter import filedialog, messagebox
import tkinter as tk

class FileTransferHandler:
    def __init__(self, app):
        self.app = app
        self.file_transfer = app.file_transfer

    def seleccionar_archivo(self):
        """Selecciona un archivo para enviar"""
        # Intentar usar la carpeta shared_files como directorio inicial
        initial_dir = "/app/shared_files"
        if not os.path.exists(initial_dir):
            initial_dir = os.getcwd()
            
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo para enviar",
            initialdir=initial_dir
        )
        
        if file_path:
            self.app.app_state.archivo_seleccionado = file_path
            nombre_archivo = os.path.basename(file_path)
            tamaño_archivo = os.path.getsize(file_path)
            tamaño_mb = tamaño_archivo / (1024 * 1024)
            tamaño_gb = tamaño_archivo / (1024 * 1024 * 1024)
            
            # Mostrar tamaño apropiadamente
            if tamaño_gb >= 1:
                texto = f"Archivo: {nombre_archivo} ({tamaño_gb:.2f} GB)"
                mensaje_sistema = f"Archivo grande seleccionado: {nombre_archivo} ({tamaño_gb:.2f} GB)"
            else:
                texto = f"Archivo: {nombre_archivo} ({tamaño_mb:.1f} MB)"
                mensaje_sistema = f"Archivo seleccionado: {nombre_archivo} ({tamaño_mb:.1f} MB)"
            
            self.app.lbl_archivo.config(text=texto)
            self.app.btn_enviar_archivo.config(state=tk.NORMAL)
            
            # Deshabilitar envío de carpeta
            self.app.btn_enviar_carpeta.config(state=tk.DISABLED)
            self.app.app_state.carpeta_seleccionada = None
            
            self.app.mostrar_mensaje("Sistema", mensaje_sistema)
            
            # Mostrar estimación de transferencia para archivos grandes
            if tamaño_gb >= 0.5:  # Mayor a 500MB
                fragmentos_estimados = tamaño_archivo // 1475  # Tamaño aproximado de fragmento
                tiempo_estimado = fragmentos_estimados * 0.01  # Estimación muy aproximada
                self.app.mostrar_mensaje("Sistema", f"⏱️ Transferencia estimada: ~{tiempo_estimado:.0f} segundos ({fragmentos_estimados:,} fragmentos)")

    def seleccionar_carpeta(self):
        """Selecciona una carpeta para enviar"""
        folder_path = filedialog.askdirectory(
            title="Seleccionar carpeta para enviar"
        )
        
        if folder_path:
            self.app.app_state.carpeta_seleccionada = folder_path
            nombre_carpeta = os.path.basename(folder_path)
            
            # Obtener información de la carpeta
            if self.app.communication_manager.folder_transfer:
                total_size, file_count = self.app.communication_manager.folder_transfer.get_folder_size(folder_path)
                size_mb = total_size / (1024 * 1024)
                
                texto = f"Carpeta: {nombre_carpeta} ({file_count} archivos, {size_mb:.1f} MB)"
            else:
                texto = f"Carpeta: {nombre_carpeta}"
            
            self.app.lbl_archivo.config(text=texto)
            self.app.btn_enviar_carpeta.config(state=tk.NORMAL)
            
            # Deshabilitar envío de archivo
            self.app.btn_enviar_archivo.config(state=tk.DISABLED)
            self.app.app_state.archivo_seleccionado = None
            
            self.app.mostrar_mensaje("Sistema", f"Carpeta seleccionada: {nombre_carpeta}")

    def enviar_archivo(self):
        """Envía el archivo seleccionado"""
        if not self.app.app_state.archivo_seleccionado:
            messagebox.showerror("Error", "Primero selecciona un archivo")
            return
        
        if not self.app.communication_manager.com:
            messagebox.showerror("Error", "Comunicador no inicializado")
            return
        
        # Deshabilitar botones durante el envío
        self.app.btn_enviar_archivo.config(state=tk.DISABLED)
        self.app.btn_seleccionar.config(state=tk.DISABLED)
        
        # Mostrar mensaje de inicio
        nombre_archivo = os.path.basename(self.app.app_state.archivo_seleccionado)
        self.app.mostrar_mensaje("Sistema", f"Enviando archivo: {nombre_archivo}...")
        
        # Enviar en hilo separado
        threading.Thread(
            target=self._enviar_archivo_thread, 
            daemon=True
        ).start()

    def _enviar_archivo_thread(self):
        """Envía el archivo en un hilo separado"""
        try:
            exito, mensaje = self.file_transfer.send_file(
                self.app.app_state.archivo_seleccionado, 
                self.app.app_state.destino_actual
            )
            
            # Actualizar interfaz en el hilo principal
            self.app.root.after(0, self._callback_envio_archivo, exito, mensaje)
            
        except Exception as e:
            self.app.root.after(0, self._callback_envio_archivo, False, f"Error: {str(e)}")

    def _callback_envio_archivo(self, exito, mensaje):
        """Callback cuando termina el envío del archivo"""
        # Rehabilitar botones
        self.app.btn_seleccionar.config(state=tk.NORMAL)
        
        if exito:
            nombre_archivo = os.path.basename(self.app.app_state.archivo_seleccionado)
            self.app.mostrar_mensaje("Sistema", f"Archivo enviado: {nombre_archivo}")
            
            # Limpiar selección
            self.app.app_state.archivo_seleccionado = None
            self.app.lbl_archivo.config(text="Ningun elemento seleccionado")
        else:
            self.app.btn_enviar_archivo.config(state=tk.NORMAL)
            self.app.mostrar_mensaje("Error", f"Fallo en envio: {mensaje}")

    def enviar_carpeta(self):
        """Envía la carpeta seleccionada"""
        if not self.app.app_state.carpeta_seleccionada:
            messagebox.showerror("Error", "Primero selecciona una carpeta")
            return
        
        if not self.app.communication_manager.folder_transfer:
            messagebox.showerror("Error", "Gestor de carpetas no inicializado")
            return
        
        # Deshabilitar botones durante el envío
        self.app.btn_enviar_carpeta.config(state=tk.DISABLED)
        self.app.btn_seleccionar_carpeta.config(state=tk.DISABLED)
        
        # Mostrar mensaje de inicio
        nombre_carpeta = os.path.basename(self.app.app_state.carpeta_seleccionada)
        self.app.mostrar_mensaje("Sistema", f"Enviando carpeta: {nombre_carpeta}...")
        
        # Enviar en hilo separado
        threading.Thread(
            target=self._enviar_carpeta_thread, 
            daemon=True
        ).start()

    def _enviar_carpeta_thread(self):
        """Envía la carpeta en un hilo separado"""
        try:
            def progress_callback(progress, status):
                # Actualizar en hilo principal
                self.app.root.after(0, lambda: self.app.mostrar_mensaje("Sistema", f"Progreso: {progress:.1f}% - {status}"))
            
            exito, mensaje = self.app.communication_manager.folder_transfer.send_folder(
                self.app.app_state.carpeta_seleccionada, 
                self.app.app_state.destino_actual,
                progress_callback
            )
            
            # Actualizar interfaz en el hilo principal
            self.app.root.after(0, self._callback_envio_carpeta, exito, mensaje)
            
        except Exception as e:
            self.app.root.after(0, self._callback_envio_carpeta, False, f"Error: {str(e)}")

    def _callback_envio_carpeta(self, exito, mensaje):
        """Callback cuando termina el envío de la carpeta"""
        # Rehabilitar botones
        self.app.btn_seleccionar_carpeta.config(state=tk.NORMAL)
        
        if exito:
            nombre_carpeta = os.path.basename(self.app.app_state.carpeta_seleccionada)
            self.app.mostrar_mensaje("Sistema", f"Carpeta enviada: {nombre_carpeta}")
            
            # Limpiar selección
            self.app.app_state.carpeta_seleccionada = None
            self.app.lbl_archivo.config(text="Ningun elemento seleccionado")
        else:
            self.app.btn_enviar_carpeta.config(state=tk.NORMAL)
            self.app.mostrar_mensaje("Error", f"Fallo en envío: {mensaje}")

    def procesar_archivo_recibido(self, frame):
        """Procesa y guarda un archivo recibido (método del original)"""
        try:
            print(f"Procesando archivo recibido:")
            print(f"   - Nombre archivo: {getattr(frame, 'nombre_archivo', 'No disponible')}")
            # Convertir datos a string si son bytes
            datos_raw = frame.datos
            
            # Solo intentar decodificar para preview, no para procesamiento
            try:
                if isinstance(datos_raw, bytes):
                    mensaje_preview = datos_raw.decode('utf-8', errors='ignore')[:100]
                else:
                    mensaje_preview = str(datos_raw)[:100]
            except:
                mensaje_preview = f"<datos binarios {len(datos_raw) if datos_raw else 0} bytes>"
            
            print(f"   - Datos recibidos: {mensaje_preview}...")
            
            # Procesar según el tipo de datos - pasar datos raw al file_transfer
            if isinstance(datos_raw, bytes) and len(datos_raw) >= 2:
                # Verificar formato FILE_TRANSFER: nuevo
                if datos_raw.startswith(b"FILE_TRANSFER:"):
                    self.file_transfer.receive_file(datos_raw, frame.mac_origen)
                    return
                
                # Intentar formato binario legacy
                try:
                    header_length = int.from_bytes(datos_raw[:2], 'big')
                    if len(datos_raw) >= 2 + header_length:
                        header = datos_raw[2:2+header_length].decode('utf-8')
                        if header.startswith(('FILE_CHUNK:', 'FILE_METADATA:', 'FILE_END:')):
                            self.file_transfer.receive_file(datos_raw, frame.mac_origen)
                            return
                except:
                    pass
            
            # Intentar formato legacy (string)
            try:
                if isinstance(datos_raw, bytes):
                    mensaje = datos_raw.decode('utf-8', errors='ignore')
                else:
                    mensaje = str(datos_raw)
                
                if mensaje.startswith(('FOLDER_START:', 'FOLDER_FILE:', 'FOLDER_END:')):
                    # Procesar mensajes de transferencia de carpeta
                    if self.app.communication_manager.folder_transfer:
                        self.app.communication_manager.folder_transfer.handle_folder_message(mensaje, frame.mac_origen)
                elif mensaje.startswith(('FILE_METADATA:', 'FILE_CHUNK:', 'FILE_END:', 'FILE_TRANSFER:')):
                    # Procesar archivos (legacy y nuevo formato)
                    self.file_transfer.receive_file(datos_raw, frame.mac_origen)
                else:
                    # Archivo no fragmentado - guardar directamente
                    self._guardar_archivo_no_fragmentado(frame)
            except Exception as e:
                print(f"Error procesando datos como string: {e}")
                # Intentar como archivo no fragmentado
                self._guardar_archivo_no_fragmentado(frame)
                
        except Exception as e:
            error_msg = f" Error procesando archivo: {str(e)}"
            self.app.mostrar_mensaje("Error", error_msg)
            print(error_msg)
            import traceback
            traceback.print_exc()

    def _guardar_archivo_no_fragmentado(self, frame):
        """Guarda un archivo que no está fragmentado (método del original)"""
        try:
            nombre_archivo = getattr(frame, 'nombre_archivo', None)
            datos_archivo = frame.datos
            
            if not nombre_archivo:
                timestamp = int(time.time())
                nombre_archivo = f"archivo_recibido_{timestamp}.bin"
            
            if not datos_archivo:
                print("No hay datos en el frame para guardar")
                return
            
            # Crear directorio de downloads si no existe
            download_dir = "downloads"
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
            
            # Generar nombre único
            nombre_base = nombre_archivo
            nombre_completo = os.path.join(download_dir, nombre_base)
            
            contador = 1
            while os.path.exists(nombre_completo):
                nombre, extension = os.path.splitext(nombre_base)
                nombre_completo = os.path.join(download_dir, f"{nombre}_{contador}{extension}")
                contador += 1
            
            # Guardar archivo
            with open(nombre_completo, 'wb') as f:
                f.write(datos_archivo)
            
            # Verificar si es parte de una transferencia de carpeta
            if (self.app.communication_manager.folder_transfer and 
                self.app.communication_manager.folder_transfer.check_folder_file_received(nombre_completo, frame.mac_origen)):
                # Es parte de una carpeta, el folder_transfer se encarga del mensaje
                print(f" Archivo de carpeta procesado: {nombre_completo}")
                return
            
            # Mostrar mensaje de éxito para archivo individual
            tamaño = len(datos_archivo)
            mensaje = f"Archivo recibido: {nombre_base} ({tamaño} bytes)"
            self.app.mostrar_mensaje("Sistema", mensaje)
            
            print(f" Archivo guardado: {nombre_completo}")
            
        except Exception as e:
            error_msg = f"Error guardando archivo no fragmentado: {str(e)}"
            self.app.mostrar_mensaje("Error", error_msg)
            print(error_msg)