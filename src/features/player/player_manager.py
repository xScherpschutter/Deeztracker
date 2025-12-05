import flet as ft
import flet_audio as fta
import os
import shutil
import time
import random

class PlayerManager:
    def __init__(self, page: ft.Page):
        self.page = page
        self.playlist = []
        self.current_index = -1
        self.is_playing = False
        self.is_shuffle = False
        self.is_repeat = False  # False, 'all', 'one'
        
        # Current active audio control
        self.audio = None
        
        # State for UI
        self.duration = 0
        self.position = 0
        
        # Listeners
        self.track_change_listeners = []
        self.position_change_listeners = []
        self.state_change_listeners = []
        
        # Temp directory for playing files
        self.temp_audio_dir = "temp_audio"
        if not os.path.exists(self.temp_audio_dir):
            os.makedirs(self.temp_audio_dir)

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
            # 1. Clean up previous audio control
            if self.audio:
                try:
                    self.audio.pause()
                    if self.audio in self.page.overlay:
                        self.page.overlay.remove(self.audio)
                    # self.page.update() # Update later to avoid flicker
                except Exception as e:
                    print(f"PlayerManager: Error cleaning up old audio: {e}")

            # 2. Prepare temp file
            # We copy the file to a temp folder to ensure Flet can access it 
            # and to avoid any file locking or path issues.
            file_ext = os.path.splitext(track['path'])[1]
            # Use timestamp to ensure unique filename and avoid caching
            temp_filename = f"track_{int(time.time())}_{random.randint(1000, 9999)}{file_ext}"
            temp_path = os.path.join(self.temp_audio_dir, temp_filename)
            abs_temp_path = os.path.abspath(temp_path)
            
            shutil.copy(track['path'], abs_temp_path)
            print(f"PlayerManager: Copied file to {abs_temp_path}")

            # 3. Create NEW Audio control
            self.audio = fta.Audio(
                src=abs_temp_path,
                autoplay=True,
                volume=1.0,
                balance=0,
                on_loaded=self._on_loaded,
                on_duration_changed=self._on_duration_changed,
                on_position_changed=self._on_position_changed,
                on_state_changed=self._on_state_changed,
                on_seek_complete=self._on_seek_complete,
            )

            # 4. Add to overlay and update
            self.page.overlay.append(self.audio)
            self.page.update()
            
            # Optimistically set playing state
            self.is_playing = True
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

    def toggle_play_pause(self):
        if not self.audio:
            return

        if self.is_playing:
            self.audio.pause()
            self.is_playing = False
        else:
            self.audio.resume()
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
                    if self.audio:
                        self.audio.pause()
                    self.is_playing = False
                    self._notify_state_change()
                    return

        self.load_current_track()

    def prev_track(self):
        if not self.playlist:
            return

        # If played more than 3 seconds, restart track
        if self.position > 3000:
            if self.audio:
                self.audio.seek(0)
            return

        self.current_index -= 1
        if self.current_index < 0:
            self.current_index = 0
            
        self.load_current_track()

    def seek(self, position_ms):
        if self.audio:
            try:
                self.audio.seek(position_ms)
                self.position = position_ms # Optimistic update
            except Exception as e:
                print(f"PlayerManager: Seek error: {e}")

    def toggle_shuffle(self):
        self.is_shuffle = not self.is_shuffle
        return self.is_shuffle

    def toggle_repeat(self):
        self.is_repeat = not self.is_repeat
        return self.is_repeat

    # --- Event Handlers ---

    def _on_loaded(self, e):
        print("PlayerManager: Audio loaded")
        if self.audio:
            self.audio.play()
            self.is_playing = True
            self._notify_state_change()

    def _on_duration_changed(self, e):
        self.duration = int(e.data)
        # print(f"PlayerManager: Duration {self.duration}")

    def _on_position_changed(self, e):
        self.position = int(e.data)
        for listener in self.position_change_listeners:
            try:
                listener(self.position, self.duration)
            except Exception:
                pass

    def _on_state_changed(self, e):
        print(f"PlayerManager: State changed to {e.data}")
        if e.data == "completed":
            print("PlayerManager: Track completed, calling next_track")
            self.next_track()

    def _on_seek_complete(self, e):
        pass

    def _notify_state_change(self):
        for listener in self.state_change_listeners:
            try:
                listener(self.is_playing)
            except Exception as e:
                print(f"Error in state change listener: {e}")
        self.page.update()
