#!/usr/bin/env python3
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, filedialog, ttk
import threading
import time
import sys
import os
import json
from env_recb import Envio_recibo_frames
from files import FileTransfer

# Configuración para VirtualBox - evitar problemas gráficos
os.environ['TK_SILENCE_DEPRECATION'] = '1'

class ChatMinimalTkinter:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Ethernet")
        self.root.geometry("500x450")  # Un poco más alto para los botones de archivo
        
        # Configuración minimalista
        self.root.resizable(True, True)
        self.root.configure(bg='white')
        
        # Variables
        self.com = None
        self.contactos = {}
        self.destino_actual = "FF:FF:FF:FF:FF:FF"
        self.archivo_contactos = "contactos_minimal.json"
        self.file_transfer = FileTransfer(self)
        self.archivo_seleccionado = None
        
        self.cargar_contactos()
        self.crear_interfaz_minimal()
        self.iniciar_comunicador()

    def send_message(self, mensaje, dest_mac):
        """Envía un mensaje (necesario para FileTransfer)"""
        if not self.com:
            return False
        
        try:
            resultado = self.com.enviar_mensaje(dest_mac, mensaje)
            return resultado > 0
        except Exception as e:
            print(f"Error en send_message: {e}")
            return False
        
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
        """Interfaz ultra-minimalista con botones de archivo"""
        
        # Frame principal simple
        main_frame = tk.Frame(self.root, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Información básica
        info_frame = tk.Frame(main_frame, bg='white')
        info_frame.pack(fill=tk.X, pady=2)
        
        self.status_label = tk.Label(info_frame, text="Desconectado", bg='white', fg='red')
        self.status_label.pack(side=tk.LEFT)
        
        # Área de mensajes (más pequeña)
        self.text_area = scrolledtext.ScrolledText(
            main_frame, 
            wrap=tk.WORD,
            width=50,
            height=12,
            font=('Arial', 9)
        )
        self.text_area.pack(fill=tk.BOTH, expand=True, pady=5)
        self.text_area.config(state=tk.DISABLED)
        
        # === SECCIÓN DE ARCHIVOS SIMPLIFICADA ===
        file_frame = tk.Frame(main_frame, bg='white')
        file_frame.pack(fill=tk.X, pady=2)
        
        # Botón para seleccionar archivo (sin emojis ni colores)
        self.btn_seleccionar = tk.Button(
            file_frame, 
            text="Seleccionar Archivo",
            command=self.seleccionar_archivo,
            width=15
        )
        self.btn_seleccionar.pack(side=tk.LEFT, padx=2)
        
        # Etiqueta del archivo seleccionado
        self.lbl_archivo = tk.Label(
            file_frame, 
            text="Ningun archivo", 
            bg='white', 
            fg='black'
        )
        self.lbl_archivo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Botón para enviar archivo (sin emojis ni colores)
        self.btn_enviar_archivo = tk.Button(
            file_frame, 
            text="Enviar Archivo",
            command=self.enviar_archivo,
            state=tk.DISABLED,
            width=15
        )
        self.btn_enviar_archivo.pack(side=tk.RIGHT, padx=2)
        
        # Controles simples
        control_frame = tk.Frame(main_frame, bg='white')
        control_frame.pack(fill=tk.X, pady=2)
        
        # Destino con Combobox simple
        tk.Label(control_frame, text="Para:", bg='white').pack(side=tk.LEFT)
        
        self.destino_var = tk.StringVar(value="FF:FF:FF:FF:FF:FF")
        self.destino_combo = tk.Listbox(control_frame, height=4, width=25, exportselection=0)
        self.destino_combo.pack(side=tk.LEFT, padx=2)
        
        # Actualizar lista de destinos
        self.actualizar_destinos()
        
        # Botón para agregar contacto
        tk.Button(control_frame, text="+", command=self.agregar_contacto_simple, 
                 width=2).pack(side=tk.LEFT, padx=2)
        
        # Entrada de mensaje
        msg_frame = tk.Frame(main_frame, bg='white')
        msg_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(msg_frame, text="Mensaje:", bg='white').pack(side=tk.LEFT)
        self.mensaje_var = tk.StringVar()
        self.mensaje_entry = tk.Entry(msg_frame, textvariable=self.mensaje_var, width=40)
        self.mensaje_entry.pack(side=tk.LEFT, padx=2)
        self.mensaje_entry.bind('<Return>', self.enviar_mensaje)
        
        # Botones básicos
        btn_frame = tk.Frame(main_frame, bg='white')
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="Enviar", command=self.enviar_mensaje, width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Limpiar", command=self.limpiar_mensajes, width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Salir", command=self.salir, width=8).pack(side=tk.LEFT, padx=2)
        
        # Bind selección de destino
        self.destino_combo.bind('<<ListboxSelect>>', self.seleccionar_destino)
    
    def seleccionar_archivo(self):
        """Selecciona un archivo para enviar"""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo para enviar"
        )
        
        if file_path:
            self.archivo_seleccionado = file_path
            nombre_archivo = os.path.basename(file_path)
            
            self.lbl_archivo.config(text=nombre_archivo)
            self.btn_enviar_archivo.config(state=tk.NORMAL)
            
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
    
    def _callback_envio_archivo(self, exito, mensaje):
        """Callback cuando termina el envío del archivo"""
        # Rehabilitar botones
        self.btn_seleccionar.config(state=tk.NORMAL)
        
        if exito:
            nombre_archivo = os.path.basename(self.archivo_seleccionado)
            self.mostrar_mensaje("Sistema", f"Archivo enviado: {nombre_archivo}")
            
            # Limpiar selección
            self.archivo_seleccionado = None
            self.lbl_archivo.config(text="Ningun archivo")
        else:
            self.btn_enviar_archivo.config(state=tk.NORMAL)
            self.mostrar_mensaje("Error", f"Fallo en envio: {mensaje}")
    
    def actualizar_destinos(self):
        """Actualiza la lista de destinos disponibles"""
        self.destino_combo.delete(0, tk.END)
        
        for mac, nombre in self.contactos.items():
            self.destino_combo.insert(tk.END, f"{nombre} ({mac})")
        
        # Seleccionar el primero por defecto
        if self.destino_combo.size() > 0:
            self.destino_combo.selection_set(0)
            self.seleccionar_destino()
    
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
        def _iniciar():
            try:
                if os.geteuid() != 0:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Ejecuta con sudo!"))
                    return
                
                self.com = Envio_recibo_frames()
                mac_propia = self.com.mac_ori
                
                self.root.after(0, lambda: self.actualizar_estado(f"Conectado - MAC: {mac_propia}"))
                self.root.after(0, lambda: self.mostrar_mensaje("Sistema", f"Conectado - Mi MAC: {mac_propia}"))
                
                # Modificar el escuchador para manejar archivos
                self.com.escuchar(callback=self.manejar_mensaje_recibido)
                
            except Exception as e:
                self.root.after(0, lambda: self.mostrar_mensaje("Error", str(e)))
        
        threading.Thread(target=_iniciar, daemon=True).start()
    
    def manejar_mensaje_recibido(self, mac_origen, mensaje):
        """Maneja mensajes recibidos (texto y archivos)"""
        if isinstance(mensaje, bytes):
            try:
                mensaje = mensaje.decode('utf-8')
            except:
                mensaje = f"[Datos: {len(mensaje)} bytes]"
        
        # Procesar mensajes de archivo
        if mensaje.startswith(("FILE_METADATA:", "FILE_CHUNK:", "FILE_END:")):
            self.root.after(0, lambda: self.file_transfer.receive_file(mensaje, mac_origen))
        else:
            # Agregar a contactos si es nuevo
            if mac_origen not in self.contactos:
                self.contactos[mac_origen] = f"Dispositivo {mac_origen[-6:]}"
                self.guardar_contactos()
                self.root.after(0, self.actualizar_destinos)
            
            self.root.after(0, lambda: self.mostrar_mensaje(mac_origen, mensaje))
    
    def enviar_mensaje(self, event=None):
        """Envía mensaje de texto"""
        if not self.com:
            messagebox.showerror("Error", "Comunicador no inicializado")
            return
        
        mensaje = self.mensaje_var.get().strip()
        if not mensaje:
            return
        
        self.mensaje_var.set("")
        threading.Thread(target=lambda: self._enviar(mensaje), daemon=True).start()
    
    def _enviar(self, mensaje):
        """Envía mensaje en hilo separado"""
        try:
            resultado = self.com.enviar_mensaje(self.destino_actual, mensaje)
            if resultado > 0:
                self.root.after(0, lambda: self.mostrar_mensaje("Yo", f"→ {mensaje}"))
        except Exception as e:
            self.root.after(0, lambda: self.mostrar_mensaje("Error", f"Envío fallido: {e}"))
    
    def mostrar_mensaje(self, remitente, mensaje):
        """Muestra mensaje en el área de texto"""
        self.text_area.config(state=tk.NORMAL)
        
        # Usar nombre amigable si está en contactos
        if remitente in self.contactos:
            nombre = self.contactos[remitente]
        else:
            nombre = remitente
        
        timestamp = time.strftime("%H:%M:%S")
        self.text_area.insert(tk.END, f"[{timestamp}] {nombre}: {mensaje}\n")
        self.text_area.see(tk.END)
        self.text_area.config(state=tk.DISABLED)
    
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
    
    def salir(self):
        """Cierra la aplicación"""
        if messagebox.askokcancel("Salir", "¿Estás seguro?"):
            if self.com:
                self.com.stop()
            self.root.destroy()

def main():
    # Verificar Linux
    if not sys.platform.startswith('linux'):
        print("Solo funciona en Linux")
        return
    
    # Crear ventana principal
    root = tk.Tk()
    
    # Configuración extra para VirtualBox
    root.tk.call('tk', 'scaling', 1.0)  # Deshabilitar escalado
    root.option_add('*tearOff', False)   # Deshabilitar menús tear-off
    
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