"""
Utilities for detecting the operating system and getting music paths.
"""
import os
import sys


def get_os_name() -> str:
    """Detects the current operating system.
    
    Returns:
        str: 'windows', 'linux', or 'macos'
    """
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "darwin":
        return "macos"
    else:
        return "linux"


def get_music_folder() -> str:
    """Gets the operating system's music folder.
    
    Returns:
        str: Absolute path to the user's music folder.
    """
    user_home = os.path.expanduser("~")
    os_name = get_os_name()
    
    if os_name == "windows":
        # Windows: use the user's Music folder
        music_folder = os.path.join(user_home, "Music")
        
        # If it doesn't exist, try with "Música" (Spanish)
        if not os.path.exists(music_folder):
            music_folder = os.path.join(user_home, "Música")
        
        # If it still doesn't exist, create it
        if not os.path.exists(music_folder):
            music_folder = os.path.join(user_home, "Music")
            os.makedirs(music_folder, exist_ok=True)
    
    elif os_name == "macos":
        # macOS: use the user's Music folder
        music_folder = os.path.join(user_home, "Music")
        if not os.path.exists(music_folder):
            os.makedirs(music_folder, exist_ok=True)
    
    else:
        # Linux: use XDG_MUSIC_DIR if defined, otherwise ~/Music
        music_folder = os.environ.get("XDG_MUSIC_DIR")
        
        if not music_folder or not os.path.exists(music_folder):
            music_folder = os.path.join(user_home, "Music")
        
        if not os.path.exists(music_folder):
            # Try with "Música"
            alt_folder = os.path.join(user_home, "Música")
            if os.path.exists(alt_folder):
                music_folder = alt_folder
            else:
                os.makedirs(music_folder, exist_ok=True)
    
    return music_folder


def get_downloads_folder() -> str:
    """Gets the operating system's downloads folder.
    
    Returns:
        str: Absolute path to the user's downloads folder.
    """
    user_home = os.path.expanduser("~")
    
    downloads_folder = os.path.join(user_home, "Downloads")
    
    # Check for Spanish alternatives
    if not os.path.exists(downloads_folder):
        downloads_folder = os.path.join(user_home, "Descargas")
    
    if not os.path.exists(downloads_folder):
        downloads_folder = os.path.join(user_home, "Downloads")
        os.makedirs(downloads_folder, exist_ok=True)
    
    return downloads_folder


def get_deeztracker_music_folder() -> str:
    """Gets the specific Deeztracker folder for saving music.
    Creates a 'Deeztracker' subfolder inside the system's music folder.
    
    Returns:
        str: Absolute path to the Deeztracker/Music folder.
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


# System information for debugging
def get_system_info() -> dict:
    """Gets system information for debugging.
    
    Returns:
        dict: Dictionary with system information.
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
