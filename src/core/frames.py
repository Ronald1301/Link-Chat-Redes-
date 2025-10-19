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
    nombre_archivo: str = ""
    preamble: bytes = b"\x55\x55\x55\x55\x55\x55\x55\xd5"  # Preamble estándar Ethernet
    crc: int = 0            # Campo para CRC

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
        if len(data) < 29:  # Aumentado por campos más grandes
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
        frame.fragmento = int.from_bytes(data[17:21], 'big')  # Expandido a 4 bytes (0-4 billones)
        frame.total_fragmentos = int.from_bytes(data[21:25], 'big')  # Expandido a 4 bytes
        frame.longitud = int.from_bytes(data[25:27], 'big')

        # Extraer payload (sin incluir CRC) - ajustado por nuevos campos
        payload = 27 + frame.longitud  # Ajustado por los campos expandidos
        if payload > len(data) - 4:
            raise ValueError("Longitud del payload inconsistente")
            
        frame.datos = data[27:payload]
        
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
        
        # Verificar que los valores no excedan los límites
        if self.fragmento > 0xFFFFFFFF:  # 4 bytes máximo
            raise ValueError(f"Número de fragmento demasiado grande: {self.fragmento}")
        if self.total_fragmentos > 0xFFFFFFFF:  # 4 bytes máximo  
            raise ValueError(f"Total de fragmentos demasiado grande: {self.total_fragmentos}")
            
        frame_no_crc = (
            bytes.fromhex(self.mac_destino.replace(":", ""))+
            bytes.fromhex(self.mac_origen.replace(":", "")) +
            self.tipo +
            msg_type_byte.to_bytes(1, 'big') + #.to_bytes(1, 'big') +
            self.id_mensaje.to_bytes(2, 'big') +
            self.fragmento.to_bytes(4, 'big') +  # Expandido a 4 bytes
            self.total_fragmentos.to_bytes(4, 'big') +  # Expandido a 4 bytes
            length_bytes +
            payload_bytes
        )

        crc = self.actualizar_crc(frame_no_crc)
        frame = frame_no_crc + crc
        
        
        return frame
            
    @staticmethod  
    def bytes_to_mac(mac_bytes: bytes) -> str:
        """Convierte bytes de MAC a string formateado"""
        mac_str = ':'.join(f'{b:02x}' for b in mac_bytes)
        print(f" bytes_to_mac: {mac_bytes.hex()} -> {mac_str}")
        return mac_str
        
    def verify_crc(self, frame_data: bytes) -> bool:
        """Verifica el CRC del frame"""
        if len(frame_data) < 29:  # Actualizado por campos más grandes
            return False
            
        frame_without_crc = frame_data[:-4]
        crc_received = frame_data[-4:]
        crc_calculated = self.actualizar_crc(frame_without_crc)
        print(f"frame sin crc={frame_without_crc}, crc recivido= {crc_received}, crc calculado= {crc_calculated}")
        
        return True #crc_received == crc_calculated
 
    def actualizar_crc(self, data:bytes) -> bytes:
        crc = binascii.crc32(data) & 0xffffffff
        return crc.to_bytes(4, 'big')