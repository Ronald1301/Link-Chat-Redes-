import tkinter as tk
from tkinter import scrolledtext, ttk
from config import *

class UIComponents:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        
    def crear_frame_principal(self):
        """Crea el frame principal"""
        main_frame = tk.Frame(self.root, bg=bg_color, highlightbackground=border_color, highlightthickness=1)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        return main_frame

    def crear_seccion_conexion(self, parent):
        """Crea la sección de conexión"""
        interfaz_frame = tk.Frame(parent, bg=bg_color, highlightbackground=border_color, highlightthickness=1)
        interfaz_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(interfaz_frame, text="Interfaz:", bg=bg_color, fg=fg_color, font=(font_family, font_size)).pack(side=tk.LEFT)
        
        # Obtener interfaces disponibles
        from src.core.mac import Mac
        interfaces = Mac.obtener_interfaces_fisicas()
        
        if not interfaces:
            tk.Label(interfaz_frame, text="No hay interfaces disponibles", bg=bg_color, fg='red', font=(font_family, font_size)).pack(side=tk.LEFT)
            return None, None, None
        
        interfaz_var = tk.StringVar()
        interfaz_combo = ttk.Combobox(
            interfaz_frame, 
            textvariable=interfaz_var,
            values=interfaces,
            state="readonly",
            width=20
        )
        interfaz_combo.pack(side=tk.LEFT, padx=5)
        interfaz_combo.set(interfaces[0])
        
        btn_conectar = tk.Button(
            interfaz_frame,
            text="Conectar",
            command=self.app.conectar_interfaz,
            width=10,
            bg=button_bg,
            fg=fg_color,
            font=(font_family, font_size),
            relief="solid",
            bd=1
        )
        btn_conectar.pack(side=tk.LEFT, padx=5)
        
        return interfaz_var, interfaz_combo, btn_conectar

    def crear_seccion_informacion(self, parent):
        """Crea la sección de información"""
        info_frame = tk.Frame(parent, bg=bg_color, highlightbackground=border_color, highlightthickness=1)
        info_frame.pack(fill=tk.X, pady=2)
        
        status_label = tk.Label(info_frame, text="Desconectado", bg=bg_color, fg='red', font=(font_family, font_size))
        status_label.pack(side=tk.LEFT)
        
        return status_label

    def crear_area_mensajes(self, parent):
        """Crea el área de mensajes"""
        text_area = scrolledtext.ScrolledText(
            parent, 
            wrap=tk.WORD,
            width=50,
            height=12,
            font=(font_family, font_size),
            bg=bg_color,
            fg=fg_color,
            insertbackground=fg_color,
            relief="solid",
            bd=1
        )
        text_area.pack(fill=tk.BOTH, expand=True, pady=5)
        text_area.config(state=tk.DISABLED)
        return text_area

    def crear_seccion_entrada(self, parent):
        """Crea la sección de entrada de mensajes"""
        msg_frame = tk.Frame(parent, bg=bg_color, highlightbackground=border_color, highlightthickness=1)
        msg_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(msg_frame, text="Mensaje:", bg=bg_color, fg=fg_color, font=(font_family, font_size)).pack(side=tk.LEFT)
        
        input_frame = tk.Frame(msg_frame, bg=bg_color)
        input_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        mensaje_entry = tk.Text(
            input_frame, 
            height=3,
            font=(font_family, font_size),
            bg=entry_bg,
            fg=fg_color,
            insertbackground=fg_color,
            relief="solid",
            bd=1,
            wrap=tk.WORD
        )
        mensaje_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        mensaje_entry.bind('<Return>', self.app.enviar_mensaje)
        mensaje_entry.bind('<Shift-Return>', self.app.insertar_nueva_linea)
        
        btn_enviar = tk.Button(
            input_frame, 
            text="Enviar", 
            command=self.app.enviar_mensaje, 
            width=8,
            bg=button_bg,
            fg=fg_color,
            font=(font_family, font_size),
            state=tk.DISABLED,
            relief="solid",
            bd=1
        )
        btn_enviar.pack(side=tk.LEFT, padx=2)
        
        return mensaje_entry, btn_enviar

    def crear_seccion_archivos(self, parent):
        """Crea la sección de transferencia de archivos"""
        file_frame = tk.Frame(parent, bg=bg_color, highlightbackground=border_color, highlightthickness=1)
        file_frame.pack(fill=tk.X, pady=2)
        
        # Primera fila: Selección
        file_row1 = tk.Frame(file_frame, bg=bg_color)
        file_row1.pack(fill=tk.X, pady=1)
        
        btn_seleccionar = tk.Button(
            file_row1, 
            text="Seleccionar Archivo",
            command=self.app.seleccionar_archivo,
            width=15,
            bg=button_bg,
            fg=fg_color,
            font=(font_family, font_size),
            relief="solid",
            bd=1
        )
        btn_seleccionar.pack(side=tk.LEFT, padx=2)
        
        btn_seleccionar_carpeta = tk.Button(
            file_row1, 
            text="Seleccionar Carpeta",
            command=self.app.seleccionar_carpeta,
            width=15,
            bg=button_bg,
            fg=fg_color,
            font=(font_family, font_size),
            relief="solid",
            bd=1
        )
        btn_seleccionar_carpeta.pack(side=tk.LEFT, padx=2)
        
        lbl_archivo = tk.Label(
            file_row1, 
            text="Ningun elemento seleccionado", 
            bg=bg_color, 
            fg=fg_color,
            font=(font_family, font_size)
        )
        lbl_archivo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Segunda fila: Envío
        file_row2 = tk.Frame(file_frame, bg=bg_color)
        file_row2.pack(fill=tk.X, pady=1)
        
        btn_enviar_archivo = tk.Button(
            file_row2, 
            text="Enviar Archivo",
            command=self.app.enviar_archivo,
            state=tk.DISABLED,
            width=15,
            bg=button_bg,
            fg=fg_color,
            font=(font_family, font_size),
            relief="solid",
            bd=1
        )
        btn_enviar_archivo.pack(side=tk.LEFT, padx=2)
        
        btn_enviar_carpeta = tk.Button(
            file_row2, 
            text="Enviar Carpeta",
            command=self.app.enviar_carpeta,
            state=tk.DISABLED,
            width=15,
            bg=button_bg,
            fg=fg_color,
            font=(font_family, font_size),
            relief="solid",
            bd=1
        )
        btn_enviar_carpeta.pack(side=tk.LEFT, padx=2)
        
        return btn_seleccionar, btn_seleccionar_carpeta, lbl_archivo, btn_enviar_archivo, btn_enviar_carpeta

    def crear_seccion_controles(self, parent):
        """Crea la sección de controles"""
        control_frame = tk.Frame(parent, bg=bg_color, highlightbackground=border_color, highlightthickness=1)
        control_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(control_frame, text="Para:", bg=bg_color, fg=fg_color, font=(font_family, font_size)).pack(side=tk.LEFT)
        
        destino_var = tk.StringVar(value="FF:FF:FF:FF:FF:FF")
        destino_combo = ttk.Combobox(
            control_frame, 
            textvariable=destino_var,
            values=list(self.app.app_state.contactos.keys()),
            state="readonly",
            width=25
        )
        destino_combo.pack(side=tk.LEFT, padx=2)
        
        btn_agregar_contacto = tk.Button(
            control_frame, 
            text="+", 
            command=self.app.agregar_contacto_simple, 
            width=2,
            state=tk.DISABLED,
            bg=button_bg,
            fg=fg_color,
            font=(font_family, font_size),
            relief="solid",
            bd=1
        )
        btn_agregar_contacto.pack(side=tk.LEFT, padx=2)
        
        return destino_var, destino_combo, btn_agregar_contacto

    def crear_seccion_seguridad(self, parent):
        """Crea la sección de seguridad"""
        security_frame = tk.Frame(parent, bg=bg_color, highlightbackground=border_color, highlightthickness=1)
        security_frame.pack(fill=tk.X, pady=2)
        
        btn_habilitar_seguridad = tk.Button(
            security_frame, 
            text="Habilitar Seguridad",
            command=self.app.toggle_security,
            width=15,
            bg=button_bg,
            fg=fg_color,
            font=(font_family, font_size),
            relief="solid",
            bd=1,
            state=tk.DISABLED
        )
        btn_habilitar_seguridad.pack(side=tk.LEFT, padx=2)
        
        btn_buscar_dispositivos = tk.Button(
            security_frame, 
            text="Buscar Dispositivos",
            command=self.app.buscar_dispositivos,
            width=15,
            bg=button_bg,
            fg=fg_color,
            font=(font_family, font_size),
            relief="solid",
            bd=1,
            state=tk.DISABLED
        )
        btn_buscar_dispositivos.pack(side=tk.LEFT, padx=2)
        
        lbl_seguridad = tk.Label(
            security_frame, 
            text="Seguridad: Deshabilitada", 
            bg=bg_color, 
            fg='red',
            font=(font_family, font_size)
        )
        lbl_seguridad.pack(side=tk.LEFT, padx=10)
        
        return btn_habilitar_seguridad, btn_buscar_dispositivos, lbl_seguridad

    def crear_botones_control(self, parent):
        """Crea los botones de control"""
        btn_frame = tk.Frame(parent, bg=bg_color, highlightbackground=border_color, highlightthickness=1)
        btn_frame.pack(fill=tk.X, pady=5)

        tk.Button(btn_frame, text="Limpiar", command=self.app.limpiar_mensajes, 
                 width=8, bg=button_bg, fg=fg_color, font=(font_family, font_size), 
                 relief="solid", bd=1).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Estadísticas", command=self.app.mostrar_estadisticas, 
                 width=10, bg=button_bg, fg=fg_color, font=(font_family, font_size), 
                 relief="solid", bd=1).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Reset Stats", command=self.app.reiniciar_estadisticas, 
                 width=10, bg=button_bg, fg=fg_color, font=(font_family, font_size), 
                 relief="solid", bd=1).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Salir", command=self.app.salir, 
                 width=8, bg=button_bg, fg=fg_color, font=(font_family, font_size), 
                 relief="solid", bd=1).pack(side=tk.LEFT, padx=2)