from dataclasses import dataclass, field
import struct
import hashlib
import time

@dataclass
class Frame:
    preamble: bytes = field(default=b'\xAA' * 7 + b'\xAB')
    mac_destino: str = ""
    mac_origen: str = ""
    tipo: int = 0
    datos: bytes = b""
    crc: int = 0
    es_fragmento: bool = False  # Nuevo campo para indicar fragmentación
    id_mensaje: int = 0         # ID único del mensaje original
    num_fragmento: int = 0      # Número de fragmento actual
    total_fragmentos: int = 1   # Total de fragmentos del mensaje

    def __post_init__(self):
        self.validar_campos()

    def validar_campos(self):
        # Validaciones existentes...
        mac_dest_bytes = bytes.fromhex(self.mac_destino.replace(':', ''))
        if len(mac_dest_bytes) != 6:
            raise ValueError(f"MAC destino debe ser 6 bytes, tiene {len(mac_dest_bytes)}")

        mac_orig_bytes = bytes.fromhex(self.mac_origen.replace(':', ''))
        if len(mac_orig_bytes) != 6:
            raise ValueError(f"MAC origen debe ser 6 bytes, tiene {len(mac_orig_bytes)}")

        if not (0 <= self.tipo <= 0xFFFF):
            raise ValueError(f"Tipo debe ser valor de 2 bytes (0-65535), tiene {self.tipo}")

        # Para fragmentos, el tamaño máximo es menor porque agregamos headers
        tamaño_maximo = 1500 - (8 if self.es_fragmento else 0)
        if len(self.datos) > tamaño_maximo:
            raise ValueError(f"Datos máximo {tamaño_maximo} bytes, tiene {len(self.datos)}")
        
        # Padding solo para mensajes completos (no fragmentos)
        if not self.es_fragmento and len(self.datos) < 46:
            self.datos = self.datos + b'\x00' * (46 - len(self.datos))
        
        if not (0 <= self.crc <= 0xFFFFFFFF):
            raise ValueError(f"CRC debe ser valor de 4 bytes (0-4294967295), tiene {self.crc}")

        # Validaciones para fragmentos
        if self.es_fragmento:
            if self.num_fragmento >= self.total_fragmentos:
                raise ValueError(f"Número de fragmento {self.num_fragmento} >= total {self.total_fragmentos}")
            if self.total_fragmentos > 65535:
                raise ValueError(f"Demasiados fragmentos: {self.total_fragmentos}")

    def serializar(self) -> bytes:
        # Convertir MACs a bytes
        mac_dest_bytes = bytes.fromhex(self.mac_destino.replace(':', ''))
        mac_orig_bytes = bytes.fromhex(self.mac_origen.replace(':', ''))
        
        # Convertir tipo a 2 bytes (big-endian)
        tipo_bytes = struct.pack('>H', self.tipo)
        
        # Si es fragmento, agregar headers de fragmentación antes de los datos
        if self.es_fragmento:
            header_fragmento = struct.pack('>QHH', 
                                         self.id_mensaje, 
                                         self.num_fragmento, 
                                         self.total_fragmentos)
            datos_con_header = header_fragmento + self.datos
        else:
            datos_con_header = self.datos
        
        # Convertir CRC a 4 bytes (big-endian)
        crc_bytes = struct.pack('>I', self.crc)
        
        # Concatenar todos los componentes
        frame_bytes = (self.preamble + mac_dest_bytes + mac_orig_bytes + 
                      tipo_bytes + datos_con_header + crc_bytes)
        
        return frame_bytes
    
    @classmethod
    def desde_bytes(cls, datos: bytes) -> 'Frame':
        if len(datos) < 72:  # Mínimo para frame sin fragmentación
            raise ValueError(f"Frame demasiado pequeño: {len(datos)} bytes")
        
        # Extraer componentes básicos
        preamble = datos[0:8]
        mac_dest_bytes = datos[8:14]
        mac_orig_bytes = datos[14:20]
        tipo = struct.unpack('>H', datos[20:22])[0]
        
        mac_destino = ':'.join(f'{b:02x}' for b in mac_dest_bytes)
        mac_origen = ':'.join(f'{b:02x}' for b in mac_orig_bytes)
        
        # Determinar si es fragmento (basado en el tipo o en la estructura)
        # Asumimos que si después del tipo hay 8 bytes que parecen un header de fragmento, es fragmento
        es_fragmento = False
        id_mensaje = 0
        num_fragmento = 0
        total_fragmentos = 1
        
        # Los datos comienzan en el byte 22, pero si es fragmento, los primeros 8 bytes son header
        try:
            if len(datos) >= 30:  # Suficiente para tener header de fragmento
                # Intentar leer header de fragmento
                id_mensaje, num_fragmento, total_fragmentos = struct.unpack('>QHH', datos[22:34])
                es_fragmento = True
                datos_payload = datos[34:-4]  # Saltar header de fragmento
            else:
                datos_payload = datos[22:-4]  # Datos normales
        except:
            # Si falla la deserialización, no es fragmento
            datos_payload = datos[22:-4]
        
        # CRC (últimos 4 bytes)
        crc = struct.unpack('>I', datos[-4:])[0]
        
        return cls(
            preamble=preamble,
            mac_destino=mac_destino,
            mac_origen=mac_origen,
            tipo=tipo,
            datos=datos_payload,
            crc=crc,
            es_fragmento=es_fragmento,
            id_mensaje=id_mensaje,
            num_fragmento=num_fragmento,
            total_fragmentos=total_fragmentos
        )
    
    def calcular_crc(self) -> int:
        # Incluir todos los campos en el cálculo del CRC para mayor robustez
        data = (self.mac_destino.encode() + self.mac_origen.encode() + 
                struct.pack('>H', self.tipo) + self.datos)
        
        if self.es_fragmento:
            data += struct.pack('>QHH', self.id_mensaje, self.num_fragmento, self.total_fragmentos)
        
        checksum = sum(data) & 0xFFFFFFFF
        return checksum

    def actualizar_crc(self):
        self.crc = self.calcular_crc()

    def __str__(self) -> str:
        base = f"Frame(MAC_Dest: {self.mac_destino}, MAC_Orig: {self.mac_origen}, Tipo: 0x{self.tipo:04x}"
        if self.es_fragmento:
            base += f", Fragmento {self.num_fragmento+1}/{self.total_fragmentos} (ID: {self.id_mensaje})"
        base += f", Datos: {len(self.datos)} bytes, CRC: 0x{self.crc:08x})"
        return base

    @property
    def tamaño_total(self) -> int:
        tamaño_base = 26  # Cabecera Ethernet básica
        if self.es_fragmento:
            tamaño_base += 8  # Header de fragmentación
        return tamaño_base + len(self.datos)