#!/usr/bin/env python3
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, filedialog, ttk
import threading
import time
import sys
import os
import json
from src.core.frames import Tipo_Mensaje
from src.core.env_recb import Envio_recibo_frames
from src.features.files import FileTransfer
from src.core.mac import Mac
from src.features.discovery import DiscoveryManager
from src.features.folder_transfer import FolderTransfer
from src.features.simple_security import SimpleSecurityManager 

if not os.path.exists("downloads"):
    os.makedirs("downloads")

# Configuración para VirtualBox - evitar problemas gráficos
os.environ['TK_SILENCE_DEPRECATION'] = '1'
os.environ['XLIB_SKIP_ARGB_VISUALS'] = '1'
os.environ['QT_X11_NO_MITSHM'] = '1'
os.environ['_JAVA_AWT_WM_NONREPARENTING'] = '1'

# Configuración específica para VirtualBox
if 'virtualbox' in os.environ.get('SESSION_MANAGER', '').lower():
    os.environ['GDK_BACKEND'] = 'x11'

def configurar_tkinter():
    import tkinter as tk
    
    tk.Button._default_state = 'normal'
    
    # Forzar modo simple para evitar problemas de renderizado
    try:
        # Intentar deshabilitar aceleración por hardware
        os.environ['TK_FONT'] = 'Arial 14'  # Aumentado para mejor legibilidad    
    except:
        pass
    
configurar_tkinter()

