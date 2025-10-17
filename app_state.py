import json
import os
from config import CONTACTS_FILE

class AppState:
    def __init__(self):
        self.contactos = {}
        self.destino_actual = "FF:FF:FF:FF:FF:FF"
        self.archivo_seleccionado = None
        self.carpeta_seleccionada = None
        self.interfaz_seleccionada = None
        self.dic_usuarios = {"todos": "ff:ff:ff:ff:ff:ff"}
        self.stop_event = None
        self.archivo_contactos = CONTACTS_FILE  
        self.cargar_contactos()

    def cargar_contactos(self):
        """Carga contactos básicos"""
        try:
            if os.path.exists(self.archivo_contactos):
                with open(self.archivo_contactos, 'r') as f:
                    self.contactos = json.load(f)
        except:
            self.contactos = {
                "FF:FF:FF:FF:FF:FF": "Todos (Broadcast)",
                "01:00:5E:00:00:01": "Multicast"
            }
    
    def guardar_contactos(self):
        """Guarda contactos"""
        try:
            with open(self.archivo_contactos, 'w') as f:
                json.dump(self.contactos, f)
        except:
            pass
    
    def validar_mac(self, mac):
        """Valida dirección MAC"""
        if mac.upper() == "FF:FF:FF:FF:FF:FF":
            return True
        
        partes = mac.split(':')
        if len(partes) != 6:
            return False
        
        for parte in partes:
            if len(parte) != 2 or not all(c in '0123456789abcdefABCDEF' for c in parte):
                return False
        
        return True
    