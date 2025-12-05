import flet as ft
import pygame
import random
import asyncio
import os

class PlayerManager:
    def __init__(self, page: ft.Page):
        self.page = page
        
        # Initialize Pygame Mixer
        pygame.mixer.init()
        
        self.playlist = []
        self.current_index = -1
        self.is_playing = False
        self.is_shuffle = False
        self.is_repeat = False # False, 'all', 'one'
        
        # Callbacks for UI updates
        self.track_change_listeners = []
        self.position_change_listeners = []
        self.state_change_listeners = []
        
        self.duration = 0
        self.position = 0
        self.seek_offset = 0 # Offset to add to get_pos() for accurate position
        
        # Start background task for position updates
        self.page.run_task(self.update_progress_loop)

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

    async def update_progress_loop(self):
        print("PlayerManager: Starting progress loop")
        while True:
            # print(f"PlayerManager: Loop tick. Playing: {self.is_playing}, Busy: {pygame.mixer.music.get_busy()}")
            if self.is_playing and pygame.mixer.music.get_busy():
                # Pygame get_pos returns milliseconds since playback started
                # It does NOT account for seeking directly, but we handle seek offset manually if needed
                # Actually, pygame.mixer.music.get_pos() returns time played, not absolute position if seeked.
                # However, for simple implementation, we can use it. 
                # Better approach: track start time and calculate.
                # For now, let's use get_pos() and see if it suffices or if we need offset.
                # Note: get_pos() returns -1 if not playing.
                
                current_pos = pygame.mixer.music.get_pos()
                if current_pos != -1:
                    self.position = self.seek_offset + current_pos
                    # Notify listeners
                    for listener in self.position_change_listeners:
                        try:
                            listener(self.position, self.duration)
                        except Exception:
                            pass
                
                # Check if track finished
                # Pygame music.get_busy() returns False when music stops.
                # If we expect it to be playing (self.is_playing is True) but it's not busy,
                # then it finished naturally.
                if not pygame.mixer.music.get_busy() and self.is_playing:
                     print("PlayerManager: Track finished naturally. Calling next_track()")
                     self.next_track()

            await asyncio.sleep(0.5)

    def play_track(self, track, playlist=None):
        if playlist:
            self.playlist = playlist
            try:
                self.current_index = self.playlist.index(track)
            except ValueError:
                self.current_index = 0
        
        self.load_current_track()

    def load_current_track(self):
        if not self.playlist or self.current_index < 0 or self.current_index >= len(self.playlist):
            return

        track = self.playlist[self.current_index]
        print(f"Loading track: {track['path']}")
        
        try:
            pygame.mixer.music.load(track['path'])
            pygame.mixer.music.play()
            self.is_playing = True
            self.seek_offset = 0 # Reset offset on new track
            
            # Get duration
            # Pygame doesn't give duration of stream easily. We might need Mutagen or similar.
            # Or use Sound object for duration?
            # pygame.mixer.Sound(file).get_length() * 1000
            try:
                sound = pygame.mixer.Sound(track['path'])
                self.duration = int(sound.get_length() * 1000)
            except Exception as e:
                print(f"Could not get duration: {e}")
                self.duration = 0 # Unknown
            
            # Notify listeners
            for listener in self.track_change_listeners:
                try:
                    listener(track)
                except Exception as e:
                    print(f"Error in track change listener: {e}")
            
            self.page.update()
            
        except Exception as e:
            print(f"Error playing track: {e}")
            self.is_playing = False

    def toggle_play_pause(self):
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
        else:
            pygame.mixer.music.unpause()
            # If it was stopped (not paused), unpause might not work, need play.
            # But we assume it was paused.
            # If nothing loaded, this might fail.
            if not pygame.mixer.music.get_busy():
                 # Maybe it was stopped or never started?
                 # If we have a current track, try to play it?
                 pass
            self.is_playing = True
        
        for listener in self.state_change_listeners:
            try:
                listener(self.is_playing)
            except Exception as e:
                print(f"Error in state change listener: {e}")
            
        self.page.update()

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
                    pygame.mixer.music.stop()
                    self.is_playing = False
                    for listener in self.state_change_listeners:
                        listener(self.is_playing)
                    return

        self.load_current_track()

    def prev_track(self):
        if not self.playlist:
            return

        # If played more than 3 seconds, restart
        if pygame.mixer.music.get_pos() > 3000:
            pygame.mixer.music.rewind()
            pygame.mixer.music.play() # Rewind might stop it?
            return

        self.current_index -= 1
        if self.current_index < 0:
            self.current_index = 0
            
        self.load_current_track()

    def seek(self, position_ms):
        # Pygame set_pos is unreliable for many formats.
        # Use play(start=...) instead.
        try:
            start_sec = position_ms / 1000.0
            pygame.mixer.music.play(start=start_sec)
            
            # When using play(start=...), get_pos() resets to 0 (or close to it).
            # So seek_offset should be the start time we requested.
            self.seek_offset = position_ms
            self.position = position_ms
            
            # Ensure it's playing (play() starts it)
            self.is_playing = True
            for listener in self.state_change_listeners:
                listener(self.is_playing)
                
        except Exception as e:
            print(f"Seek error: {e}")

    def toggle_shuffle(self):
        self.is_shuffle = not self.is_shuffle
        return self.is_shuffle

    def toggle_repeat(self):
        self.is_repeat = not self.is_repeat
        return self.is_repeat
