"""
Utilidades para detectar el sistema operativo y obtener rutas de música.
"""
import os
import sys


def get_os_name() -> str:
    """Detecta el sistema operativo actual.
    
    Returns:
        str: 'windows', 'linux', o 'macos'
    """
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "darwin":
        return "macos"
    else:
        return "linux"


def get_music_folder() -> str:
    """Obtiene la carpeta de música del sistema operativo.
    
    Returns:
        str: Ruta absoluta a la carpeta de música del usuario.
    """
    user_home = os.path.expanduser("~")
    os_name = get_os_name()
    
    if os_name == "windows":
        # Windows: usar la carpeta Music del usuario
        music_folder = os.path.join(user_home, "Music")
        
        # Si no existe, intentar con "Música" (español)
        if not os.path.exists(music_folder):
            music_folder = os.path.join(user_home, "Música")
        
        # Si tampoco existe, crearla
        if not os.path.exists(music_folder):
            music_folder = os.path.join(user_home, "Music")
            os.makedirs(music_folder, exist_ok=True)
    
    elif os_name == "macos":
        # macOS: usar la carpeta Music del usuario
        music_folder = os.path.join(user_home, "Music")
        if not os.path.exists(music_folder):
            os.makedirs(music_folder, exist_ok=True)
    
    else:
        # Linux: usar XDG_MUSIC_DIR si está definido, sino ~/Music
        music_folder = os.environ.get("XDG_MUSIC_DIR")
        
        if not music_folder or not os.path.exists(music_folder):
            music_folder = os.path.join(user_home, "Music")
        
        if not os.path.exists(music_folder):
            # Intentar con "Música"
            alt_folder = os.path.join(user_home, "Música")
            if os.path.exists(alt_folder):
                music_folder = alt_folder
            else:
                os.makedirs(music_folder, exist_ok=True)
    
    return music_folder


def get_downloads_folder() -> str:
    """Obtiene la carpeta de descargas del sistema operativo.
    
    Returns:
        str: Ruta absoluta a la carpeta de descargas del usuario.
    """
    user_home = os.path.expanduser("~")
    
    downloads_folder = os.path.join(user_home, "Downloads")
    
    # Verificar alternativas en español
    if not os.path.exists(downloads_folder):
        downloads_folder = os.path.join(user_home, "Descargas")
    
    if not os.path.exists(downloads_folder):
        downloads_folder = os.path.join(user_home, "Downloads")
        os.makedirs(downloads_folder, exist_ok=True)
    
    return downloads_folder


def get_deeztracker_music_folder() -> str:
    """Obtiene la carpeta específica de Deeztracker para guardar música.
    Crea una subcarpeta 'Deeztracker' dentro de la carpeta de música del sistema.
    
    Returns:
        str: Ruta absoluta a la carpeta Deeztracker/Music.
    """
    music_folder = get_music_folder()
    deeztracker_folder = os.path.join(music_folder, "Deeztracker")
    
    if not os.path.exists(deeztracker_folder):
        os.makedirs(deeztracker_folder, exist_ok=True)
    
    return deeztracker_folder


def get_custom_music_folder(custom_path: str = None) -> str:
    if custom_path and os.path.exists(custom_path):
        return custom_path
    return get_deeztracker_music_folder()


# Información del sistema para debugging
def get_system_info() -> dict:
    """Obtiene información del sistema para debugging.
    
    Returns:
        dict: Diccionario con información del sistema.
    """
    return {
        "os": get_os_name(),
        "platform": sys.platform,
        "music_folder": get_music_folder(),
        "downloads_folder": get_downloads_folder(),
        "deeztracker_folder": get_deeztracker_music_folder(),
    }


def get_system_info_with_custom(custom_path: str = None) -> dict:
    return {
        "os": get_os_name(),
        "platform": sys.platform,
        "music_folder": get_music_folder(),
        "downloads_folder": get_downloads_folder(),
        "deeztracker_folder": get_deeztracker_music_folder(),
        "custom_music_folder": get_custom_music_folder(custom_path),
    }
