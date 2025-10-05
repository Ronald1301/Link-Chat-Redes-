import time
import struct
import hashlib
from threading import Lock
from typing import Dict, List, Tuple, Optional

class FragmentManager:
    def __init__(self):
        self.fragmentos_pendientes: Dict[str, Dict] = {}
        self.timeout = 30 
        self.lock = Lock()  
        
    def agregar_fragmento(self, id_mensaje: int, num_fragmento: int, total_fragmentos: int, 
                          datos: bytes, mac_origen: str) -> Optional[bytes]:
        #Agrega un fragmento y devuelve el mensaje completo si está listo
        with self.lock:
            clave = f"{mac_origen}_{id_mensaje}"
        
            if clave not in self.fragmentos_pendientes:
                self.fragmentos_pendientes[clave] = {
                    'total_fragmentos': total_fragmentos,
                    'fragmentos_recibidos': {},
                    'timestamp': time.time(),
                    'mac_origen': mac_origen,
                    'id_mensaje': id_mensaje,
                    'bytes_totales': 0,
                    'fragmentos_esperados': set(range(total_fragmentos)) 
                }
                print(f"🔧 FragmentManager: Nuevo mensaje {clave} con {total_fragmentos} fragmentos")
            
            mensaje = self.fragmentos_pendientes[clave]
            
            if total_fragmentos > mensaje['total_fragmentos']:
                print(f"🔧 FragmentManager: Actualizando total de {mensaje['total_fragmentos']} a {total_fragmentos}")
                mensaje['total_fragmentos'] = total_fragmentos
                mensaje['fragmentos_esperados'] = set(range(total_fragmentos))
            
            if num_fragmento not in mensaje['fragmentos_recibidos']:
                mensaje['fragmentos_recibidos'][num_fragmento] = datos
                mensaje['bytes_totales'] += len(datos)
                mensaje['timestamp'] = time.time()
                print(f"🔧 FragmentManager: Fragmento {num_fragmento} almacenado")
            else:
                print(f"⚠️  FragmentManager: Fragmento {num_fragmento} ya estaba almacenado")
            
            fragmentos_recibidos = set(mensaje['fragmentos_recibidos'].keys())
            fragmentos_faltantes = mensaje['fragmentos_esperados'] - fragmentos_recibidos
            
            print(f"🔧 FragmentManager: Fragmentos recibidos: {len(fragmentos_recibidos)}/{mensaje['total_fragmentos']}")
            print(f"🔧 FragmentManager: Fragmentos faltantes: {sorted(fragmentos_faltantes)}")
            
            if not fragmentos_faltantes:
                print(f"🎉 FragmentManager: TODOS los fragmentos recibidos para {clave}")
                
                try:
                    # Reensamblar en orden
                    fragmentos_ordenados = []
                    for i in range(mensaje['total_fragmentos']):
                        fragmentos_ordenados.append(mensaje['fragmentos_recibidos'][i])
                    
                    mensaje_completo = b''.join(fragmentos_ordenados)
                    print(f"🎉 FragmentManager: Mensaje reensamblado - {len(mensaje_completo)} bytes")
                    
                    # Limpiar
                    del self.fragmentos_pendientes[clave]
                    return mensaje_completo
                    
                except Exception as e:
                    print(f"❌ FragmentManager: Error reensamblando mensaje: {e}")
                    import traceback
                    traceback.print_exc()
                    del self.fragmentos_pendientes[clave]
                    return None
            else:
                # Mostrar progreso detallado
                progreso = len(fragmentos_recibidos) / mensaje['total_fragmentos'] * 100
                print(f"📊 FragmentManager: Progreso: {progreso:.1f}% ({len(fragmentos_recibidos)}/{mensaje['total_fragmentos']})")
            
            # Limpiar mensajes antiguos
            self._limpiar_antiguos()
        
            return None
    
    def _limpiar_antiguos(self): #Elimina mensajes fragmentados antiguos
        ahora = time.time()
        claves_a_eliminar = []
        
        for clave, mensaje in self.fragmentos_pendientes.items():
            if ahora - mensaje['timestamp'] > self.timeout:
                claves_a_eliminar.append(clave)
                fragmentos_recibidos = len(mensaje['fragmentos_recibidos'])
                print(f"⏰ FragmentManager: Timeout para {clave} - {fragmentos_recibidos}/{mensaje['total_fragmentos']} fragmentos")
        
        for clave in claves_a_eliminar:
            del self.fragmentos_pendientes[clave]
    
    def obtener_estado_ensamblaje(self): #Retorna estadísticas de ensamblaje
        with self.lock:
            total_mensajes = len(self.fragmentos_pendientes)
            total_fragmentos_esperados = sum(msg['total_fragmentos'] for msg in self.fragmentos_pendientes.values())
            fragmentos_recibidos = sum(len(msg['fragmentos_recibidos']) for msg in self.fragmentos_pendientes.values())
            
            return {
                'mensajes_pendientes': total_mensajes,
                'fragmentos_totales': total_fragmentos_esperados,
                'fragmentos_recibidos': fragmentos_recibidos
            }