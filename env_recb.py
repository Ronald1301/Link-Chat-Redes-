import socket
import threading
import time
import random
from mac import Mac
from frames import Frame
from fragmentation import FragmentManager


class Envio_recibo_frames:
    def __init__(self, tipo_protocolo=0x8888, interfaz = None):
        if interfaz is not None:
            resultado = Mac.obtener_mac(interfaz)
        else:
            resultado = Mac.obtener_mac()
            
        if resultado[0] is None:
            raise Exception(resultado[1])
        self.interfaz, self.mac_ori = resultado
        self.tipo_protocolo = tipo_protocolo
        self.mi_socket = None
        self.ejecutando = False
        self.canal_ocupado = False
        self.lock = threading.Lock()
        self.fragment_manager = FragmentManager()
        self.conectar()
        
        # Estadísticas de fragmentación
        self.estadisticas = {
            'mensajes_enviados': 0,
            'mensajes_recibidos': 0,
            'fragmentos_enviados': 0,
            'fragmentos_recibidos': 0,
            'mensajes_fragmentados': 0
        }

    def conectar(self):
        try:
            self.mi_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
            self.mi_socket.bind((self.interfaz, 0))
            print(f"✅ Conectado a interfaz {self.interfaz} con MAC {self.mac_ori}")
        except PermissionError:
            raise Exception("Se necesitan permisos de root (sudo)")
        except Exception as e:
            raise Exception(f"Error conectando a {self.interfaz}: {e}")
        
    def enviar_frame(self, frame: Frame):
        if not self.mi_socket:
            self.conectar()
        return self._enviar_con_csma(frame)
        
    def _enviar_con_csma(self, frame: Frame, max_intentos=16):
        intentos = 0
        
        while intentos < max_intentos:
            intentos += 1
            
            if not self._canal_libre():
                time.sleep(self._calcular_backoff(intentos))
                continue
            
            try:
                with self.lock:
                    self.canal_ocupado = True
                
                data = frame.serializar()
                bytes_enviados = self.mi_socket.send(data)
                
                time.sleep(0.001)
                return bytes_enviados
                
            except Exception as e:
                print(f"❌ Error en transmisión: {e}")
                return 0
            finally:
                with self.lock:
                    self.canal_ocupado = False
        
        print("💥 Demasiados intentos - transmisión fallida")
        return 0
    
    def _canal_libre(self, tiempo_escucha=0.000096):
        time.sleep(tiempo_escucha)
        with self.lock:
            return not self.canal_ocupado
    
    def _calcular_backoff(self, intento):
        k = min(intento, 10)
        slots = random.randint(0, 2**k - 1)
        return slots * 0.000512
    
    def enviar_mensaje(self, destino: str, mensaje: str, tipo_protocolo=None) -> bool:
        """
        Envía un mensaje, fragmentándolo si es necesario
        
        Returns:
            True si el mensaje fue enviado completamente, False si hubo error
        """
        if tipo_protocolo is None:
            tipo_protocolo = self.tipo_protocolo
        
        # Convertir mensaje a bytes
        datos = mensaje.encode('utf-8')
        
        try:
            # Fragmentar mensaje si es necesario
            fragmentos = self.fragment_manager.fragmentar_mensaje(datos)
            total_fragmentos = len(fragmentos)
            
            if total_fragmentos > 1:
                print(f"📦 Fragmentando mensaje de {len(datos)} bytes en {total_fragmentos} fragmentos")
                self.estadisticas['mensajes_fragmentados'] += 1
            
            # Enviar cada fragmento
            for i, (datos_fragmento, id_mensaje, num_fragmento, total_frags) in enumerate(fragmentos):
                frame = Frame(
                    mac_destino=destino,
                    mac_origen=self.mac_ori,            
                    tipo=tipo_protocolo,
                    datos=datos_fragmento,
                    es_fragmento=(total_frags > 1),
                    id_mensaje=id_mensaje,
                    num_fragmento=num_fragmento,
                    total_fragmentos=total_frags
                )
                
                frame.actualizar_crc()
                resultado = self.enviar_frame(frame)
                
                if resultado > 0:
                    self.estadisticas['fragmentos_enviados'] += 1
                    if total_frags > 1:
                        print(f"  📤 Enviando fragmento {num_fragmento+1}/{total_frags} ({len(datos_fragmento)} bytes)")
                else:
                    print(f"❌ Error enviando fragmento {num_fragmento+1}/{total_frags}")
                    return False
                
                # Pequeña pausa entre fragmentos para evitar saturación
                if i < len(fragmentos) - 1:
                    time.sleep(0.01)
            
            self.estadisticas['mensajes_enviados'] += 1
            if total_fragmentos > 1:
                print(f"✅ Mensaje fragmentado enviado completamente ({total_fragmentos} fragmentos)")
            return True
            
        except Exception as e:
            print(f"❌ Error enviando mensaje: {e}")
            return False
    
    def escuchar(self, callback=None):
        def _escuchar():
            self.ejecutando = True
            print(f"👂 Escuchando en {self.interfaz}...")
            
            while self.ejecutando:
                try:
                    packet = self.mi_socket.recv(4096)  # Buffer más grande para mensajes largos
                    
                    with self.lock:
                        self.canal_ocupado = True
                    
                    if len(packet) >= 72:  # Mínimo para frame básico
                        try:
                            frame = Frame.desde_bytes(packet)
                            
                            if frame.tipo == self.tipo_protocolo:
                                self._procesar_frame_recibido(frame, callback)
                        
                        except Exception as e:
                            print(f"Error procesando frame: {e}")
                    
                    time.sleep(0.01)
                    with self.lock:
                        self.canal_ocupado = False
                
                except Exception as e:
                    if self.ejecutando:
                        print(f"Error escuchando: {e}")
        
        thread = threading.Thread(target=_escuchar, daemon=True)
        thread.start()
        return thread
    
    def _procesar_frame_recibido(self, frame: Frame, callback):
        """Procesa un frame recibido, manejando fragmentación si es necesario"""
        self.estadisticas['fragmentos_recibidos'] += 1
        
        if frame.es_fragmento:
            # Es un fragmento de un mensaje más grande
            mensaje_completo = self.fragment_manager.agregar_fragmento(
                frame.id_mensaje, 
                frame.num_fragmento, 
                frame.total_fragmentos,
                frame.datos,
                frame.mac_origen
            )
            
            if mensaje_completo is not None:
                # ¡Mensaje completo reensamblado!
                self.estadisticas['mensajes_recibidos'] += 1
                print(f"🎉 Mensaje reensamblado: {len(mensaje_completo)} bytes de {frame.total_fragmentos} fragmentos")
                
                try:
                    mensaje = mensaje_completo.decode('utf-8')
                    if callback:
                        callback(frame.mac_origen, mensaje)
                except UnicodeDecodeError:
                    if callback:
                        callback(frame.mac_origen, mensaje_completo)
            else:
                # Aún faltan fragmentos
                estado = self.fragment_manager.obtener_estado_ensamblaje()
                print(f"📦 Fragmento {frame.num_fragmento+1}/{frame.total_fragmentos} recibido (pendientes: {estado['mensajes_pendientes']})")
        
        else:
            # Mensaje normal (no fragmentado)
            self.estadisticas['mensajes_recibidos'] += 1
            try:
                mensaje = frame.datos.rstrip(b'\x00').decode('utf-8')
                if callback:
                    callback(frame.mac_origen, mensaje)
            except UnicodeDecodeError:
                if callback:
                    callback(frame.mac_origen, frame.datos)
    
    def obtener_estadisticas(self):
        """Retorna estadísticas de fragmentación"""
        estado_ensamblaje = self.fragment_manager.obtener_estado_ensamblaje()
        return {**self.estadisticas, **estado_ensamblaje}
    
    def stop(self):
        self.ejecutando = False
        if self.mi_socket:
            self.mi_socket.close()
            print("🔌 Socket cerrado")