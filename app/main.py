#!/usr/bin/env python3
import signal
import sys
import time
from env_recb import Envio_recibo_frames

class AplicacionMensajeria:
    def __init__(self):
        self.comunicador = None
        self.contactos = {}
        self.ejecutando = True
        
    def inicializar(self):
        """Inicializa la aplicación"""
        try:
            print("🚀 Inicializando aplicación de mensajería...")
            self.comunicador = Envio_recibo_frames(tipo_protocolo=0x8888)
            
            # Configurar manejador de señales para Ctrl+C
            signal.signal(signal.SIGINT, self.manejar_terminacion)
            signal.signal(signal.SIGTERM, self.manejar_terminacion)
            
            return True
        except Exception as e:
            print(f"❌ Error inicializando: {e}")
            return False
    
    def manejar_mensaje_recibido(self, mac_origen, mensaje):
        """Callback para mensajes entrantes"""
        nombre = self.contactos.get(mac_origen, mac_origen)
        print(f"\n💬 [{time.strftime('%H:%M:%S')}] {nombre}: {mensaje}")
        
        # Auto-respuesta para demostración
        if "hola" in mensaje.lower() and mac_origen not in self.contactos:
            self.agregar_contacto(mac_origen)
            time.sleep(1)
            self.enviar_mensaje(mac_origen, "¡Hola! Bienvenido al chat.")
    
    def agregar_contacto(self, mac):
        """Agrega un nuevo contacto"""
        if mac not in self.contactos:
            nombre = input(f"🤔 Nuevo contacto {mac}. ¿Cómo quieres llamarlo? ")
            self.contactos[mac] = nombre or mac
            print(f"✅ Contacto agregado: {nombre}")
    
    def enviar_mensaje(self, destino, mensaje):
        """Envía un mensaje a un destino"""
        try:
            if len(mensaje) == 0:
                print("⚠️  Mensaje vacío")
                return
            
            print(f"📤 Enviando a {destino}...")
            resultado = self.comunicador.enviar_mensaje(destino, mensaje)
            
            if resultado > 0:
                nombre = self.contactos.get(destino, destino)
                print(f"✅ Mensaje enviado a {nombre}")
            else:
                print("❌ Error enviando mensaje")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def modo_chat_interactivo(self):
        """Modo chat interactivo"""
        print("\n" + "="*50)
        print("💬 CHAT DE CAPA DE ENLACE")
        print("="*50)
        print("Comandos:")
        print("  /contactos - Ver lista de contactos")
        print("  /salir - Salir de la aplicación")
        print("  /ayuda - Mostrar esta ayuda")
        print("="*50)
        
        # Iniciar escucha de mensajes
        self.comunicador.escuchar(callback=self.manejar_mensaje_recibido)
        
        while self.ejecutando:
            try:
                comando = input("\n📝 Ingresa MAC destino o comando: ").strip()
                
                if comando.lower() == '/salir':
                    break
                elif comando.lower() == '/contactos':
                    self.mostrar_contactos()
                elif comando.lower() == '/ayuda':
                    self.mostrar_ayuda()
                elif comando.startswith('/'):
                    print("❌ Comando no reconocido")
                else:
                    # Asumimos que es una MAC destino
                    destino = comando
                    if not self.validar_mac(destino):
                        print("❌ Formato de MAC inválido (usar aa:bb:cc:dd:ee:ff)")
                        continue
                    
                    mensaje = input("💭 Mensaje: ").strip()
                    if mensaje:
                        self.enviar_mensaje(destino, mensaje)
                    else:
                        print("⚠️  Mensaje vacío")
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def validar_mac(self, mac):
        """Valida el formato de una dirección MAC"""
        partes = mac.split(':')
        if len(partes) != 6:
            return False
        for parte in partes:
            if len(parte) != 2 or not all(c in '0123456789abcdefABCDEF' for c in parte):
                return False
        return True
    
    def mostrar_contactos(self):
        """Muestra la lista de contactos"""
        if not self.contactos:
            print("📞 No hay contactos guardados")
        else:
            print("📞 Lista de contactos:")
            for mac, nombre in self.contactos.items():
                print(f"  {nombre} ({mac})")
    
    def mostrar_ayuda(self):
        """Muestra la ayuda"""
        print("""
🤖 Aplicación de Mensajería - Capa de Enlace

Esta aplicación permite enviar mensajes directamente a nivel Ethernet
usando el protocolo CSMA para el control de acceso al medio.

CARACTERÍSTICAS:
• Comunicación directa dispositivo a dispositivo
• Protocolo CSMA para evitar colisiones
• Frames Ethernet personalizados (tipo 0x8888)
• Chat en tiempo real

USO:
1. Ingresa la MAC destino (formato aa:bb:cc:dd:ee:ff)
2. Escribe tu mensaje
3. Presiona Enter para enviar

Los mensajes se enviarán usando el algoritmo CSMA que:
1. Escucha el canal antes de transmitir
2. Si está ocupado, espera un tiempo aleatorio
3. Transmite cuando el canal está libre
4. Reintenta en caso de colisión
        """)
    
    def manejar_terminacion(self, signum, frame):
        """Maneja la terminación graceful de la aplicación"""
        print("\n\n🛑 Cerrando aplicación...")
        self.ejecutando = False
        if self.comunicador:
            self.comunicador.stop()
        sys.exit(0)
    
    def ejecutar(self):
        """Método principal de la aplicación"""
        if not self.inicializar():
            return
        
        print("✅ Aplicación inicializada correctamente")
        print(f"📡 Interface: {self.comunicador.interfaz}")
        print(f"🔑 MAC local: {self.comunicador.mac_ori}")
        print(f"📊 Protocolo: 0x{self.comunicador.tipo_protocolo:04x}")
        
        self.modo_chat_interactivo()
        
        # Limpieza final
        if self.comunicador:
            self.comunicador.stop()

def main():
    """Función principal"""
    print("💬 Aplicación de Mensajería - Capa de Enlace")
    print("⚠️  Debes ejecutar con: sudo python3 chat_app.py")
    
    app = AplicacionMensajeria()
    app.ejecutar()

if __name__ == "__main__":
    main()