import subprocess
class Mac:
    @staticmethod
    def obtener_mac():
        try:
            interfaces = subprocess.run("ls /sys/class/net/", shell=True, capture_output=True, text=True, check=True)
            
            lista_interfaces = interfaces.stdout.strip().split('\n')
            interfaces_fisicas = [iface for iface in lista_interfaces 
                                    if not iface.startswith(('lo', 'docker', 'br-', 'virbr', 'veth', 'tun', 'tap', 'wg')) and
                             not iface.endswith('-link')]
                
            if not interfaces_fisicas:
                return "No se encontraron interfaces físicas"
            
            interfaz_principal = interfaces_fisicas[0]

            mac_interfaz = subprocess.run(f"cat /sys/class/net/{interfaz_principal}/address", shell=True, capture_output=True, text=True)
            if mac_interfaz.returncode == 0:
                return interfaz_principal, mac_interfaz.stdout.strip()
            else:
                return f"No se pudo obtener MAC para {interfaz_principal}"
        except Exception as e:
            return f"Error: {str(e)}"