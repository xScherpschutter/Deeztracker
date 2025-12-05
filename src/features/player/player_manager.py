import flet as ft
from just_playback import Playback
import random
import threading
import time

class PlayerManager:
    def __init__(self, page: ft.Page):
        self.page = page
        self.playlist = []
        self.current_index = -1
        self.is_playing = False
        self.is_shuffle = False
        self.is_repeat = False
        
        # just_playback instance
        self.playback = Playback()
        
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
            if self.playback.active:
                self.playback.stop()

            # Reset pause flag
            self._user_paused = False

            # Load and play the new track
            self.playback.load_file(track['path'])
            self.duration = int(self.playback.duration * 1000)  # Convert to ms
            print(f"PlayerManager: Loaded track, duration: {self.duration}ms")
            
            self.playback.play()
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

        except Exception as e:
            print(f"PlayerManager: Critical error loading track: {e}")
            self.is_playing = False
            self._notify_state_change()

    def _start_position_updates(self):
        """Start a background thread to update position."""
        self._stop_position_thread = False
        self._position_thread = threading.Thread(target=self._position_update_loop, daemon=True)
        self._position_thread.start()

    def _stop_position_updates(self):
        """Stop the position update thread."""
        self._stop_position_thread = True
        if self._position_thread and self._position_thread.is_alive():
            self._position_thread.join(timeout=0.5)

    def _position_update_loop(self):
        """Background loop to update position and check for track completion."""
        last_position = -1
        stalled_count = 0
        loop_count = 0
        
        while not self._stop_position_thread:
            try:
                loop_count += 1
                
                # Skip everything if user paused
                if self._user_paused:
                    time.sleep(0.25)
                    continue
                
                # Check playback state
                is_active = self.playback.active
                is_playing = self.playback.playing if is_active else False
                
                # Update position if active
                if is_active:
                    self.position = int(self.playback.curr_pos * 1000)
                    
                    # Notify listeners
                    for listener in self.position_change_listeners:
                        try:
                            listener(self.position, self.duration)
                        except Exception:
                            pass
                
                # Debug log every ~5 seconds
                if loop_count % 20 == 0:
                    print(f"PlayerManager: pos={self.position}ms, dur={self.duration}ms, active={is_active}, playing={is_playing}, stalled={stalled_count}")
                
                # ===== TRACK COMPLETION DETECTION =====
                # These checks are OUTSIDE of `if is_active` because playback may become inactive when done
                
                # Method 1: Playback stopped naturally (playing=False, not paused by user)
                if not is_playing and self.position > 1000:
                    print(f"PlayerManager: Track completed (not playing) - pos={self.position}, dur={self.duration}")
                    self._stop_position_thread = True
                    self.page.run_task(self._async_next_track)
                    break
                
                # Method 2: Position >= duration
                if self.duration > 0 and self.position >= self.duration:
                    print(f"PlayerManager: Track completed (pos >= dur) - pos={self.position}, dur={self.duration}")
                    self._stop_position_thread = True
                    self.page.run_task(self._async_next_track)
                    break
                
                # Method 3: Position stalled when past 90%
                if self.position == last_position:
                    stalled_count += 1
                else:
                    stalled_count = 0
                
                if stalled_count >= 4 and self.duration > 0 and self.position > (self.duration * 0.9):
                    print(f"PlayerManager: Track completed (stalled) - pos={self.position}, dur={self.duration}")
                    self._stop_position_thread = True
                    self.page.run_task(self._async_next_track)
                    break
                
                last_position = self.position
                        
            except Exception as e:
                print(f"Position update error: {e}")
            
            time.sleep(0.25)

    async def _async_next_track(self):
        """Async wrapper for next_track to be called from background thread."""
        self.next_track()

    def toggle_play_pause(self):
        if not self.playback.active:
            return

        if self.is_playing:
            self._user_paused = True  # Mark as user-initiated pause
            self.playback.pause()
            self.is_playing = False
        else:
            self._user_paused = False  # Resume, clear the pause flag
            self.playback.resume()
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
                    if self.playback.active:
                        self.playback.stop()
                    self.is_playing = False
                    self._notify_state_change()
                    return

        self.load_current_track()

    def prev_track(self):
        if not self.playlist:
            return

        # If played more than 3 seconds, restart track
        if self.position > 3000:
            self.playback.seek(0)
            self.position = 0
            return

        self.current_index -= 1
        if self.current_index < 0:
            self.current_index = 0
            
        self.load_current_track()

    def seek(self, position_ms):
        if self.playback.active:
            try:
                # just_playback uses seconds
                self.playback.seek(position_ms / 1000)
                self.position = position_ms
            except Exception as e:
                print(f"PlayerManager: Seek error: {e}")

    def set_volume(self, volume):
        """Set volume (0.0 to 1.0)."""
        if self.playback.active:
            self.playback.set_volume(volume)

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
        self.page.update()

    def cleanup(self):
        """Clean up resources when the player is destroyed."""
        self._stop_position_updates()
        if self.playback.active:
            self.playback.stop()