class ChatMinimalTkinter:
    def __init__(self, root):
        self.root = root
        self.root.title("Link Chat")
        self.root.geometry("1000x1000")  # Un poco más alto para los botones de archivo
        
        # Configuración minimalista
        self.root.resizable(True, True)
        self.root.configure(bg='#2F2F2F')

        self.bg_color = '#2F2F2F'
        self.fg_color = 'white'
        self.entry_bg = '#404040'
        self.button_bg  = '#505050'
        self.border_color = 'black'
        self.font_size = 14  # Aumentado para mejor legibilidad

         
        # Colores para burbujas de chat
        self.bubble_me_bg = '#0084FF'  # Azul para mis mensajes
        self.bubble_other_bg = '#404040'  # Gris para mensajes de otros
        self.bubble_system_bg = '#FF6B00'  # Naranja para mensajes del sistema


        self.usuario=None
        
        
        # Variables
        self.com = None
        self.contactos = {}
        self.destino_actual = "FF:FF:FF:FF:FF:FF"
        self.archivo_contactos = "contactos_minimal.json"
        self.file_transfer = FileTransfer(self)
        self.archivo_seleccionado = None
        self.carpeta_seleccionada = None
        self.interfaz_seleccionada = None
        self.dic_usuarios = {"todos": "ff:ff:ff:ff:ff:ff"}
        self.stop_event = None
        
        # Nuevas funcionalidades
        self.discovery_manager = None
        self.folder_transfer = None
        self.security_manager = None


        self.contador_mensajes = 0  # INICIALIZAR contador_mensajes
        self.ejecutando_recepcion = False  # Control para el hilo de recepción
        
        self.cargar_contactos()
        self.crear_interfaz_minimal()
        
    def cargar_contactos(self):
        """Carga contactos básicos"""
        try:
            if os.path.exists(self.archivo_contactos):
                with open(self.archivo_contactos, 'r') as f:
                    self.contactos = json.load(f)
        except:
            self.contactos = {
                "FF:FF:FF:FF:FF:FF": "Todos (Broadcast)",
                "01:00:5E:00:00:01": "Multicast"
            }
    
    def guardar_contactos(self):
        """Guarda contactos"""
        try:
            with open(self.archivo_contactos, 'w') as f:
                json.dump(self.contactos, f)
        except:
            pass
    
    def crear_interfaz_minimal(self):        
        # Frame principal simple
        main_frame = tk.Frame(self.root, bg=self.bg_color, highlightbackground=self.border_color, highlightthickness=1)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        interfaz_frame = tk.Frame(main_frame, bg=self.bg_color, highlightbackground=self.border_color, highlightthickness=1)
        interfaz_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(interfaz_frame, text="Interfaz:", bg=self.bg_color,  fg=self.fg_color, font=('Arial', self.font_size)).pack(side=tk.LEFT)
        
        # Obtener interfaces disponibles
        interfaces = Mac.obtener_interfaces_fisicas()
        
        if not interfaces:
            tk.Label(interfaz_frame, text="No hay interfaces disponibles", bg=self.bg_color, fg='red' , font=('Arial', self.font_size)).pack(side=tk.LEFT)
            return
        
        self.interfaz_var = tk.StringVar()
        self.interfaz_combo = ttk.Combobox(
            interfaz_frame, 
            textvariable=self.interfaz_var,
            values=interfaces,
            state="readonly",
            width=20
        )
        self.interfaz_combo.pack(side=tk.LEFT, padx=5)
        self.interfaz_combo.set(interfaces[0])  # Seleccionar primera por defecto
        
        # Botón para conectar
        self.btn_conectar = tk.Button(
            interfaz_frame,
            text="Conectar",
            command=self.conectar_interfaz,
            width=10,
            bg=self.button_bg,
            fg=self.fg_color,
            font=('Arial', self.font_size),
            relief="solid",
            bd=1
        )
        self.btn_conectar.pack(side=tk.LEFT, padx=5)
        
        
        # Información básica
        info_frame = tk.Frame(main_frame, bg=self.bg_color, highlightbackground=self.border_color, highlightthickness=1)
        info_frame.pack(fill=tk.X, pady=2)
        
        self.status_label = tk.Label(info_frame, text="Desconectado", bg=self.bg_color, fg='red', font=('Arial', self.font_size))
        self.status_label.pack(side=tk.LEFT)
        
        # Área de mensajes (más pequeña)
        self.text_area = scrolledtext.ScrolledText(
            main_frame, 
            wrap=tk.WORD,
            width=50,
            height=12,
            font=('Arial', self.font_size),
            bg=self.bg_color,
            fg=self.fg_color,
            insertbackground=self.fg_color,  # Color del cursor
            relief="solid",
            bd=1
        )
        self.text_area.pack(fill=tk.BOTH, expand=True, pady=5)
        self.text_area.config(state=tk.DISABLED)

        # Entrada de mensaje
        msg_frame = tk.Frame(main_frame, bg=self.bg_color, highlightbackground=self.border_color, highlightthickness=1)
        msg_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(msg_frame, text="Mensaje:" ,bg=self.bg_color, fg=self.fg_color, font=('Arial', self.font_size)).pack(side=tk.LEFT)
        input_frame = tk.Frame(msg_frame, bg=self.bg_color)
        input_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.mensaje_var = tk.StringVar()
        self.mensaje_entry = tk.Text(
            input_frame, 
            height=3,  # Hacer el campo más alto (3 líneas)
            font=('Arial', self.font_size),
            bg=self.entry_bg,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            relief="solid",
            bd=1,
            wrap=tk.WORD
        )
        self.mensaje_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.mensaje_entry.bind('<Return>', self.enviar_mensaje)
        self.mensaje_entry.bind('<Shift-Return>', self.insertar_nueva_linea)  # Permitir nueva línea con Shift+Enter
        
        self.btn_enviar = tk.Button(
            input_frame, 
            text="Enviar", 
            command=self.enviar_mensaje, 
            width=8,
            bg=self.button_bg,
            fg=self.fg_color,
            font=('Arial', self.font_size),
            state=tk.DISABLED,  # Deshabilitado hasta conectar
            relief="solid",
            bd=1
        )
        self.btn_enviar.pack(side=tk.LEFT, padx=2)
        
        # === SECCIÓN DE ARCHIVOS Y CARPETAS AMPLIADA ===
        file_frame = tk.Frame(main_frame, bg=self.bg_color, highlightbackground=self.border_color, highlightthickness=1)
        file_frame.pack(fill=tk.X, pady=2)
        
        # Primera fila: Archivos
        file_row1 = tk.Frame(file_frame, bg=self.bg_color)
        file_row1.pack(fill=tk.X, pady=1)
        
        # Botón para seleccionar archivo
        self.btn_seleccionar = tk.Button(
            file_row1, 
            text="Seleccionar Archivo",
            command=self.seleccionar_archivo,
            width=15,
            bg=self.button_bg,
            fg=self.fg_color,
            font=('Arial', self.font_size),
            relief="solid",
            bd=1
        )
        self.btn_seleccionar.pack(side=tk.LEFT, padx=2)
        
        # Botón para seleccionar carpeta
        self.btn_seleccionar_carpeta = tk.Button(
            file_row1, 
            text="Seleccionar Carpeta",
            command=self.seleccionar_carpeta,
            width=15,
            bg=self.button_bg,
            fg=self.fg_color,
            font=('Arial', self.font_size),
            relief="solid",
            bd=1
        )
        self.btn_seleccionar_carpeta.pack(side=tk.LEFT, padx=2)
        
        # Etiqueta del elemento seleccionado
        self.lbl_archivo = tk.Label(
            file_row1, 
            text="Ningun elemento seleccionado", 
            bg=self.bg_color, 
            fg=self.fg_color,
            font=('Arial', self.font_size)
        )
        self.lbl_archivo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Segunda fila: Botones de envío
        file_row2 = tk.Frame(file_frame, bg=self.bg_color)
        file_row2.pack(fill=tk.X, pady=1)
        
        # Botón para enviar archivo
        self.btn_enviar_archivo = tk.Button(
            file_row2, 
            text="Enviar Archivo",
            command=self.enviar_archivo,
            state=tk.DISABLED,
            width=15,
            bg=self.button_bg,
            fg=self.fg_color,
            font=('Arial', self.font_size),
            relief="solid",
            bd=1
        )
        self.btn_enviar_archivo.pack(side=tk.LEFT, padx=2)
        
        # Botón para enviar carpeta
        self.btn_enviar_carpeta = tk.Button(
            file_row2, 
            text="Enviar Carpeta",
            command=self.enviar_carpeta,
            state=tk.DISABLED,
            width=15,
            bg=self.button_bg,
            fg=self.fg_color,
            font=('Arial', self.font_size),
            relief="solid",
            bd=1
        )
        self.btn_enviar_carpeta.pack(side=tk.LEFT, padx=2)
        
        # Controles simples
        control_frame = tk.Frame(main_frame, bg=self.bg_color, highlightbackground=self.border_color, highlightthickness=1)
        control_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(control_frame, text="Para:", bg=self.bg_color, fg=self.fg_color, font=('Arial', self.font_size)).pack(side=tk.LEFT)
        
        self.destino_var = tk.StringVar(value="FF:FF:FF:FF:FF:FF")
        self.destino_combo = ttk.Combobox(
            control_frame, 
            textvariable=self.destino_var,
            values=list(self.contactos.keys()),
            state="readonly",
            width=25
        )
        self.destino_combo.pack(side=tk.LEFT, padx=2)
        self.destino_combo.bind('<<ComboboxSelected>>', self.actualizar_destino)

        
        
        # Botón para agregar contacto
        self.btn_agregar_contacto = tk.Button(
            control_frame, 
            text="+", 
            command=self.agregar_contacto_simple, 
            width=2,
            state=tk.DISABLED, # Deshabilitado hasta conectar
            bg=self.button_bg,
            fg=self.fg_color,
            font=('Arial', self.font_size),
            relief="solid",
            bd=1
        )
        self.btn_agregar_contacto.pack(side=tk.LEFT, padx=2)

        # === SECCIÓN DE SEGURIDAD Y UTILIDADES ===
        security_frame = tk.Frame(main_frame, bg=self.bg_color, highlightbackground=self.border_color, highlightthickness=1)
        security_frame.pack(fill=tk.X, pady=2)
        
        # Botones de seguridad
        self.btn_habilitar_seguridad = tk.Button(
            security_frame, 
            text="Habilitar Seguridad",
            command=self.toggle_security,
            width=15,
            bg=self.button_bg,
            fg=self.fg_color,
            font=('Arial', self.font_size),
            relief="solid",
            bd=1,
            state=tk.DISABLED
        )
        self.btn_habilitar_seguridad.pack(side=tk.LEFT, padx=2)
        
        # Botón para iniciar discovery
        self.btn_buscar_dispositivos = tk.Button(
            security_frame, 
            text="Buscar Dispositivos",
            command=self.buscar_dispositivos,
            width=15,
            bg=self.button_bg,
            fg=self.fg_color,
            font=('Arial', self.font_size),
            relief="solid",
            bd=1,
            state=tk.DISABLED
        )
        self.btn_buscar_dispositivos.pack(side=tk.LEFT, padx=2)
        
        # Estado de seguridad
        self.lbl_seguridad = tk.Label(
            security_frame, 
            text="Seguridad: Deshabilitada", 
            bg=self.bg_color, 
            fg='red',
            font=('Arial', self.font_size)
        )
        self.lbl_seguridad.pack(side=tk.LEFT, padx=10)

        btn_frame = tk.Frame(main_frame, bg=self.bg_color, highlightbackground=self.border_color, highlightthickness=1)
        btn_frame.pack(fill=tk.X, pady=5)

        tk.Button(btn_frame, text="Limpiar", command=self.limpiar_mensajes, width=8, bg=self.button_bg, fg=self.fg_color, font=('Arial', self.font_size), relief="solid", bd=1).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Estadísticas", command=self.mostrar_estadisticas, width=10, bg=self.button_bg, fg=self.fg_color, font=('Arial', self.font_size), relief="solid", bd=1).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Salir", command=self.salir, width=8, bg=self.button_bg, fg=self.fg_color, font=('Arial', self.font_size), relief="solid", bd=1).pack(side=tk.LEFT, padx=2)
        
        # Bind selección de destino
        self.destino_combo.bind('<<ListboxSelect>>', self.seleccionar_destino)
    
    def insertar_nueva_linea(self, event=None):
        """Inserta una nueva línea cuando se presiona Shift+Enter"""
        self.mensaje_entry.insert(tk.INSERT, "\n")
        return "break"  # Previene el comportamiento por defecto de Enter
    
    def actualizar_destino(self, event=None):
        try:
            # Obtener el valor actual del combobox
            seleccion = self.destino_var.get()
            print(f"🔍 actualizar_destino: Selección del combobox: '{seleccion}'")
            
            # Si la selección está en formato "Nombre (MAC)", extraer solo la MAC
            if "(" in seleccion and ")" in seleccion:
                mac = seleccion.split("(")[1].split(")")[0].strip()
                print(f"🔍 actualizar_destino: MAC extraída: '{mac}'")
            else:
                mac = seleccion
            
            # Validar y normalizar la MAC
            if self.validar_mac(mac):
                self.destino_actual = mac.upper().replace('-', ':')
                print(f"✅ Destino actualizado: {self.destino_actual}")
            else:
                print(f"❌ MAC destino inválida: {mac}")
                
        except Exception as e:
            print(f"❌ Error en actualizar_destino: {e}")

    def conectar_interfaz(self):
        """Conecta usando la interfaz seleccionada"""
        interfaz = self.interfaz_var.get()
        if not interfaz:
            messagebox.showerror("Error", "Selecciona una interfaz")
            return
        
        self.interfaz_seleccionada = interfaz
        self.btn_conectar.config(state=tk.DISABLED)
        self.interfaz_combo.config(state=tk.DISABLED)
        self.actualizar_estado(f"Conectando a {interfaz}...")
        
        self.iniciar_comunicador()
    
    def habilitar_controles_chat(self):
        """Habilita todos los controles una vez conectado"""
        self.btn_seleccionar.config(state=tk.NORMAL)
        self.btn_seleccionar_carpeta.config(state=tk.NORMAL)
        self.btn_agregar_contacto.config(state=tk.NORMAL)
        self.btn_habilitar_seguridad.config(state=tk.NORMAL)
        self.btn_buscar_dispositivos.config(state=tk.NORMAL)
        self.mensaje_entry.config(state=tk.NORMAL)
        self.btn_enviar.config(state=tk.NORMAL)

    def seleccionar_archivo(self):
        """Selecciona un archivo para enviar"""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo para enviar"
        )
        
        if file_path:
            self.archivo_seleccionado = file_path
            nombre_archivo = os.path.basename(file_path)
            tamaño_archivo = os.path.getsize(file_path)
            tamaño_mb = tamaño_archivo / (1024 * 1024)
            
            texto = f"Archivo: {nombre_archivo} ({tamaño_mb:.1f} MB)"
            self.lbl_archivo.config(text=texto)
            self.btn_enviar_archivo.config(state=tk.NORMAL)
            
            # Deshabilitar envío de carpeta
            self.btn_enviar_carpeta.config(state=tk.DISABLED)
            self.carpeta_seleccionada = None
            
            self.mostrar_mensaje("Sistema", f"Archivo seleccionado: {nombre_archivo}")
    
    def enviar_archivo(self):
        """Envía el archivo seleccionado"""
        if not self.archivo_seleccionado:
            messagebox.showerror("Error", "Primero selecciona un archivo")
            return
        
        if not self.com:
            messagebox.showerror("Error", "Comunicador no inicializado")
            return
        
        # Deshabilitar botones durante el envío
        self.btn_enviar_archivo.config(state=tk.DISABLED)
        self.btn_seleccionar.config(state=tk.DISABLED)
        
        # Mostrar mensaje de inicio
        nombre_archivo = os.path.basename(self.archivo_seleccionado)
        self.mostrar_mensaje("Sistema", f"Enviando archivo: {nombre_archivo}...")
        
        # Enviar en hilo separado
        threading.Thread(
            target=self._enviar_archivo_thread, 
            daemon=True
        ).start()
    
    def _enviar_archivo_thread(self):
        """Envía el archivo en un hilo separado"""
        try:
            exito, mensaje = self.file_transfer.send_file(
                self.archivo_seleccionado, 
                self.destino_actual
            )
            
            # Actualizar interfaz en el hilo principal
            self.root.after(0, self._callback_envio_archivo, exito, mensaje)
            
        except Exception as e:
            self.root.after(0, self._callback_envio_archivo, False, f"Error: {str(e)}")

    def procesar_archivo_recibido(self, frame):
        """Procesa y guarda un archivo recibido"""
        try:
            print(f"Procesando archivo recibido:")
            print(f"   - Nombre archivo: {getattr(frame, 'nombre_archivo', 'No disponible')}")
            # Convertir datos a string si son bytes
            # Para archivos, pasar datos raw para evitar corrupción
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
                    if self.folder_transfer:
                        self.folder_transfer.handle_folder_message(mensaje, frame.mac_origen)
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
            self.mostrar_mensaje("Error", error_msg)
            print(error_msg)
            import traceback
            traceback.print_exc()
            

    def _guardar_archivo_no_fragmentado(self, frame):
        """Guarda un archivo que no está fragmentado"""
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
            if self.folder_transfer and self.folder_transfer.check_folder_file_received(nombre_completo, frame.mac_origen):
                # Es parte de una carpeta, el folder_transfer se encarga del mensaje
                print(f" Archivo de carpeta procesado: {nombre_completo}")
                return
            
            # Mostrar mensaje de éxito para archivo individual
            tamaño = len(datos_archivo)
            mensaje = f"Archivo recibido: {nombre_base} ({tamaño} bytes)"
            self.mostrar_mensaje("Sistema", mensaje)
            
            print(f" Archivo guardado: {nombre_completo}")
            
        except Exception as e:
            error_msg = f"Error guardando archivo no fragmentado: {str(e)}"
            self.mostrar_mensaje("Error", error_msg)
            print(error_msg)
    
    def _callback_envio_archivo(self, exito, mensaje):
        """Callback cuando termina el envío del archivo"""
        # Rehabilitar botones
        self.btn_seleccionar.config(state=tk.NORMAL)
        
        if exito:
            nombre_archivo = os.path.basename(self.archivo_seleccionado)
            self.mostrar_mensaje("Sistema", f"Archivo enviado: {nombre_archivo}")
            
            # Limpiar selección
            self.archivo_seleccionado = None
            self.lbl_archivo.config(text="Ningun elemento seleccionado")
        else:
            self.btn_enviar_archivo.config(state=tk.NORMAL)
            self.mostrar_mensaje("Error", f"Fallo en envio: {mensaje}")
    
    def actualizar_destinos(self):
        """Actualiza la lista de destinos disponibles"""
        try:
            # Crear lista en formato "Nombre (MAC)"
            valores_combobox = [f"{nombre} ({mac})" for mac, nombre in self.contactos.items()]
            
            # Actualizar los valores del combobox
            self.destino_combo['values'] = valores_combobox
            
            print(f"🔧 Destinos disponibles: {valores_combobox}")
            
            # Si no hay selección actual, seleccionar broadcast por defecto
            if valores_combobox and not self.destino_var.get():
                # Buscar el valor de broadcast en la lista
                broadcast_item = next((item for item in valores_combobox if "FF:FF:FF:FF:FF:FF" in item), None)
                if broadcast_item:
                    self.destino_var.set(broadcast_item)
                    self.actualizar_destino()
                    print(f"🔧 Destino establecido por defecto: {self.destino_actual}")
                
        except Exception as e:
            print(f"❌ Error actualizando destinos: {e}")
    
    def seleccionar_destino(self, event=None):
        """Selecciona destino de la lista"""
        seleccion = self.destino_combo.curselection()
        if seleccion:
            texto = self.destino_combo.get(seleccion[0])
            # Extraer MAC del texto "Nombre (MAC)"
            if "(" in texto and ")" in texto:
                mac = texto.split("(")[1].split(")")[0]
                self.destino_actual = mac
    
    def agregar_contacto_simple(self):
        """Diálogo simple para agregar contacto"""
        mac = simpledialog.askstring("Agregar Contacto", "Dirección MAC (AA:BB:CC:DD:EE:FF):")
        if mac and self.validar_mac(mac):
            nombre = simpledialog.askstring("Agregar Contacto", "Nombre descriptivo:")
            if nombre:
                self.contactos[mac.upper()] = nombre
                self.guardar_contactos()
                self.actualizar_destinos()
                messagebox.showinfo("Éxito", "Contacto agregado")
        elif mac:
            messagebox.showerror("Error", "MAC inválida")
    
    def iniciar_comunicador(self):
        """Inicia el comunicador"""
        self.stop_event = threading.Event()
        self.com = Envio_recibo_frames(interfaz=self.interfaz_seleccionada)
        mac_propia = self.com.mac_ori
        
        # Inicializar nuevos módulos
        self.discovery_manager = DiscoveryManager(
            self.com, 
            callback_device_found=self.on_device_discovered
        )
        self.folder_transfer = FolderTransfer(self)
        self.security_manager = SimpleSecurityManager(self)
                
        self.habilitar_controles_chat()
        self.actualizar_estado(f"Conectado - {self.interfaz_seleccionada} - MAC: {mac_propia}")
        self.mostrar_mensaje("Sistema", f"Conectado - Interfaz: {self.interfaz_seleccionada} - Mi MAC: {mac_propia}")
        
        # Iniciar discovery automático
        self.discovery_manager.start_discovery()
        
        self.actualizar_destino()
        self.receive_thread = threading.Thread(
            target=self.com.receive_thread,
            args=(self.stop_event,),  
            daemon=True
            )
        self.receive_thread.start()
        self.poll_incoming()

    def _hilo_recepcion(self):
        """Hilo personalizado para recibir mensajes"""
        print(f"👂 Iniciando hilo de recepción en {self.interfaz_seleccionada}...")
        
        while self.ejecutando_recepcion and self.com:
            try:
                # Recibir frame
                frame_bytes = self.com.receive_frame()
                
                if frame_bytes:
                    # Decodificar frame
                    frame_decodificado = self.com.decodificar_frame(frame_bytes)
                    
                    if frame_decodificado:
                        mac_origen = frame_decodificado.mac_origen
                        mensaje = frame_decodificado.datos
                        
                        # Procesar en el hilo principal
                        self.root.after(0, lambda: self.manejar_mensaje_recibido(mac_origen, mensaje))
                
                # Pequeña pausa para no saturar la CPU
                time.sleep(0.01)
                
            except Exception as e:
                if self.ejecutando_recepcion:
                    print(f"❌ Error en hilo de recepción: {e}")
                    time.sleep(0.1)  # Pausa más larga en caso de error
    
    def manejar_mensaje_recibido(self, mac_origen, mensaje):
        # Agregar a contactos si es nuevo
        if mac_origen not in self.contactos:
            self.contactos[mac_origen] = f"Dispositivo {mac_origen[-6:]}"
            self.guardar_contactos()
            self.root.after(0, self.actualizar_destinos)
        
        # Mostrar mensaje
        if isinstance(mensaje, bytes):
            try:
                # Intentar decodificar como texto
                mensaje_texto = mensaje.decode('utf-8')
                self.root.after(0, lambda: self.mostrar_mensaje(mac_origen, mensaje_texto))
            except:
                # Es un archivo u otros datos binarios
                self.root.after(0, lambda: self.mostrar_mensaje(mac_origen, f"[Datos binarios: {len(mensaje)} bytes]"))
        else:
            self.root.after(0, lambda: self.mostrar_mensaje(mac_origen, mensaje))
        
        # Procesar mensajes de archivo
        if isinstance(mensaje, str) and mensaje.startswith(("FILE_METADATA:", "FILE_CHUNK:", "FILE_END:")):
            self.root.after(0, lambda: self.file_transfer.receive_file(mensaje, mac_origen))
    
    def enviar_mensaje(self, event=None):
        """Envía mensaje de texto"""
        if not self.com:
            messagebox.showerror("Error", "Comunicador no inicializado")
            return
        
        self.actualizar_destino()
        mensaje = self.mensaje_entry.get('1.0', tk.END).strip()
        if not mensaje:
            return
        
        # Verificar si se debe cifrar el mensaje
        mensaje_final = mensaje
        if (self.security_manager and 
            self.security_manager.has_secure_channel(self.destino_actual) and
            self.destino_actual != "FF:FF:FF:FF:FF:FF"):  # No cifrar broadcast
            
            encrypted_msg = self.security_manager.encrypt_message(mensaje, self.destino_actual)
            if encrypted_msg:
                mensaje_final = encrypted_msg
                self.mostrar_mensaje("Yo 🔒", f"→ {mensaje}")  # Mostrar mensaje original
            else:
                self.mostrar_mensaje("Yo", f"→ {mensaje}")
        else:
            self.mostrar_mensaje("Yo", f"→ {mensaje}")
        
        # Crear y enviar frame
        frames = self.com.crear_frame(self.destino_actual, Tipo_Mensaje.texto, mensaje_final)
        
        if frames:
            self.com.enviar_frame(frames)

        self.mensaje_entry.delete('1.0', tk.END)
    
    def _enviar_mensaje_thread(self, mensaje, destino):
        """Envía mensaje en hilo separado"""
        try:
            self.contador_mensajes += 1
            frame = self.com.crear_frame(
                destino,
    
                Tipo_Mensaje.texto.value,
                mensaje
            )
            
            bytes_enviados = self.com.enviar_frame(frame)
            
            if bytes_enviados > 0:
                self.root.after(0, lambda: self.mostrar_mensaje("Yo", mensaje))
            else:
                self.root.after(0, lambda: self.mostrar_mensaje("Error", "No se pudo enviar el mensaje"))
                
        except Exception as e:
            self.root.after(0, lambda: self.mostrar_mensaje("Error", f"Error al enviar: {str(e)}"))

    def poll_incoming(self):
        # Revisar si hay frames en la cola
        try:
            # Revisar si hay frames en la cola
            while not self.com.cola_mensajes.empty():
                decoded_frame = self.com.cola_mensajes.get()
                print(f"🔔 Frame obtenido de cola: tipo {decoded_frame.tipo_mensaje}")

                if decoded_frame.tipo_mensaje == Tipo_Mensaje.texto:
                    print("📝 Mensaje de texto recibido")
                    # Procesar mensaje de texto directamente
                    mensaje = decoded_frame.datos
                    
                    # Convertir a string si es bytes
                    if isinstance(mensaje, bytes):
                        try:
                            mensaje = mensaje.decode('utf-8')
                        except:
                            mensaje = str(mensaje)
                    
                    # Usar procesamiento mejorado que maneja discovery, seguridad, etc.
                    self.procesar_mensaje_recibido_mejorado(decoded_frame.mac_origen, mensaje)
                
                elif decoded_frame.tipo_mensaje == Tipo_Mensaje.archivo:
                    print("📁 Frame de archivo recibido")
                    # Procesar archivo recibido
                    self.procesar_archivo_recibido(decoded_frame)
                else:
                    print(f"❓ Tipo de mensaje desconocido: {decoded_frame.tipo_mensaje}")

        except Exception as e:
            print(f"❌ Error en poll_incoming: {e}")
        
        # Programar que se vuelva a ejecutar más frecuentemente
        self.root.after(40, self.poll_incoming)

        # def _enviar(self, mensaje):
    
    def mostrar_mensaje(self, remitente, mensaje):
        """Muestra mensaje en el área de texto"""
        try:
            self.text_area.config(state=tk.NORMAL)
            
            # Usar nombre amigable si está en contactos
            if remitente in self.contactos:
                nombre = self.contactos[remitente]
            else:
                nombre = remitente
            
            timestamp = time.strftime("%H:%M:%S")
            
            # Formato simple sin emojis para evitar errores gráficos
            if remitente == "Yo":
                formato = f"[{timestamp}] Yo: {mensaje}\n"
            elif remitente == "Sistema":
                formato = f"[{timestamp}] Sistema: {mensaje}\n"
            elif remitente == "Error":
                formato = f"[{timestamp}] Error: {mensaje}\n"
            else:
                formato = f"[{timestamp}] {nombre}: {mensaje}\n"
            
            self.text_area.insert(tk.END, formato)
            self.text_area.see(tk.END)
            self.text_area.config(state=tk.DISABLED)
            
        except Exception as e:
            print(f"❌ Error en mostrar_mensaje: {e}")
    
    def limpiar_mensajes(self):
        """Limpia el área de mensajes"""
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.config(state=tk.DISABLED)
    
    def actualizar_estado(self, mensaje):
        """Actualiza la barra de estado"""
        self.status_label.config(text=mensaje)
    
    def validar_mac(self, mac):
        """Valida dirección MAC"""
        if mac.upper() == "FF:FF:FF:FF:FF:FF":
            return True
        
        partes = mac.split(':')
        if len(partes) != 6:
            return False
        
        for parte in partes:
            if len(parte) != 2 or not all(c in '0123456789abcdefABCDEF' for c in parte):
                return False
        
        return True
    
    # === NUEVAS FUNCIONALIDADES ===
    
    def seleccionar_carpeta(self):
        """Selecciona una carpeta para enviar"""
        folder_path = filedialog.askdirectory(
            title="Seleccionar carpeta para enviar"
        )
        
        if folder_path:
            self.carpeta_seleccionada = folder_path
            nombre_carpeta = os.path.basename(folder_path)
            
            # Obtener información de la carpeta
            if self.folder_transfer:
                total_size, file_count = self.folder_transfer.get_folder_size(folder_path)
                size_mb = total_size / (1024 * 1024)
                
                texto = f"Carpeta: {nombre_carpeta} ({file_count} archivos, {size_mb:.1f} MB)"
            else:
                texto = f"Carpeta: {nombre_carpeta}"
            
            self.lbl_archivo.config(text=texto)
            self.btn_enviar_carpeta.config(state=tk.NORMAL)
            
            # Deshabilitar envío de archivo
            self.btn_enviar_archivo.config(state=tk.DISABLED)
            self.archivo_seleccionado = None
            
            self.mostrar_mensaje("Sistema", f"Carpeta seleccionada: {nombre_carpeta}")
    
    def enviar_carpeta(self):
        """Envía la carpeta seleccionada"""
        if not self.carpeta_seleccionada:
            messagebox.showerror("Error", "Primero selecciona una carpeta")
            return
        
        if not self.folder_transfer:
            messagebox.showerror("Error", "Gestor de carpetas no inicializado")
            return
        
        # Deshabilitar botones durante el envío
        self.btn_enviar_carpeta.config(state=tk.DISABLED)
        self.btn_seleccionar_carpeta.config(state=tk.DISABLED)
        
        # Mostrar mensaje de inicio
        nombre_carpeta = os.path.basename(self.carpeta_seleccionada)
        self.mostrar_mensaje("Sistema", f"Enviando carpeta: {nombre_carpeta}...")
        
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
                self.root.after(0, lambda: self.mostrar_mensaje("Sistema", f"Progreso: {progress:.1f}% - {status}"))
            
            exito, mensaje = self.folder_transfer.send_folder(
                self.carpeta_seleccionada, 
                self.destino_actual,
                progress_callback
            )
            
            # Actualizar interfaz en el hilo principal
            self.root.after(0, self._callback_envio_carpeta, exito, mensaje)
            
        except Exception as e:
            self.root.after(0, self._callback_envio_carpeta, False, f"Error: {str(e)}")
    
    def _callback_envio_carpeta(self, exito, mensaje):
        """Callback cuando termina el envío de la carpeta"""
        # Rehabilitar botones
        self.btn_seleccionar_carpeta.config(state=tk.NORMAL)
        
        if exito:
            nombre_carpeta = os.path.basename(self.carpeta_seleccionada)
            self.mostrar_mensaje("Sistema", f"Carpeta enviada: {nombre_carpeta}")
            
            # Limpiar selección
            self.carpeta_seleccionada = None
            self.lbl_archivo.config(text="Ningun elemento seleccionado")
        else:
            self.btn_enviar_carpeta.config(state=tk.NORMAL)
            self.mostrar_mensaje("Error", f"Fallo en envío: {mensaje}")
    
    def toggle_security(self):
        """Habilita/deshabilita la seguridad"""
        if not self.security_manager:
            return
        
        if self.security_manager.security_enabled:
            self.security_manager.disable_security()
            self.btn_habilitar_seguridad.config(text="Habilitar Seguridad")
            self.lbl_seguridad.config(text="Seguridad: Deshabilitada", fg='red')
        else:
            if self.security_manager.enable_security():
                self.btn_habilitar_seguridad.config(text="Deshabilitar Seguridad")
                self.lbl_seguridad.config(text="Seguridad: Habilitada", fg='green')
            else:
                messagebox.showerror("Error", "No se pudo habilitar la seguridad")
    
    def buscar_dispositivos(self):
        """Inicia búsqueda activa de dispositivos"""
        if not self.discovery_manager:
            return
        
        self.discovery_manager.send_discovery_request()
        self.mostrar_mensaje("Sistema", "Buscando dispositivos en la red...")
        
        # Mostrar dispositivos encontrados después de un momento
        self.root.after(3000, self.mostrar_dispositivos_encontrados)
    
    def mostrar_dispositivos_encontrados(self):
        """Muestra los dispositivos encontrados"""
        if not self.discovery_manager:
            return
        
        devices = self.discovery_manager.get_discovered_devices()
        count = len(devices)
        
        self.mostrar_mensaje("Sistema", f"Dispositivos encontrados: {count}")
        for mac, info in devices.items():
            self.mostrar_mensaje("Sistema", f"- {info['hostname']} ({mac})")
    
    def on_device_discovered(self, device_info: dict):
        """Callback cuando se descubre un nuevo dispositivo"""
        mac = device_info['mac']
        hostname = device_info['hostname']
        
        # Agregar a contactos automáticamente
        if mac not in self.contactos:
            self.contactos[mac] = hostname
            self.guardar_contactos()
            self.actualizar_destinos()
        
        # Notificar al usuario
        self.mostrar_mensaje("Discovery", f"Nuevo dispositivo: {hostname} ({mac})")
    
    def mostrar_estadisticas(self):
        """Muestra estadísticas del sistema"""
        if not self.com:
            messagebox.showinfo("Estadísticas", "No hay conexión activa")
            return
        
        estadisticas = self.com.obtener_estadisticas()
        
        # Agregar estadísticas de discovery y seguridad
        if self.discovery_manager:
            device_count = self.discovery_manager.get_device_count()
            estadisticas['dispositivos_descubiertos'] = device_count
        
        if self.security_manager:
            security_status = self.security_manager.get_security_status()
            estadisticas.update(security_status)
        
        # Crear mensaje de estadísticas
        mensaje = "=== ESTADÍSTICAS ===\n"
        mensaje += f"Mensajes enviados: {estadisticas.get('mensajes_enviados', 0)}\n"
        mensaje += f"Mensajes recibidos: {estadisticas.get('mensajes_recibidos', 0)}\n"
        mensaje += f"Fragmentos enviados: {estadisticas.get('fragmentos_enviados', 0)}\n"
        mensaje += f"Fragmentos recibidos: {estadisticas.get('fragmentos_recibidos', 0)}\n"
        mensaje += f"Dispositivos descubiertos: {estadisticas.get('dispositivos_descubiertos', 0)}\n"
        mensaje += f"Canales seguros: {estadisticas.get('secure_channels', 0)}\n"
        mensaje += f"Seguridad habilitada: {'Sí' if estadisticas.get('enabled', False) else 'No'}"
        
        messagebox.showinfo("Estadísticas del Sistema", mensaje)
    
    def procesar_mensaje_recibido_mejorado(self, mac_origen: str, mensaje: str):
        """Versión mejorada del procesamiento de mensajes"""
        
        # Procesar mensajes de discovery
        if self.discovery_manager and self.discovery_manager.process_discovery_message(mac_origen, mensaje):
            return
        
        # Procesar mensajes de seguridad
        if self.security_manager and self.security_manager.process_security_message(mac_origen, mensaje):
            return
        
        # Procesar mensajes de carpetas
        if self.folder_transfer and mensaje.startswith(('FOLDER_START:', 'FOLDER_FILE:', 'FOLDER_END:')):
            self.folder_transfer.handle_folder_message(mensaje, mac_origen)
            return
        
        # Procesar mensaje normal
        self.manejar_mensaje_recibido(mac_origen, mensaje)

    def salir(self):
        """Cierra la aplicación"""
        if messagebox.askokcancel("Salir", "¿Estás seguro?"):
            # Detener todos los servicios
            if self.discovery_manager:
                self.discovery_manager.stop_discovery()
            if self.security_manager:
                self.security_manager.disable_security()
            if self.folder_transfer:
                self.folder_transfer.cleanup_temp_files()
            if self.com:
                self.com.stop()
                self.stop_event.set()
            self.root.destroy()

def main():
    # Verificar Linux
    if not sys.platform.startswith('linux'):
        print("Solo funciona en Linux")
        return
    
     
    # CONFIGURACIONES PARA EVITAR ERRORES GRÁFICOS
    os.environ['TK_SILENCE_DEPRECATION'] = '1'

    # Crear ventana principal
    root = tk.Tk()
    
    # Configuración extra para VirtualBox
    root.tk.call('tk', 'scaling', 1.0)  # Deshabilitar escalado
    root.option_add('*tearOff', False)   # Deshabilitar menús tear-off

    # Reducir actualizaciones de UI
    root.option_add('*Listbox*background', 'white')
    root.option_add('*Listbox*foreground', 'black')
    
    
    # Configuración adicional para evitar errores gráficos
    root.option_add('*font', 'Arial 9')
    root.option_add('*Button*font', 'Arial 9')
    root.option_add('*Label*font', 'Arial 9')
    root.option_add('*Entry*font', 'Arial 9')
    
    app = ChatMinimalTkinter(root)
    root.protocol("WM_DELETE_WINDOW", app.salir)
    
    try:
        root.mainloop()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Chat Ethernet Minimal - Tkinter")
    print("Ejecutar con: sudo python3 app_tkinter_minimal.py")
    main()