"""
Linux MPRIS Backend (placeholder for future implementation)
"""

class MPRISBackend:
    """Linux MPRIS integration (to be implemented)"""
    
    def __init__(self, player_manager):
        self.player_manager = player_manager
        print("MPRIS backend not yet implemented")
    
    def update_metadata(self, track: dict):
        """Update media metadata"""
        pass
    
    def update_playback_state(self, is_playing: bool):
        """Update playback state"""
        pass
    
    def cleanup(self):
        """Clean up resources"""
        pass
