"""
Windows SMTC (System Media Transport Controls) Backend
"""
try:
    from winsdk.windows.media import (
        SystemMediaTransportControls,
        SystemMediaTransportControlsButton,
        SystemMediaTransportControlsButtonPressedEventArgs,
        MediaPlaybackStatus,
        MediaPlaybackType,
    )
    from winsdk.windows.storage.streams import RandomAccessStreamReference
    from winsdk.windows.foundation import Uri
    import winsdk.windows.media.control as media_control
    SMTC_AVAILABLE = True
except ImportError:
    SMTC_AVAILABLE = False
    print("Warning: winsdk not available, SMTC disabled")

import asyncio
from pathlib import Path
import sys

class SMTCBackend:
    """Windows System Media Transport Controls integration"""
    
    def __init__(self, player_manager):
        if not SMTC_AVAILABLE:
            raise ImportError("winsdk is required for Windows SMTC")
        
        self.player_manager = player_manager
        self.smtc = None
        self.current_track = None
        self._init_smtc()
    
    def _init_smtc(self):
        """Initialize System Media Transport Controls"""
        try:
            import winsdk._winrt as _winrt
            from winsdk.windows.media.playback import MediaPlayer
            
            self.media_player = MediaPlayer()
            self.smtc = self.media_player.system_media_transport_controls
            
            if not self.smtc:
                raise Exception("Could not get SMTC from MediaPlayer")
            
            self.smtc.is_enabled = True
            self.smtc.is_play_enabled = True
            self.smtc.is_pause_enabled = True
            self.smtc.is_next_enabled = True
            self.smtc.is_previous_enabled = True
            
            self.smtc.add_button_pressed(self._on_button_pressed)
            
            print("SMTC initialized successfully")
        except Exception as e:
            print(f"Error initializing SMTC: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_button_pressed(self, sender, args: SystemMediaTransportControlsButtonPressedEventArgs):
        """Handle media button presses"""
        button = args.button
        
        print(f"SMTC button pressed: {button}")
        
        if button == SystemMediaTransportControlsButton.PLAY:
            if not self.player_manager.is_playing:
                self.player_manager.toggle_play_pause()
        elif button == SystemMediaTransportControlsButton.PAUSE:
            if self.player_manager.is_playing:
                self.player_manager.toggle_play_pause()
        elif button == SystemMediaTransportControlsButton.NEXT:
            self.player_manager.next_track()
        elif button == SystemMediaTransportControlsButton.PREVIOUS:
            self.player_manager.prev_track()
    
    def update_metadata(self, track: dict):
        """Update media metadata in SMTC"""
        if not self.smtc:
            return
        
        self.current_track = track
        
        try:
            updater = self.smtc.display_updater
            updater.type = MediaPlaybackType.MUSIC
            
            cover_path = track.get('cover', '')
            
            if cover_path and cover_path.strip():
                try:
                    if cover_path.startswith('http'):
                        uri = Uri(cover_path)
                        updater.thumbnail = RandomAccessStreamReference.create_from_uri(uri)
                    else:
                        file_path = Path(cover_path).resolve()
                        
                        if file_path.exists():
                            try:
                                from winsdk.windows.storage import StorageFile
                                
                                # Define async wrapper for WinRT IAsyncOperation
                                async def get_storage_file():
                                    return await StorageFile.get_file_from_path_async(str(file_path))
                                
                                # Try to use StorageFile with proper async handling
                                try:
                                    # Check if there's a running event loop
                                    try:
                                        loop = asyncio.get_running_loop()
                                        # Use run_coroutine_threadsafe with the async wrapper
                                        storage_file = asyncio.run_coroutine_threadsafe(
                                            get_storage_file(),
                                            loop
                                        ).result(timeout=2)
                                    except RuntimeError:
                                        # No running loop, create a new one
                                        storage_file = asyncio.run(get_storage_file())
                                    
                                    stream_ref = RandomAccessStreamReference.create_from_file(storage_file)
                                    updater.thumbnail = stream_ref
                                    print(f"Thumbnail set: {track.get('title', 'Unknown')}")
                                except Exception as async_error:
                                    print(f"StorageFile async error: {async_error}, falling back to URI")
                                    raise  # Re-raise to trigger URI fallback
                                
                            except Exception as storage_error:
                                from urllib.parse import quote
                                
                                path_str = str(file_path).replace('\\', '/')
                                path_parts = path_str.split('/')
                                encoded_parts = [quote(part) for part in path_parts]
                                encoded_path = '/'.join(encoded_parts)
                                
                                if not encoded_path.startswith('/'):
                                    encoded_path = '/' + encoded_path
                                file_uri = f"file://{encoded_path}"
                                
                                uri = Uri(file_uri)
                                stream_ref = RandomAccessStreamReference.create_from_uri(uri)
                                updater.thumbnail = stream_ref
                                print(f"Thumbnail set via URI fallback: {track.get('title', 'Unknown')}")
                                
                except Exception as e:
                    print(f"Thumbnail error: {e}")
            
            music_props = updater.music_properties
            music_props.title = track.get('title', 'Unknown')
            music_props.artist = track.get('artist', 'Unknown')
            music_props.album_title = track.get('album', '')
            
            updater.update()
            print(f"SMTC metadata updated: {track.get('title', 'Unknown')}")
            
        except Exception as e:
            print(f"SMTC metadata update error: {e}")
            import traceback
            traceback.print_exc()
    
    def update_playback_state(self, is_playing: bool):
        """Update playback state in SMTC"""
        if not self.smtc:
            return
        
        try:
            if is_playing:
                self.smtc.playback_status = MediaPlaybackStatus.PLAYING
            else:
                self.smtc.playback_status = MediaPlaybackStatus.PAUSED
            
            print(f"SMTC playback state: {'PLAYING' if is_playing else 'PAUSED'}")
        except Exception as e:
            print(f"SMTC playback state error: {e}")
    
    def cleanup(self):
        """Clean up SMTC resources"""
        if self.smtc:
            try:
                self.smtc.is_enabled = False
            except:
                pass
