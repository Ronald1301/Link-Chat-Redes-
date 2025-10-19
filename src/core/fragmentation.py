import time
import struct
import hashlib
from threading import Lock
from typing import Dict, List, Tuple, Optional

class FragmentManager:
    def __init__(self, progress_callback=None):
        self.fragmentos_pendientes: Dict[str, Dict] = {}
        self.timeout = 1800  # 30 minutos para archivos grandes
        self.lock = Lock()  # Para thread safety
        self.progress_callback = progress_callback  # Callback para mostrar progreso
        
    def agregar_fragmento(self, id_mensaje: int, num_fragmento: int, total_fragmentos: int, datos: bytes, mac_origen: str) -> Optional[bytes]:
        #Agrega un fragmento y devuelve el mensaje completo si está listo
        with self.lock:
            clave = f"{mac_origen}_{id_mensaje}"
            
            print(f"🔧 FragmentManager: Agregando fragmento {num_fragmento} (total: {total_fragmentos})")
            print(f"🔧 FragmentManager: Clave: {clave}")
            print(f"🔧 FragmentManager: Tamaño datos: {len(datos)} bytes")
            
            if clave not in self.fragmentos_pendientes:
                # NUEVO: Inicializar con diccionario para manejar fragmentos fuera de orden
                self.fragmentos_pendientes[clave] = {
                    'total_fragmentos': total_fragmentos,
                    'fragmentos_recibidos': {},  # Usar diccionario en lugar de lista
                    'timestamp': time.time(),
                    'mac_origen': mac_origen,
                    'id_mensaje': id_mensaje,
                    'bytes_totales': 0,
                    'fragmentos_esperados': set(range(total_fragmentos))  # NUEVO: saber qué fragmentos esperamos
                }
                print(f"🔧 FragmentManager: Nuevo mensaje {clave} con {total_fragmentos} fragmentos")
            
            mensaje = self.fragmentos_pendientes[clave]
            
            # NUEVO: Actualizar total_fragmentos si recibimos uno mayor
            if total_fragmentos > mensaje['total_fragmentos']:
                print(f"🔧 FragmentManager: Actualizando total de {mensaje['total_fragmentos']} a {total_fragmentos}")
                mensaje['total_fragmentos'] = total_fragmentos
                # Actualizar fragmentos esperados
                mensaje['fragmentos_esperados'] = set(range(total_fragmentos))
            
            # Almacenar el fragmento en el diccionario
            if num_fragmento not in mensaje['fragmentos_recibidos']:
                mensaje['fragmentos_recibidos'][num_fragmento] = datos
                mensaje['bytes_totales'] += len(datos)
                mensaje['timestamp'] = time.time()
                print(f" FragmentManager: Fragmento {num_fragmento} almacenado")
            else:
                print(f"  FragmentManager: Fragmento {num_fragmento} ya estaba almacenado")
            
            # VERIFICACIÓN CORREGIDA: Comprobar si tenemos todos los fragmentos esperados
            fragmentos_recibidos = set(mensaje['fragmentos_recibidos'].keys())
            fragmentos_faltantes = mensaje['fragmentos_esperados'] - fragmentos_recibidos
            
            print(f" FragmentManager: Fragmentos recibidos: {len(fragmentos_recibidos)}/{mensaje['total_fragmentos']}")
            print(f" FragmentManager: Fragmentos faltantes: {sorted(fragmentos_faltantes)}")
            
            if not fragmentos_faltantes:
                # ¡Todos los fragmentos recibidos!
                print(f"🎉 FragmentManager: TODOS los fragmentos recibidos para {clave}")
                
                try:
                    # Reensamblar en orden
                    print(f"🔧 Reensamblando {mensaje['total_fragmentos']} fragmentos...")
                    fragmentos_ordenados = []
                    bytes_totales = 0
                    for i in range(mensaje['total_fragmentos']):
                        fragmento = mensaje['fragmentos_recibidos'][i]
                        fragmentos_ordenados.append(fragmento)
                        bytes_totales += len(fragmento)
                    
                    mensaje_completo = b''.join(fragmentos_ordenados)
                    print(f"✅ FragmentManager: Mensaje reensamblado - {len(mensaje_completo)} bytes ({len(mensaje_completo) / (1024*1024):.1f} MB)")
                    
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
                # Mostrar progreso detallado cada 100 fragmentos o 10%
                progreso = len(fragmentos_recibidos) / mensaje['total_fragmentos'] * 100
                if len(fragmentos_recibidos) % 100 == 0 or progreso % 10 < 1:
                    mb_recibidos = mensaje['bytes_totales'] / (1024 * 1024)
                    print(f"📊 FragmentManager: Progreso: {progreso:.1f}% ({len(fragmentos_recibidos)}/{mensaje['total_fragmentos']}) - {mb_recibidos:.1f} MB recibidos")
                    
                    # Llamar callback de progreso si está disponible
                    if self.progress_callback:
                        try:
                            self.progress_callback(
                                mac_origen, 
                                len(fragmentos_recibidos), 
                                mensaje['total_fragmentos'], 
                                mensaje['bytes_totales']
                            )
                        except Exception as e:
                            print(f"❌ Error en progress_callback: {e}")
            
            # Limpiar mensajes antiguos
            self._limpiar_antiguos()
        
            return None
    
    def _limpiar_antiguos(self):
        """Elimina mensajes fragmentados antiguos"""
        ahora = time.time()
        claves_a_eliminar = []
        
        for clave, mensaje in self.fragmentos_pendientes.items():
            tiempo_transcurrido = ahora - mensaje['timestamp']
            if tiempo_transcurrido > self.timeout:
                claves_a_eliminar.append(clave)
                fragmentos_recibidos = len(mensaje['fragmentos_recibidos'])
                minutos_transcurridos = tiempo_transcurrido / 60
                print(f"⏰ FragmentManager: Timeout para {clave} - {fragmentos_recibidos}/{mensaje['total_fragmentos']} fragmentos después de {minutos_transcurridos:.1f} minutos")
        
        for clave in claves_a_eliminar:
            del self.fragmentos_pendientes[clave]
    
    def obtener_estado_ensamblaje(self):
        """Retorna estadísticas de ensamblaje"""
        with self.lock:
            total_mensajes = len(self.fragmentos_pendientes)
            total_fragmentos_esperados = sum(msg['total_fragmentos'] for msg in self.fragmentos_pendientes.values())
            fragmentos_recibidos = sum(len(msg['fragmentos_recibidos']) for msg in self.fragmentos_pendientes.values())
            
            return {
                'mensajes_pendientes': total_mensajes,
                'fragmentos_totales': total_fragmentos_esperados,
                'fragmentos_recibidos': fragmentos_recibidos
            }