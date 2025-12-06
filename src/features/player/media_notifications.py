"""
Media Notifications Manager
Handles native OS media notifications (SMTC on Windows, MPRIS on Linux)
"""
import platform
from typing import Optional, Callable

class MediaNotificationManager:
    """Cross-platform media notification manager"""
    
    def __init__(self, player_manager):
        self.player_manager = player_manager
        self.platform = platform.system()
        self.backend = None
        
        # Initialize platform-specific backend
        self._init_backend()
        
    def _init_backend(self):
        """Initialize the appropriate backend for the platform"""
        try:
            if self.platform == "Windows":
                from .backends.smtc_backend import SMTCBackend
                self.backend = SMTCBackend(self.player_manager)
                print("Windows SMTC initialized")
            elif self.platform == "Linux":
                from .backends.mpris_backend import MPRISBackend
                self.backend = MPRISBackend(self.player_manager)
                print("Linux MPRIS initialized")
            else:
                print(f"Media notifications not supported on {self.platform}")
        except ImportError as e:
            print(f"Could not initialize media notifications: {e}")
            self.backend = None
    
    def update_metadata(self, track: dict):
        """Update metadata in native OS controls"""
        if self.backend:
            self.backend.update_metadata(track)
    
    def update_playback_state(self, is_playing: bool):
        """Update playback state"""
        if self.backend:
            self.backend.update_playback_state(is_playing)
    
    def cleanup(self):
        """Clean up resources"""
        if self.backend:
            self.backend.cleanup()
