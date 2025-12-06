import sys
import os
import flet as ft
import vlc
import random
import threading
import time
import platform
from .media_notifications import MediaNotificationManager

class PlayerManager:
    def __init__(self, page: ft.Page):
        self.page = page
        self.playlist = []
        self.current_index = -1

        self.is_playing = False
        self.is_shuffle = False
        self.is_repeat = False
        
        # VLC instance and player
        self.vlc_available = False
        self.vlc_instance = None
        self.player = None
        self.event_manager = None
        
        try:
            # Try to initialize VLC
            if getattr(sys, 'frozen', False):
                bundle_dir = sys._MEIPASS
                plugin_path = os.path.join(bundle_dir, 'vlc_plugins')
                os.environ['VLC_PLUGIN_PATH'] = plugin_path

            self.vlc_instance = vlc.Instance()
            self.player = self.vlc_instance.media_player_new()
            
            # VLC event manager for track completion
            self.event_manager = self.player.event_manager()
            self.event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_track_end)
            
            self.vlc_available = True
        except (NameError, OSError, AttributeError) as e:
            print(f"VLC initialization failed: {e}")
            print("Please install VLC system dependencies (e.g., 'sudo apt install vlc libvlc-dev')")

            def show_vlc_warning():
                snack_bar = ft.SnackBar(
                    content=ft.Text("VLC libraries not found. Audio playback will not work. Please install VLC."),
                    bgcolor=ft.colors.ERROR,
                    duration=10000,
                    action="OK"
                )
                self.page.open(snack_bar)
                self.page.update()
            
            show_vlc_warning()
            
        # State for UI
        self.duration = 0  # in milliseconds
        self.position = 0  # in milliseconds
        
        # Flag to distinguish user pause from track end
        self._user_paused = False
        
        # Listeners
        self.track_change_listeners = []
        self.position_change_listeners = []
        self.state_change_listeners = []
        
        # Position update thread
        self._position_thread = None
        self._stop_position_thread = False
        
        # Initialize media notifications
        self.media_notifications = None
        try:
            self.media_notifications = MediaNotificationManager(self)
        except Exception as e:
            print(f"Could not initialize media notifications: {e}")

    def subscribe(self, on_track_change=None, on_state_change=None, on_position_change=None):
        if on_track_change:
            self.track_change_listeners.append(on_track_change)
        if on_state_change:
            self.state_change_listeners.append(on_state_change)
        if on_position_change:
            self.position_change_listeners.append(on_position_change)

    def unsubscribe(self, on_track_change=None, on_state_change=None, on_position_change=None):
        if on_track_change and on_track_change in self.track_change_listeners:
            self.track_change_listeners.remove(on_track_change)
        if on_state_change and on_state_change in self.state_change_listeners:
            self.state_change_listeners.remove(on_state_change)
        if on_position_change and on_position_change in self.position_change_listeners:
            self.position_change_listeners.remove(on_position_change)

    def play_track(self, track, playlist=None):
        """Starts playing a specific track, optionally updating the playlist."""
        if playlist:
            self.playlist = playlist
            try:
                self.current_index = self.playlist.index(track)
            except ValueError:
                self.current_index = 0
        
        self.load_current_track()

    def load_current_track(self):
        """Loads and plays the track at self.current_index."""
        if not self.playlist or self.current_index < 0 or self.current_index >= len(self.playlist):
            return

        track = self.playlist[self.current_index]
        print(f"PlayerManager: Preparing to play {track['path']}")

        try:
            # Stop any current playback
            self._stop_position_updates()
            
            if not self.vlc_available:
                print("PlayerManager: VLC not available, skipping playback")
                # Still notify listeners so UI updates with track info
                self.is_playing = False
                self._notify_state_change()
                for listener in self.track_change_listeners:
                    try:
                        listener(track)
                    except Exception:
                        pass
                return

            if self.player.is_playing():
                self.player.stop()

            # Reset pause flag
            self._user_paused = False

            # Create VLC media and set metadata
            media = self.vlc_instance.media_new(track['path'])
            
            # Set metadata for native OS notifications
            media.set_meta(vlc.Meta.Title, track.get('title', 'Unknown'))
            media.set_meta(vlc.Meta.Artist, track.get('artist', 'Unknown'))
            media.set_meta(vlc.Meta.Album, track.get('album', ''))
            
            # Set cover art if available
            if 'cover' in track and track['cover']:
                # VLC expects file:// URL for local files
                cover_path = track['cover']
                if not cover_path.startswith('http') and not cover_path.startswith('file://'):
                    cover_path = f"file:///{cover_path.replace('\\', '/')}"
                media.set_meta(vlc.Meta.ArtworkURL, cover_path)
            
            # Save metadata to media
            media.save_meta()
            
            # Load media into player
            self.player.set_media(media)
            
            # Wait for media to parse (needed for duration)
            media.parse()
            self.duration = media.get_duration()  # Already in milliseconds
            print(f"PlayerManager: Loaded track, duration: {self.duration}ms")
            
            # Play the track
            self.player.play()
            self.is_playing = True
            
            # Start position update thread
            self._start_position_updates()
            
            self._notify_state_change()
            
            # Notify track change
            for listener in self.track_change_listeners:
                try:
                    listener(track)
                except Exception as e:
                    print(f"Error in track change listener: {e}")
            
            # Update media notifications
            if self.media_notifications:
                self.media_notifications.update_metadata(track)

        except Exception as e:
            print(f"PlayerManager: Critical error loading track: {e}")
            import traceback
            traceback.print_exc()
            self.is_playing = False
            self._notify_state_change()

    def _on_track_end(self, event):
        """VLC event callback when track ends."""
        print("PlayerManager: Track ended (VLC event)")
        if not self._user_paused:
            # Schedule next track on the page's thread
            self.page.run_task(self._async_next_track)

    def _start_position_updates(self):
        """Start a background thread to update position."""
        if not self.vlc_available:
            return
            
        self._stop_position_thread = False
        self._position_thread = threading.Thread(target=self._position_update_loop, daemon=True)
        self._position_thread.start()

    def _stop_position_updates(self):
        """Stop the position update thread."""
        self._stop_position_thread = True
        if self._position_thread and self._position_thread.is_alive():
            self._position_thread.join(timeout=0.5)

    def _position_update_loop(self):
        """Background loop to update position."""
        while not self._stop_position_thread:
            try:
                # Skip if user paused
                if self._user_paused:
                    time.sleep(0.25)
                    continue
                
                # Get current position from VLC
                if self.player.is_playing():
                    current_pos = self.player.get_time()  # Returns milliseconds
                    if current_pos != -1:
                        self.position = current_pos
                    
                    # Update duration if not set yet
                    if self.duration == 0:
                        length = self.player.get_length()
                        if length > 0:
                            self.duration = length
                    
                    # Notify listeners
                    for listener in self.position_change_listeners:
                        try:
                            listener(self.position, self.duration)
                        except Exception:
                            pass
                            
            except Exception as e:
                print(f"Position update error: {e}")
            
            time.sleep(0.25)

    async def _async_next_track(self):
        """Async wrapper for next_track to be called from background thread."""
        self.next_track()

    def toggle_play_pause(self):
        if not self.vlc_available or not self.player.get_media():
            return

        if self.is_playing:
            self._user_paused = True  # Mark as user-initiated pause
            self.player.pause()
            self.is_playing = False
        else:
            self._user_paused = False  # Resume, clear the pause flag
            self.player.play()
            self.is_playing = True
        
        self._notify_state_change()

    def next_track(self):
        if not self.playlist:
            return

        if self.is_shuffle:
            self.current_index = random.randint(0, len(self.playlist) - 1)
        else:
            self.current_index += 1
            if self.current_index >= len(self.playlist):
                if self.is_repeat:
                    self.current_index = 0
                else:
                    self.current_index = len(self.playlist) - 1
                    # Stop at end of playlist
                    self._stop_position_updates()
                    if self.vlc_available and self.player.is_playing():
                        self.player.stop()
                    self.is_playing = False
                    self._notify_state_change()
                    return

        self.load_current_track()

    def prev_track(self):
        if not self.playlist:
            return

        # If played more than 3 seconds, restart track
        if self.position > 3000:
            if self.vlc_available:
                self.player.set_time(0)
            self.position = 0
            return

        self.current_index -= 1
        if self.current_index < 0:
            self.current_index = 0
            
        self.load_current_track()

    def seek(self, position_ms):
        if not self.vlc_available:
            return
            
        if self.player.get_media():
            try:
                # VLC uses milliseconds
                self.player.set_time(int(position_ms))
                self.position = position_ms
            except Exception as e:
                print(f"PlayerManager: Seek error: {e}")

    def set_volume(self, volume):
        """Set volume (0.0 to 1.0)."""
        if not self.vlc_available:
            return
            
        try:
            # VLC uses 0-100 scale
            vlc_volume = int(volume * 100)
            self.player.audio_set_volume(vlc_volume)
        except Exception as e:
            print(f"PlayerManager: Volume error: {e}")

    def toggle_shuffle(self):
        self.is_shuffle = not self.is_shuffle
        return self.is_shuffle

    def toggle_repeat(self):
        self.is_repeat = not self.is_repeat
        return self.is_repeat

    def _notify_state_change(self):
        for listener in self.state_change_listeners:
            try:
                listener(self.is_playing)
            except Exception as e:
                print(f"Error in state change listener: {e}")
        
        # Update media notifications
        if self.media_notifications:
            self.media_notifications.update_playback_state(self.is_playing)
        
        self.page.update()

    def cleanup(self):
        """Clean up resources when the player is destroyed."""
        self._stop_position_updates()
        
        if not self.vlc_available:
            return
            
        if self.player.is_playing():
            self.player.stop()
        if self.media_notifications:
            self.media_notifications.cleanup()
        self.player.release()
        self.vlc_instance.release()
