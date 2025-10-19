#!/usr/bin/env python3
import tkinter as tk
from tkinter import simpledialog, messagebox
import threading
import time
import sys
import os

# Importaciones de módulos propios
from config import setup_environment, configurar_tkinter
from app_state import AppState
from communication_manager import CommunicationManager
from ui_components import UIComponents
from file_transfer_handler import FileTransferHandler
from src.features.files import FileTransfer

class ChatMinimalTkinter:
    def __init__(self, root):
        self.root = root
        self.root.title("Link Chat")
        self.root.geometry("1000x1000")
        self.root.configure(bg='#2F2F2F')
        self.root.resizable(True, True)

        # Inicializar componentes
        self.app_state = AppState()
        self.communication_manager = CommunicationManager(self)
        self.file_transfer = FileTransfer(self)
        self.ui_components = UIComponents(root, self)
        self.file_handler = FileTransferHandler(self)
        
        # Crear interfaz
        self.crear_interfaz_minimal()

    @property
    def com(self):
        """Propiedad para compatibilidad con código existente"""
        return self.communication_manager.com if self.communication_manager else None
        
    def crear_interfaz_minimal(self):
        """Crea la interfaz minimalista"""
        main_frame = self.ui_components.crear_frame_principal()
        
        # Crear todas las secciones de la interfaz
        self.interfaz_var, self.interfaz_combo, self.btn_conectar = self.ui_components.crear_seccion_conexion(main_frame)
        self.status_label = self.ui_components.crear_seccion_informacion(main_frame)
        self.text_area = self.ui_components.crear_area_mensajes(main_frame)
        self.mensaje_entry, self.btn_enviar = self.ui_components.crear_seccion_entrada(main_frame)
        (self.btn_seleccionar, self.btn_seleccionar_carpeta, self.lbl_archivo, 
         self.btn_enviar_archivo, self.btn_enviar_carpeta) = self.ui_components.crear_seccion_archivos(main_frame)
        self.destino_var, self.destino_combo, self.btn_agregar_contacto = self.ui_components.crear_seccion_controles(main_frame)
        (self.btn_habilitar_seguridad, self.btn_buscar_dispositivos, 
         self.lbl_seguridad) = self.ui_components.crear_seccion_seguridad(main_frame)
        self.ui_components.crear_botones_control(main_frame)
        
        # Bind selección de destino
        self.destino_combo.bind('<<ComboboxSelected>>', self.actualizar_destino)

    # ========== MÉTODOS DE LA INTERFAZ ==========
    
    def insertar_nueva_linea(self, event=None):
        """Inserta una nueva línea cuando se presiona Shift+Enter"""
        self.mensaje_entry.insert(tk.INSERT, "\n")
        return "break"
    
    def actualizar_destino(self, event=None):
        """Actualiza el destino actual"""
        try:
            seleccion = self.destino_var.get()
            print(f"🔍 actualizar_destino: Selección del combobox: '{seleccion}'")
            
            if "(" in seleccion and ")" in seleccion:
                mac = seleccion.split("(")[1].split(")")[0].strip()
                print(f"🔍 actualizar_destino: MAC extraída: '{mac}'")
            else:
                mac = seleccion
            
            if self.app_state.validar_mac(mac):
                self.app_state.destino_actual = mac.upper().replace('-', ':')
                print(f"✅ Destino actualizado: {self.app_state.destino_actual}")
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

    def iniciar_comunicador(self):
        """Inicia el comunicador"""
        try:
            mac_propia = self.communication_manager.conectar(self.interfaz_var.get())
            self.habilitar_controles_chat()
            self.actualizar_estado(f"Conectado - {self.interfaz_var.get()} - MAC: {mac_propia}")
            self.mostrar_mensaje("Sistema", f"Conectado - Interfaz: {self.interfaz_var.get()} - Mi MAC: {mac_propia}")
            self.actualizar_destino()
            self.poll_incoming()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar: {str(e)}")
            self.actualizar_estado("Desconectado")

    def enviar_mensaje(self, event=None):
        """Envía mensaje de texto"""
        if event and event.keysym == 'Return' and event.state == 0:
            # Es un Enter simple (sin Shift)
            if not self.communication_manager.com:
                messagebox.showerror("Error", "Comunicador no inicializado")
                return "break"  # Prevenir el comportamiento por defecto
            
            self.actualizar_destino()
            mensaje = self.mensaje_entry.get('1.0', tk.END).strip()
            if not mensaje:
                return "break"  # Prevenir el comportamiento por defecto
            
            if self.communication_manager.enviar_mensaje(mensaje, self.app_state.destino_actual):
                self.mensaje_entry.delete('1.0', tk.END)
            
            return "break"  # Prevenir que se inserte nueva línea
        
        else:
            # Llamada desde el botón o otro lugar
            if not self.communication_manager.com:
                messagebox.showerror("Error", "Comunicador no inicializado")
                return
            
            self.actualizar_destino()
            mensaje = self.mensaje_entry.get('1.0', tk.END).strip()
            if not mensaje:
                return
            
            if self.communication_manager.enviar_mensaje(mensaje, self.app_state.destino_actual):
                self.mensaje_entry.delete('1.0', tk.END)

    def mostrar_mensaje(self, remitente, mensaje):
        """Muestra mensaje en el área de texto"""
        try:
            self.text_area.config(state=tk.NORMAL)
            
            if remitente in self.app_state.contactos:
                nombre = self.app_state.contactos[remitente]
            else:
                nombre = remitente
            
            timestamp = time.strftime("%H:%M:%S")
            
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

    def mostrar_progreso_envio(self, nombre_archivo, fragmentos_enviados, total_fragmentos, bytes_enviados=None):
        """Muestra progreso de envío de archivo"""
        progreso = (fragmentos_enviados / total_fragmentos) * 100 if total_fragmentos > 0 else 0
        
        if bytes_enviados:
            mb_enviados = bytes_enviados / (1024 * 1024)
            mensaje_progreso = f"📤 Enviando {nombre_archivo}: {progreso:.1f}% ({fragmentos_enviados}/{total_fragmentos} fragmentos, {mb_enviados:.1f} MB)"
        else:
            mensaje_progreso = f"📤 Enviando {nombre_archivo}: {progreso:.1f}% ({fragmentos_enviados}/{total_fragmentos} fragmentos)"
        
        # Actualizar barra de estado
        self.actualizar_estado(mensaje_progreso)
        
        # También mostrar en chat cada 10%
        if fragmentos_enviados % max(1, total_fragmentos // 10) == 0 or fragmentos_enviados == total_fragmentos:
            self.mostrar_mensaje("Sistema", mensaje_progreso)

    def mostrar_progreso_recepcion(self, mac_origen, fragmentos_recibidos, total_fragmentos, bytes_recibidos=None):
        """Muestra progreso de recepción de archivo"""
        progreso = (fragmentos_recibidos / total_fragmentos) * 100 if total_fragmentos > 0 else 0
        
        # Obtener nombre del remitente
        nombre_remitente = self.app_state.contactos.get(mac_origen, mac_origen)
        
        if bytes_recibidos:
            mb_recibidos = bytes_recibidos / (1024 * 1024)
            mensaje_progreso = f"📥 Recibiendo de {nombre_remitente}: {progreso:.1f}% ({fragmentos_recibidos}/{total_fragmentos} fragmentos, {mb_recibidos:.1f} MB)"
        else:
            mensaje_progreso = f"📥 Recibiendo de {nombre_remitente}: {progreso:.1f}% ({fragmentos_recibidos}/{total_fragmentos} fragmentos)"
        
        # Actualizar barra de estado
        self.actualizar_estado(mensaje_progreso)
        
        # También mostrar en chat cada 10%
        if fragmentos_recibidos % max(1, total_fragmentos // 10) == 0 or fragmentos_recibidos == total_fragmentos:
            self.mostrar_mensaje("Sistema", mensaje_progreso)

    def actualizar_destinos(self):
        """Actualiza la lista de destinos disponibles"""
        try:
            valores_combobox = [f"{nombre} ({mac})" for mac, nombre in self.app_state.contactos.items()]
            self.destino_combo['values'] = valores_combobox
            
            print(f"🔧 Destinos disponibles: {valores_combobox}")
            
            if valores_combobox and not self.destino_var.get():
                broadcast_item = next((item for item in valores_combobox if "FF:FF:FF:FF:FF:FF" in item), None)
                if broadcast_item:
                    self.destino_var.set(broadcast_item)
                    self.actualizar_destino()
                    print(f"🔧 Destino establecido por defecto: {self.app_state.destino_actual}")
                
        except Exception as e:
            print(f"❌ Error actualizando destinos: {e}")
    
    def agregar_contacto_simple(self):
        """Diálogo simple para agregar contacto"""
        mac = simpledialog.askstring("Agregar Contacto", "Dirección MAC (AA:BB:CC:DD:EE:FF):")
        if mac and self.app_state.validar_mac(mac):
            nombre = simpledialog.askstring("Agregar Contacto", "Nombre descriptivo:")
            if nombre:
                self.app_state.contactos[mac.upper()] = nombre
                self.app_state.guardar_contactos()
                self.actualizar_destinos()
                messagebox.showinfo("Éxito", "Contacto agregado")
        elif mac:
            messagebox.showerror("Error", "MAC inválida")

    # ========== MÉTODOS DE TRANSFERENCIA DE ARCHIVOS ==========
    
    def seleccionar_archivo(self):
        self.file_handler.seleccionar_archivo()

    def seleccionar_carpeta(self):
        self.file_handler.seleccionar_carpeta()

    def enviar_archivo(self):
        self.file_handler.enviar_archivo()

    def enviar_carpeta(self):
        self.file_handler.enviar_carpeta()

    def procesar_archivo_recibido(self, frame):
        self.file_handler.procesar_archivo_recibido(frame)

    # ========== MÉTODOS DE SEGURIDAD Y DESCUBRIMIENTO ==========
    
    def toggle_security(self):
        """Habilita/deshabilita la seguridad"""
        if not self.communication_manager.security_manager:
            return
        
        if self.communication_manager.security_manager.security_enabled:
            self.communication_manager.security_manager.disable_security()
            self.btn_habilitar_seguridad.config(text="Habilitar Seguridad")
            self.lbl_seguridad.config(text="Seguridad: Deshabilitada", fg='red')
        else:
            if self.communication_manager.security_manager.enable_security():
                self.btn_habilitar_seguridad.config(text="Deshabilitar Seguridad")
                self.lbl_seguridad.config(text="Seguridad: Habilitada", fg='green')
            else:
                messagebox.showerror("Error", "No se pudo habilitar la seguridad")
    
    def buscar_dispositivos(self):
        """Inicia búsqueda activa de dispositivos"""
        if not self.communication_manager.discovery_manager:
            return
        
        self.communication_manager.discovery_manager.send_discovery_request()
        self.mostrar_mensaje("Sistema", "Buscando dispositivos en la red...")
        
        # Mostrar dispositivos encontrados después de un momento
        self.root.after(3000, self.mostrar_dispositivos_encontrados)
    
    def mostrar_dispositivos_encontrados(self):
        """Muestra los dispositivos encontrados"""
        if not self.communication_manager.discovery_manager:
            return
        
        devices = self.communication_manager.discovery_manager.get_discovered_devices()
        count = len(devices)
        
        self.mostrar_mensaje("Sistema", f"Dispositivos encontrados: {count}")
        for mac, info in devices.items():
            self.mostrar_mensaje("Sistema", f"- {info['hostname']} ({mac})")
    
    def on_device_discovered(self, device_info: dict):
        """Callback cuando se descubre un nuevo dispositivo"""
        mac = device_info['mac']
        hostname = device_info['hostname']
        
        # Agregar a contactos automáticamente
        if mac not in self.app_state.contactos:
            self.app_state.contactos[mac] = hostname
            self.app_state.guardar_contactos()
            self.actualizar_destinos()
        
        # Notificar al usuario
        self.mostrar_mensaje("Discovery", f"Nuevo dispositivo: {hostname} ({mac})")

    # ========== MÉTODOS DE PROCESAMIENTO DE MENSAJES ==========
    
    def poll_incoming(self):
        """Revisa mensajes entrantes"""
        self.communication_manager.poll_incoming()
        self.root.after(40, self.poll_incoming)

    def procesar_mensaje_recibido_mejorado(self, mac_origen: str, mensaje: str):
        """Versión mejorada del procesamiento de mensajes"""
        
        # Procesar mensajes de discovery
        if (self.communication_manager.discovery_manager and 
            self.communication_manager.discovery_manager.process_discovery_message(mac_origen, mensaje)):
            return
        
        # Procesar mensajes de seguridad
        if (self.communication_manager.security_manager and 
            self.communication_manager.security_manager.process_security_message(mac_origen, mensaje)):
            return
        
        # Procesar mensajes de carpetas
        if (self.communication_manager.folder_transfer and 
            mensaje.startswith(('FOLDER_START:', 'FOLDER_FILE:', 'FOLDER_END:'))):
            self.communication_manager.folder_transfer.handle_folder_message(mensaje, mac_origen)
            return
        
        # Procesar mensaje normal
        self.manejar_mensaje_recibido(mac_origen, mensaje)

    def manejar_mensaje_recibido(self, mac_origen, mensaje):
        # Agregar a contactos si es nuevo
        if mac_origen not in self.app_state.contactos:
            self.app_state.contactos[mac_origen] = f"Dispositivo {mac_origen[-6:]}"
            self.app_state.guardar_contactos()
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

    # ========== MÉTODOS DE ESTADÍSTICAS ==========
    
    def mostrar_estadisticas(self):
        """Muestra estadísticas del sistema"""
        estadisticas = self.communication_manager.obtener_estadisticas()
        
        if not estadisticas:
            messagebox.showinfo("Estadísticas", "No hay conexión activa")
            return
        
        mensaje = "=== ESTADÍSTICAS DEL SISTEMA ===\n\n"
        mensaje += " COMUNICACIÓN:\n"
        mensaje += f"   • Mensajes enviados: {estadisticas.get('mensajes_enviados', 0)}\n"
        mensaje += f"   • Mensajes recibidos: {estadisticas.get('mensajes_recibidos', 0)}\n"
        mensaje += f"   • Mensajes fragmentados: {estadisticas.get('mensajes_fragmentados', 0)}\n\n"
        
        mensaje += " ARCHIVOS:\n"
        mensaje += f"   • Archivos enviados: {estadisticas.get('archivos_enviados', 0)}\n"
        mensaje += f"   • Archivos recibidos: {estadisticas.get('archivos_recibidos', 0)}\n\n"
        
        mensaje += " FRAGMENTACIÓN:\n"
        mensaje += f"   • Fragmentos enviados: {estadisticas.get('fragmentos_enviados', 0)}\n"
        mensaje += f"   • Fragmentos recibidos: {estadisticas.get('fragmentos_recibidos', 0)}\n"
        mensaje += f"   • Mensajes pendientes: {estadisticas.get('mensajes_pendientes', 0)}\n\n"
        
        mensaje += " PROTOCOLO:\n"
        mensaje += f"   • Frames de protocolo enviados: {estadisticas.get('frames_protocolo_enviados', 0)}\n\n"
        
        mensaje += " DESCUBRIMIENTO:\n"
        mensaje += f"   • Dispositivos descubiertos: {estadisticas.get('dispositivos_descubiertos', 0)}\n\n"
        
        mensaje += " SEGURIDAD:\n"
        mensaje += f"   • Canales seguros activos: {estadisticas.get('secure_channels', 0)}\n"
        mensaje += f"   • Sistema seguridad: {'Habilitado' if estadisticas.get('enabled', False) else ' Deshabilitado'}\n\n"
        
        mensaje += " CONTACTOS:\n"
        mensaje += f"   • Total contactos: {len(self.app_state.contactos)}\n"
        mensaje += f"   • Destino actual: {self.app_state.destino_actual}"
        
        messagebox.showinfo("Estadísticas del Sistema", mensaje)
    
    def reiniciar_estadisticas(self):
        """Reinicia las estadísticas del sistema"""
        respuesta = messagebox.askyesno(
            "Reiniciar Estadísticas", 
            "¿Está seguro de que desea reiniciar todas las estadísticas a cero?"
        )
        
        if respuesta:
            self.communication_manager.reiniciar_estadisticas()
            messagebox.showinfo("Estadísticas Reiniciadas", "Todas las estadísticas han sido reiniciadas a cero.")

    def salir(self):
        """Cierra la aplicación"""
        if messagebox.askokcancel("Salir", "¿Estás seguro?"):
            self.communication_manager.desconectar()
            if self.communication_manager.folder_transfer:
                self.communication_manager.folder_transfer.cleanup_temp_files()
            self.root.destroy()

def main():
    # Verificar Linux
    if not sys.platform.startswith('linux'):
        print("Solo funciona en Linux")
        return
    
    # Configurar entorno
    setup_environment()
    configurar_tkinter()
    
    # Crear directorio de descargas si no existe
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    
    # Crear ventana principal
    root = tk.Tk()
    
    # Configuración extra para VirtualBox
    root.tk.call('tk', 'scaling', 1.0)
    root.option_add('*tearOff', False)
    
    # Configuración adicional para evitar errores gráficos
    root.option_add('*font', 'Arial 9')
    root.option_add('*Button*font', 'Arial 9')
    root.option_add('*Label*font', 'Arial 9')
    root.option_add('*Entry*font', 'Arial 9')
    
    # Crear aplicación
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