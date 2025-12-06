import sys
import os
import flet as ft

# Configure environment for PyInstaller
if getattr(sys, 'frozen', False):
    # Add the bundle directory to LD_LIBRARY_PATH so ctypes can find libvlc.so
    bundle_dir = sys._MEIPASS
    current_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
    os.environ['LD_LIBRARY_PATH'] = f"{bundle_dir}:{current_ld_path}"
    
    # Explicitly tell python-vlc where the library is
    libvlc_path = os.path.join(bundle_dir, 'libvlc.so.5')
    os.environ['PYTHON_VLC_LIB_PATH'] = libvlc_path

from ui.app import main as ui_main

if __name__ == "__main__":
    ft.app(target=ui_main)