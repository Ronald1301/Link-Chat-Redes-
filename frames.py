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
    fragmento: int = 0          # Número de fragmento actual
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
        frame.mac_destino = cls.de_bytes_a_mac(data[0:6])
        frame.mac_origen = cls.de_bytes_a_mac(data[6:12])

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
    
    def hacia_bytes(self) -> bytes: #convertir el frame a bytes
        print(f"🔍 hacia_bytes: MAC destino={self.mac_destino}, MAC origen={self.mac_origen}")
    
        if isinstance(self.datos, str):
            payload_bytes = self.datos.encode('utf-8')
        else:
            payload_bytes = self.datos

        length_bytes = len(payload_bytes).to_bytes(2, 'big')  
        msg_type_byte = self.tipo_mensaje.value if isinstance(self.tipo_mensaje, Enum) else int(self.tipo_mensaje)
        
        frame_no_crc = (
            bytes.fromhex(self.mac_destino.replace(":", ""))+
            bytes.fromhex(self.mac_origen.replace(":", "")) +
            self.tipo +
            msg_type_byte.to_bytes(1, 'big') + 
            self.id_mensaje.to_bytes(2, 'big') +
            self.fragmento.to_bytes(1, 'big') +
            self.total_fragmentos.to_bytes(1, 'big') +
            length_bytes +
            payload_bytes
        )

        crc = self.calcular_crc(frame_no_crc)
        frame = frame_no_crc + crc
    
        return frame

    @staticmethod  
    def de_bytes_a_mac(mac_bytes: bytes) -> str: #convierte bytes a mac en string
        mac_str = ':'.join(f'{b:02x}' for b in mac_bytes)
        print(f"🔍 bytes_to_mac: {mac_bytes.hex()} -> {mac_str}")
        return mac_str
        
    def verificar_crc(self, frame_data: bytes) -> bool: #verificar crc del frame
        if len(frame_data) < 25:
            return False
            
        frame_without_crc = frame_data[:-4]
        crc_received = frame_data[-4:]
        crc_calculated = self.calcular_crc(frame_without_crc)
        print(f"frame sin crc={frame_without_crc}, crc recivido= {crc_received}, crc calculado= {crc_calculated}")
        
        return crc_received == crc_calculated

    def calcular_crc(self, data:bytes) -> bytes:
        crc = binascii.crc32(data) & 0xffffffff
        return crc.to_bytes(4, 'big')
