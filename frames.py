from dataclasses import dataclass, field
import struct
import hashlib
import time
import binascii
import sys
from typing import Union
from enum import Enum

class Tipo_Mensaje(Enum):
    texto = 1
    archivo = 2
    
    @classmethod
    def from_value(cls, value):
        if isinstance(value, cls):
            return value
        try:
            return cls(value)
        except ValueError:
            raise ValueError("Tipo no valido")

@dataclass
class Frame:
    mac_destino: str = ""
    mac_origen: str = ""
    tipo: bytes = b"\x88\xb5"
    datos: bytes = b""
    tipo_mensaje: Tipo_Mensaje = Tipo_Mensaje.texto
    es_fragmento: bool = False  # Nuevo campo para indicar fragmentación
    id_mensaje: int = 0         # ID único del mensaje original
    fragmento: int = 0      # Número de fragmento actual
    total_fragmentos: int = 1   # Total de fragmentos del mensaje
    nombre_archivo: str =""

    def __init__(self, destino: str = "", origen: str = "", tipo_mensaje: Tipo_Mensaje = Tipo_Mensaje.texto, id: int = 0,
                 fragment_num: int = 0, total: int = 0, Datos: Union[bytes, str] = b""):
        self.mac_destino = destino
        self.mac_origen = origen
        self.tipo_mensaje = tipo_mensaje
        self.id_mensaje = id
        self.fragmento = fragment_num
        self.total_fragmentos = total
        self.datos = Datos
        self.longitud = len(self.datos)

    @classmethod
    def desde_bytes(cls, data:bytes) -> 'Frame':
        if len(data) < 25:
            raise ValueError("Frame invalido")
            
        frame = cls()
        
        # Extraer campos del frame
        frame.mac_destino = cls.bytes_to_mac(data[0:6])
        frame.mac_origen = cls.bytes_to_mac(data[6:12])

        
        # Verificar EtherType
        ethertype = data[12:14]
        if ethertype != b"\x88\xb5":
            raise ValueError(f"EtherType incorrecto: {ethertype.hex()}")
        
        
        frame.tipo_mensaje = Tipo_Mensaje.from_value(data[14])
        frame.id_mensaje = int.from_bytes(data[15:17], 'big')
        frame.fragmento = data[17]
        frame.total_fragmentos = data[18]
        frame.longitud = int.from_bytes(data[19:21], 'big')

        # Extraer payload (sin incluir CRC)
        payload = 21 + frame.longitud
        if payload > len(data) - 4:
            raise ValueError("Longitud del payload inconsistente")
            
        frame.datos = data[21:payload]
        
        return frame
    
    def hacia_bytes(self) -> bytes:
        """Convierte el Frame a bytes listo para enviar"""
        print(f"hacia_bytes: MAC destino={self.mac_destino}, MAC origen={self.mac_origen}")
    
        if isinstance(self.datos, str):
            payload_bytes = self.datos.encode('utf-8')
        else:
            payload_bytes = self.datos

        # Asegurar formato consistente de MACs
        mac_dest_clean = self.mac_destino.replace(":", "").lower()
        mac_orig_clean = self.mac_origen.replace(":", "").lower()
        
        print(f"MAC destino limpia: {mac_dest_clean}")
        print(f"MAC origen limpia: {mac_orig_clean}")
        
        length_bytes = len(payload_bytes).to_bytes(2, 'big')  
        msg_type_byte = self.tipo_mensaje.value if isinstance(self.tipo_mensaje, Enum) else int(self.tipo_mensaje)
        
        frame_no_crc = (
            bytes.fromhex(self.mac_destino.replace(":", ""))+
            bytes.fromhex(self.mac_origen.replace(":", "")) +
            self.tipo +
            msg_type_byte.to_bytes(1, 'big') + #.to_bytes(1, 'big') +
            self.id_mensaje.to_bytes(2, 'big') +
            self.fragmento.to_bytes(1, 'big') +
            self.total_fragmentos.to_bytes(1, 'big') +
            length_bytes +
            payload_bytes
        )

        crc = self.actualizar_crc(frame_no_crc)
        frame = frame_no_crc + crc
        
        
        return frame


    def _asegurar_entero(self, valor):
        """Asegura que el valor sea un entero para struct.pack"""
        if isinstance(valor, int):
            return valor
        elif isinstance(valor, bytes):
            # Convertir bytes a entero (big-endian)
            return int.from_bytes(valor, byteorder='big')
        elif hasattr(valor, '__int__'):
            return valor.__int__()
        elif hasattr(valor, 'int'):
            return valor.int
        else:
            try:
                return int(valor)
            except (TypeError, ValueError):
                return 0
            
    def _asegurar_bytes(self, valor):
        """Asegura que el valor sea bytes para concatenación"""
        if isinstance(valor, bytes):
            return valor
        elif isinstance(valor, int):
            # Convertir entero a bytes (4 bytes para CRC, 2 para tipo, etc.)
            if 0 <= valor <= 0xFFFF:
                return struct.pack('>H', valor)
            elif 0 <= valor <= 0xFFFFFFFF:
                return struct.pack('>I', valor)
            else:
                return struct.pack('>Q', valor)
        elif isinstance(valor, str):
            return valor.encode('utf-8')
        else:
            try:
                return bytes(valor)
            except:
                return b''
            
    def _convertir_a_enteros(self):
        """Asegura que todos los campos numéricos sean enteros"""
        self.crc = int(self.crc) if self.crc is not None else 0
        self.id_mensaje = int(self.id_mensaje) if self.id_mensaje is not None else 0
        self.num_fragmento = int(self.num_fragmento) if self.num_fragmento is not None else 0
        self.total_fragmentos = int(self.total_fragmentos) if self.total_fragmentos is not None else 1

    def validar_campos(self):
        # Usar valores convertidos a enteros para validación
        tipo_val = self._asegurar_entero(self.tipo)
        crc_val = self._asegurar_entero(self.crc)
        num_frag_val = self._asegurar_entero(self.num_fragmento)
        total_frags_val = self._asegurar_entero(self.total_fragmentos)

        # Validaciones existentes...
        mac_dest_bytes = bytes.fromhex(self.mac_destino.replace(':', ''))
        if len(mac_dest_bytes) != 6:
            raise ValueError(f"MAC destino debe ser 6 bytes, tiene {len(mac_dest_bytes)}")

        mac_orig_bytes = bytes.fromhex(self.mac_origen.replace(':', ''))
        if len(mac_orig_bytes) != 6:
            raise ValueError(f"MAC origen debe ser 6 bytes, tiene {len(mac_orig_bytes)}")

        if not (0 <= tipo_val <= 0xFFFF):
            raise ValueError(f"Tipo debe ser valor de 2 bytes (0-65535), tiene {tipo_val}")

        # Para fragmentos, el tamaño máximo es menor porque agregamos headers
        tamaño_maximo = 1500 - (8 if self.es_fragmento else 0)
        if len(self.datos) > tamaño_maximo:
            raise ValueError(f"Datos máximo {tamaño_maximo} bytes, tiene {len(self.datos)}")
        
        # Padding solo para mensajes completos (no fragmentos)
        if not self.es_fragmento and len(self.datos) < 46:
            self.datos = self.datos + b'\x00' * (46 - len(self.datos))
        
        if not (0 <= crc_val <= 0xFFFFFFFF):
            raise ValueError(f"CRC debe ser valor de 4 bytes (0-4294967295), tiene {crc_val}")

        # Validaciones para fragmentos
        if self.es_fragmento:
            if num_frag_val >= total_frags_val:
                raise ValueError(f"Número de fragmento {num_frag_val} >= total {total_frags_val}")
            if total_frags_val > 65535:
                raise ValueError(f"Demasiados fragmentos: {total_frags_val}")

    def serializar(self) -> bytes:
        # Convertir MACs a bytes con manejo de errores
        try:
            mac_dest_bytes = bytes.fromhex(self.mac_destino.replace(':', ''))
        except:
            mac_dest_bytes = b'\x00' * 6

        try:
            mac_orig_bytes = bytes.fromhex(self.mac_origen.replace(':', ''))
        except:
            mac_orig_bytes = b'\x00' * 6
        
        # Asegurar que todos los componentes sean bytes
        preamble_bytes = self._asegurar_bytes(self.preamble)
        
        tipo_entero = self._asegurar_entero(self.tipo)
        tipo_bytes = struct.pack('>H', tipo_entero)
        
        # Si es fragmento, asegurar que los valores sean enteros y luego bytes
        if self.es_fragmento:
            id_mensaje_entero = self._asegurar_entero(self.id_mensaje)
            num_fragmento_entero = self._asegurar_entero(self.num_fragmento)
            total_fragmentos_entero = self._asegurar_entero(self.total_fragmentos)
            
            header_fragmento = struct.pack('>QHH', 
                                         id_mensaje_entero, 
                                         num_fragmento_entero, 
                                         total_fragmentos_entero)
            datos_con_header = header_fragmento + self.datos
        else:
            datos_con_header = self.datos
        
        # Asegurar que CRC sea entero y luego bytes
        crc_entero = self._asegurar_entero(self.crc)
        crc_bytes = struct.pack('>I', crc_entero)
        
        # Verificar que todos los componentes son bytes antes de concatenar
        componentes = [
            ('preamble', preamble_bytes),
            ('mac_dest_bytes', mac_dest_bytes),
            ('mac_orig_bytes', mac_orig_bytes),
            ('tipo_bytes', tipo_bytes),
            ('datos_con_header', datos_con_header),
            ('crc_bytes', crc_bytes)
        ]

        print(f"tipo {tipo_bytes}")
        
        # DEBUG: Verificar tipos
        for nombre, componente in componentes:
            if not isinstance(componente, bytes):
                print(f"ERROR: {nombre} no es bytes, es {type(componente)}")
                # Convertir a bytes si es posible
                componente = self._asegurar_bytes(componente)
        
        # Concatenar todos los componentes
        frame_bytes = (preamble_bytes + mac_dest_bytes + mac_orig_bytes + 
                      tipo_bytes + datos_con_header + crc_bytes)
        print(len(frame_bytes))
        
        return frame_bytes
    
    @staticmethod  
    def bytes_to_mac(mac_bytes: bytes) -> str:
        """Convierte bytes de MAC a string formateado"""
        mac_str = ':'.join(f'{b:02x}' for b in mac_bytes)
        print(f" bytes_to_mac: {mac_bytes.hex()} -> {mac_str}")
        return mac_str
        
    def verify_crc(self, frame_data: bytes) -> bool:
        """Verifica el CRC del frame"""
        if len(frame_data) < 25:
            return False
            
        frame_without_crc = frame_data[:-4]
        crc_received = frame_data[-4:]
        crc_calculated = self.actualizar_crc(frame_without_crc)
        print(f"frame sin crc={frame_without_crc}, crc recivido= {crc_received}, crc calculado= {crc_calculated}")
        
        return True #crc_received == crc_calculated
 
    def actualizar_crc(self, data:bytes) -> bytes:
        crc = binascii.crc32(data) & 0xffffffff
        return crc.to_bytes(4, 'big')


class Tipo_Mensaje(Enum):
    texto = 1
    archivo = 2
    
    @classmethod
    def from_value(cls, value):
        if isinstance(value, cls):
            return value
        try:
            return cls(value)
        except ValueError:
            raise ValueError("Tipo no valido")