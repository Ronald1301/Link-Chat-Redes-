import socket
import threading
import time
import random
import queue
from mac import Mac
from frames import Frame, Tipo_Mensaje
from fragmentation import FragmentManager
import struct
from typing import Callable, Optional, Union

class Envio_recibo_frames:
    def __init__(self, interfaz = None):
        if interfaz is not None:
            resultado = Mac.obtener_mac(interfaz)
        else:
            resultado = Mac.obtener_mac()
        if resultado[0] is None:
            raise Exception(resultado[1])
        self.interfaz, self.mac_ori = resultado
        self.tipo_protocolo = 0x88B5
        self.mi_socket = None
        self.ejecutando = True
        self.canal_ocupado = False
        self.lock = threading.Lock()
        self.fragment_manager = FragmentManager()
        self.cola_mensajes = queue.Queue()
        self.conectar()

    def conectar(self):
        try:
            self.mi_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x88B5))
            self.mi_socket.bind((self.interfaz, 0))
            print(f"✅ Conectado a interfaz {self.interfaz} con MAC {self.mac_ori}")
            
        except PermissionError:
            raise Exception("Se necesitan permisos de root (sudo)")
        except Exception as e:
            raise Exception(f"Error conectando a {self.interfaz}: {e}")
        
    def enviar_frame(self, frames):
        for i, frame in enumerate(frames):
            try:
                print(f"📤 Frame {i+1}/{len(frames)}: {len(frame)} bytes")
                print(f"📤 Primeros 50 bytes hex: {frame.hex()[:100]}...")
                self.mi_socket.send(frame)
            except Exception as e:
                print(f"Error enviando frame {i+1}: {e}")
                raise

    def recibir_frame(self, buff_size=65535):
        try:
            print("👂 recibir_frame: Esperando frame...")
            frame, addr = self.mi_socket.recvfrom(buff_size)
            print(f"Frame recibido de {addr}: {len(frame)} bytes")
            return frame
        except socket.timeout:
            return None
        except Exception as e:
            print(f"Error en recibir_frame: {e}")
            return None
        
    def recibir_thread(self, stop_event):
        try:
            self.mi_socket.settimeout(1.0)
            print("🎧 recibir_thread: Iniciado")

            frame_count = 0
            our_protocol_count = 0
            our_mac_count = 0
            broadcast_count = 0
            other_mac_count = 0
            
            while not stop_event.is_set():
                try:
                    frame = self.recibir_frame()

                    if frame is None:
                        continue 

                    frame_count += 1
                    if len(frame) >= 14:
                        # Extraer MAC destino (primeros 6 bytes)
                        mac_dest_bytes = frame[0:6]
                        mac_dest = ':'.join(f'{b:02x}' for b in mac_dest_bytes).upper()
                        
                        # Extraer MAC origen (siguientes 6 bytes)
                        mac_orig_bytes = frame[6:12]
                        mac_orig = ':'.join(f'{b:02x}' for b in mac_orig_bytes).upper()
                        
                        # Extraer EtherType
                        eth_type = struct.unpack('>H', frame[12:14])[0]
                            
                        # Determinar tipo de frame
                        if eth_type == 0x88B5:
                            our_protocol_count += 1
                            frame_type = "NUESTRO_PROTOCOLO"
                        else:
                            frame_type = f"OTRO_PROTOCOLO(0x{eth_type:04x})"
                            
                        # Determinar destino
                        if mac_dest == "FF:FF:FF:FF:FF:FF":
                            broadcast_count += 1
                            dest_type = "BROADCAST"
                        elif mac_dest == self.mac_ori.upper():
                            our_mac_count += 1
                            dest_type = "NUESTRA_MAC"
                        else:
                            other_mac_count += 1
                            dest_type = "OTRA_MAC"
                            
                        # Mostrar información del frame
                        print(f"📥 Frame #{frame_count}: {dest_type} | {frame_type}")
                        print(f"   - Destino: {mac_dest} | Origen: {mac_orig}")
                        print(f"   - Tamaño: {len(frame)} bytes")
                            
                        # Solo procesar frames de nuestro protocolo
                        if eth_type == 0x88B5:
                            decoded_frame = self.decodificar_frame(frame)
                            if decoded_frame:
                                self.cola_mensajes.put(decoded_frame)
                            else:
                                print(f"📥 Frame #{frame_count}: Tamaño insuficiente ({len(frame)} bytes)")
                            
                except socket.timeout:
                    continue
        except Exception as e:
            print(f"❌ Error en recibir_thread: {e}")
        finally:
            self.stop()


    def crear_frame(self, mac_destino: str, tipo_mensaje: int, mensaje: Union[bytes, str], 
                    nombre_archivo: str = None) -> bytes:
        #Estructura: [6b MAC destino] + [6b MAC origen] + [2b EtherType] + [1b tipo] + [2b longitud] + [datos]
        
        if isinstance(mensaje, str):
            mensaje_bytes = mensaje.encode('utf-8')
        else:
            mensaje_bytes = mensaje


        if nombre_archivo is not None: 
            nombre_bytes = nombre_archivo.encode('utf-8')
            largo_nombre = len(nombre_archivo)
            mensaj_bytes = (largo_nombre.to_bytes(2, 'big') + nombre_bytes + mensaje_bytes)
        else:
            mensaj_bytes = mensaje_bytes

        longitud = len(mensaje_bytes)
        id_mensaje = int(time.time() * 1000) % 65536
        offset = 0
        el_origen = self.mac_ori 
        numero_fragmento = 0
        frames =[]

        if(longitud <= 1475):
            # Construir frame
            frame = Frame(
                destino = mac_destino,
                origen= el_origen,
                tipo_mensaje = tipo_mensaje,
                id= id_mensaje,
                fragment_num= 0,
                total= 0,
                Datos= mensaje_bytes
            )
        
            print(f"📦 Frame creado:")
            print(f"   → MAC destino: {mac_destino}")
            print(f"   → MAC origen:  {self.mac_ori}")
            print(f"   → EtherType:   0x{self.tipo_protocolo:04x}")
            print(f"   → Tipo:        {tipo_mensaje}")
            print(f"   → Longitud:    {longitud} bytes")
            print(f"   → Datos:       '{mensaje[:50]}{'...' if len(mensaje) > 50 else ''}'")
            #print(f"🔧 Frame completo: {len(frame)} bytes")
            frames.append(frame.hacia_bytes())
            return frames
    
        total_fragmentos = (longitud + 1475 - 1) // 1475
        print(f"🔧 Fragmentando mensaje en {total_fragmentos} partes")

        # Fragmentar el mensaje
        while offset < longitud:
            chunk = mensaj_bytes[offset:offset + 1475]
            offset += 1475

            frame = Frame(
                destino=mac_destino,
                origen=self.mac_ori,
                tipo_mensaje=tipo_mensaje,
                id=id_mensaje,
                fragment_num=numero_fragmento,
                total=total_fragmentos,
                Datos=chunk
            )
            frame_bytes = frame.hacia_bytes()
            frames.append(frame_bytes)
            numero_fragmento += 1

        return frames
    
    def decodificar_frame(self, frame_: bytes): #decodificar un frame recibido       
        try:
            frame = Frame.desde_bytes(frame_)
            print(f"🔧 Frame decodificado: Destino={frame.mac_destino}, Origen={frame.mac_origen}, Tipo={frame.tipo_mensaje}")
        except ValueError as e:
            print(f"Error parsing frame: {e}")
            return None
        
        if not frame.verificar_crc(frame_):
            print("Error: CRC no coincide, descartando frame")  
            return None
        
        #verificar si es pa mi
        mac_propia = self.mac_ori.upper()
        mac_destino_frame = frame.mac_destino.upper()

        if mac_destino_frame != mac_propia and mac_destino_frame != "FF:FF:FF:FF:FF:FF":
            return None
        
         # Verificar si es un fragmento
        if frame.total_fragmentos > 1:
            print(f"🔧 Frame fragmentado detectado: {frame.fragmento}/{frame.total_fragmentos}")
            return self._procesar_fragmento(frame)

        if frame.tipo_mensaje == Tipo_Mensaje.archivo:
            return self.process_complete_frame(frame)
        elif frame.tipo_mensaje == Tipo_Mensaje.texto:
            if frame.total_fragmentos == 0 and frame.fragmento == 0:
                return self.process_complete_frame(frame)
        return None
        
    def process_complete_frame(self, frame: Frame) -> Frame: #procesar un frame completo
        if frame.tipo_mensaje == Tipo_Mensaje.texto:    
            try:
                frame.datos = frame.datos.decode('utf-8')
            except Exception:
                print("Error decodificando payload de texto")
        elif frame.tipo_mensaje == Tipo_Mensaje.archivo:
            try:
                print(f"🔧 Procesando frame de archivo: {frame}")
                print(f"📊 Datos recibidos: {frame.datos[:100] if frame.datos else 'VACIO'}")
                
                if not frame.datos and hasattr(frame, 'nombre_archivo') and frame.nombre_archivo:
                    print("⚠️  Datos vacíos, usando nombre_archivo como datos")
                    
                    if frame.nombre_archivo.startswith(('FILE_METADATA:', 'FILE_CHUNK:', 'FILE_END:')):
                        return frame
                
                # Procesamiento archivos no fragmentados
                if frame.datos and len(frame.datos) >= 2:
                    try:
                        # Intentar extraer nombre y datos según el formato esperado
                        largo_nombre = int.from_bytes(frame.datos[0:2], 'big')
                        if len(frame.datos) >= 2 + largo_nombre:
                            nombre_archivo = frame.datos[2:2+largo_nombre].decode('utf-8')
                            datos_archivo = frame.datos[2+largo_nombre:]
                            
                            frame.nombre_archivo = nombre_archivo
                            frame.datos = datos_archivo
                            
                            print(f"✅ Archivo procesado: {nombre_archivo}, {len(datos_archivo)} bytes")
                            return frame
                    except Exception as e:
                        print(f"❌ Error procesando estructura de archivo: {e}")
                
                return frame
                
            except Exception as e:
                print(f"❌ Error en process_file_frame: {e}")
        return frame
                
                    
    def _procesar_fragmento(self, frame: Frame):
        try:
            #Procesa un fragmento de mensaje y reensambla cuando está completo
            print(f"🔧 _procesar_fragmento: Fragmento {frame.fragmento}/{frame.total_fragmentos}")
            print(f"🔧 _procesar_fragmento: ID mensaje: {frame.id_mensaje}")
            print(f"🔧 _procesar_fragmento: MAC origen: {frame.mac_origen}")
            print(f"🔧 _procesar_fragmento: Tamaño datos: {len(frame.datos)} bytes")
            
            if frame.datos is None or len(frame.datos) == 0:
                print(f"❌ _procesar_fragmento: Fragmento {frame.fragmento} tiene datos vacíos")
                return None
            
            if frame.total_fragmentos == 0:
                total_real = frame.fragmento + 1
            else:
                total_real = frame.total_fragmentos
            
            print(f"🔧 Total real de fragmentos: {total_real}")

            mensaje_completo = self.fragment_manager.agregar_fragmento(
                frame.id_mensaje,
                frame.fragmento, 
                total_real,
                frame.datos,
                frame.mac_origen
            )
            
            if mensaje_completo is not None:
                print(f"🎉 MENSAJE COMPLETO REENSAMBLADO: {len(mensaje_completo)} bytes")
                
                # Crear un nuevo frame con el mensaje completo
                frame_completo = Frame(
                    destino=frame.mac_destino,
                    origen=frame.mac_origen,
                    tipo_mensaje=frame.tipo_mensaje,
                    id=frame.id_mensaje,
                    fragment_num=0,
                    total=0,
                    Datos=mensaje_completo
                )
                
                return self.process_complete_frame(frame_completo)
            else:
                # Aún faltan fragmentos
                estado = self.fragment_manager.obtener_estado_ensamblaje()
                print(f"📦 Esperando más fragmentos... ({estado['mensajes_pendientes']} mensajes pendientes)")
                return None
                    
        except Exception as e:
            print(f"❌ Error procesando fragmento: {e}")
            import traceback
            traceback.print_exc()
            return None

    def stop(self):
        self.ejecutando = False
        if self.mi_socket:
            self.mi_socket.close()
            print("🔌 Socket cerrado")

    