import subprocess

class Mac:
    @staticmethod
    def obtener_interfaces_fisicas():
        """Obtiene todas las interfaces físicas disponibles"""
        try:
            interfaces = subprocess.run("ls /sys/class/net/", shell=True, capture_output=True, text=True, check=True)
            
            lista_interfaces = interfaces.stdout.strip().split('\n')
            interfaces_fisicas = [iface for iface in lista_interfaces 
                                    if not iface.startswith(('br-', 'virbr', 'veth', 'tun', 'tap', 'wg')) and
                             not iface.endswith('-link')]
                
            return interfaces_fisicas
        except Exception as e:
            return []
    
    @staticmethod
    def obtener_mac(interfaz=None):
        """Obtiene la MAC de una interfaz específica o la primera disponible"""
        try:
            if interfaz is None:
                # Comportamiento original - obtener primera interfaz
                interfaces_fisicas = Mac.obtener_interfaces_fisicas()
                
                if not interfaces_fisicas:
                    return None, "No se encontraron interfaces físicas"
                
                interfaz = interfaces_fisicas[0]

            # Verificar que la interfaz existe y obtener su MAC
            mac_interfaz = subprocess.run(f"cat /sys/class/net/{interfaz}/address", shell=True, capture_output=True, text=True)
            if mac_interfaz.returncode == 0:
                return interfaz, mac_interfaz.stdout.strip()
            else:
                return None, f"No se pudo obtener MAC para {interfaz}"
        except Exception as e:
            return None, f"Error: {str(e)}"