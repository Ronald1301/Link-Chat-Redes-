import time
import struct
import hashlib
from threading import Lock
from typing import Dict, List, Tuple, Optional

class FragmentManager:
    """
    Gestiona la fragmentación y reensamblaje de mensajes largos
    """
    
    def __init__(self, tiempo_espera_fragmentos: int = 30):
        """
        Args:
            tiempo_espera_fragmentos: Segundos a esperar por fragmentos faltantes antes de descartar
        """
        self.tiempo_espera = tiempo_espera_fragmentos
        self.mensajes_ensamblaje: Dict[int, Dict] = {}  # id_mensaje -> info de ensamblaje
        self.lock = Lock()
        self.ultimo_id_mensaje = int(time.time() * 1000) % (2**32)
        
    def generar_id_mensaje(self) -> int:
        """Genera un ID único para un mensaje"""
        with self.lock:
            self.ultimo_id_mensaje = (self.ultimo_id_mensaje + 1) % (2**32)
            return self.ultimo_id_mensaje
    
    def fragmentar_mensaje(self, datos: bytes, tamaño_maximo_fragmento: int = 1400) -> List[Tuple[bytes, int, int, int]]:
        """
        Fragmenta un mensaje en partes más pequeñas
        
        Args:
            datos: Datos a fragmentar
            tamaño_maximo_fragmento: Tamaño máximo por fragmento (1492 = 1500 - 8 headers)
            
        Returns:
            Lista de tuplas (datos_fragmento, id_mensaje, num_fragmento, total_fragmentos)
        """
        if len(datos) <= tamaño_maximo_fragmento:
            # No necesita fragmentación
            return [(datos, self.generar_id_mensaje(), 0, 1)]
        
        id_mensaje = self.generar_id_mensaje()
        total_fragmentos = (len(datos) + tamaño_maximo_fragmento - 1) // tamaño_maximo_fragmento
        
        if total_fragmentos > 65535:
            raise ValueError(f"Mensaje demasiado grande: {len(datos)} bytes requiere {total_fragmentos} fragmentos")
        
        fragmentos = []
        for i in range(total_fragmentos):
            inicio = i * tamaño_maximo_fragmento
            fin = min(inicio + tamaño_maximo_fragmento, len(datos))
            fragmento_datos = datos[inicio:fin]
            
            fragmentos.append((fragmento_datos, id_mensaje, i, total_fragmentos))
        
        return fragmentos
    
    def agregar_fragmento(self, id_mensaje: int, num_fragmento: int, total_fragmentos: int, 
                         datos: bytes, mac_origen: str) -> Optional[bytes]:
        """
        Agrega un fragmento recibido y verifica si el mensaje está completo
        
        Returns:
            Mensaje completo si todos los fragmentos fueron recibidos, None si faltan
        """
        with self.lock:
            # Limpiar mensajes expirados primero
            self._limpiar_expirados()
            
            clave = id_mensaje
            if clave not in self.mensajes_ensamblaje:
                # Nuevo mensaje
                self.mensajes_ensamblaje[clave] = {
                    'fragmentos_recibidos': [None] * total_fragmentos,
                    'total_fragmentos': total_fragmentos,
                    'timestamp': time.time(),
                    'mac_origen': mac_origen,
                    'fragmentos_recibidos_count': 0
                }
            
            info = self.mensajes_ensamblaje[clave]
            
            # Verificar que el número de fragmento sea válido
            if num_fragmento >= info['total_fragmentos']:
                print(f"Error: Fragmento {num_fragmento} fuera de rango (total: {info['total_fragmentos']})")
                return None
            
            # Si ya teníamos este fragmento, ignorar
            if info['fragmentos_recibidos'][num_fragmento] is None:
                info['fragmentos_recibidos'][num_fragmento] = datos
                info['fragmentos_recibidos_count'] += 1
            
            # Verificar si tenemos todos los fragmentos
            if info['fragmentos_recibidos_count'] == info['total_fragmentos']:
                # Reensamblar mensaje
                mensaje_completo = b''.join(info['fragmentos_recibidos'])
                del self.mensajes_ensamblaje[clave]
                return mensaje_completo
            
            return None
    
    def _limpiar_expirados(self):
        """Elimina mensajes que han estado esperando fragmentos por demasiado tiempo"""
        ahora = time.time()
        expirados = []
        
        for id_msg, info in self.mensajes_ensamblaje.items():
            if ahora - info['timestamp'] > self.tiempo_espera:
                expirados.append(id_msg)
                print(f"Descartando mensaje {id_msg} por timeout ({info['fragmentos_recibidos_count']}/{info['total_fragmentos']} fragmentos)")
        
        for id_msg in expirados:
            del self.mensajes_ensamblaje[id_msg]
    
    def obtener_estado_ensamblaje(self) -> Dict[str, int]:
        """Retorna estadísticas de ensamblaje"""
        with self.lock:
            return {
                'mensajes_pendientes': len(self.mensajes_ensamblaje),
                'fragmentos_faltantes': sum(
                    info['total_fragmentos'] - info['fragmentos_recibidos_count'] 
                    for info in self.mensajes_ensamblaje.values()
                )
            }