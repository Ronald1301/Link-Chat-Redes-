import os

#colores
bg_color = '#2F2F2F'
fg_color = 'white'
entry_bg = '#404040'
button_bg  = '#505050'
border_color = 'black'

# Colores para burbujas de chat
bubble_me_bg = '#0084FF'  # Azul para mis mensajes
bubble_other_bg = '#404040'  # Gris para mensajes de otros
bubble_system_bg = '#FF6B00'  # Naranja para mensajes del sistema

font_size = 14  # Aumentado para mejor legibilidad
font_family='Arial'

#rutas y archivos
DOWNLOADS_DIR = "downloads"
CONTACTS_FILE = "contactos_minimal.json"

def setup_environment():
    os.environ['TK_SILENCE_DEPRECATION'] = '1'
    os.environ['XLIB_SKIP_ARGB_VISUALS'] = '1'
    os.environ['QT_X11_NO_MITSHM'] = '1'
    os.environ['_JAVA_AWT_WM_NONREPARENTING'] = '1'

    if 'virtualbox' in os.environ.get('SESSION_MANAGER', '').lower():
        os.environ['GDK_BACKEND'] = 'x11'
    
    try:
        os.environ['TK_FONT'] = 'Arial 14'
    except:
        pass

def configurar_tkinter():
    import tkinter as tk
    tk.Button._default_state = 'normal'