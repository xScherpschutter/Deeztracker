"""
Linux MPRIS Backend
Implements the MPRIS v2 specification for Linux media control integration.
"""
import threading
import time
import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib
import subprocess

# MPRIS Interfaces
MPRIS_PREFIX = "org.mpris.MediaPlayer2"
MPRIS_PLAYER_PREFIX = "org.mpris.MediaPlayer2.Player"
PROPERTIES_PREFIX = "org.freedesktop.DBus.Properties"

class DeezTrackerMPRIS(dbus.service.Object):
    """
    DBus object implementing MPRIS v2 interfaces.
    """
    def __init__(self, bus, player_manager):
        self.player_manager = player_manager
        bus_name = dbus.service.BusName(f"{MPRIS_PREFIX}.deeztracker", bus)
        super().__init__(bus_name, "/org/mpris/MediaPlayer2")
        
        self._metadata = dbus.Dictionary({
            "mpris:trackid": dbus.ObjectPath("/org/mpris/MediaPlayer2/TrackList/NoTrack"),
            "mpris:length": dbus.Int64(0),
            "mpris:artUrl": "",
            "xesam:title": "DeezTracker",
            "xesam:artist": dbus.Array(["Unknown"], signature='s'),
            "xesam:album": "",
        }, signature='sv')

    # --- org.freedesktop.DBus.Properties Interface ---

    @dbus.service.method(PROPERTIES_PREFIX, in_signature='ss', out_signature='v')
    def Get(self, interface_name, property_name):
        return self.GetAll(interface_name)[property_name]

    @dbus.service.method(PROPERTIES_PREFIX, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface_name):
        if interface_name == MPRIS_PREFIX:
            return {
                "CanQuit": False,
                "CanRaise": False,
                "HasTrackList": False,
                "Identity": "DeezTracker",
                "DesktopEntry": "deeztracker",
                "SupportedUriSchemes": dbus.Array(["file", "http", "https"], signature='s'),
                "SupportedMimeTypes": dbus.Array(["audio/mpeg", "audio/x-wav", "audio/flac"], signature='s'),
            }
        elif interface_name == MPRIS_PLAYER_PREFIX:
            status = "Stopped"
            loop_status = "None"
            shuffle = False
            volume = 1.0
            position = dbus.Int64(0)
            
            if self.player_manager:
                status = "Playing" if self.player_manager.is_playing else "Paused"
                loop_status = "Playlist" if self.player_manager.is_repeat else "None"
                shuffle = self.player_manager.is_shuffle
                # Volume
                if self.player_manager.player:
                     try:
                        volume = self.player_manager.player.audio_get_volume() / 100.0
                     except:
                        pass
                # Position
                position = dbus.Int64(self.player_manager.position * 1000)

            return {
                "PlaybackStatus": status,
                "LoopStatus": loop_status,
                "Volume": volume,
                "Shuffle": shuffle,
                "Metadata": self._metadata,
                "Position": position,
                "Rate": 1.0,
                "MinimumRate": 1.0,
                "MaximumRate": 1.0,
                "CanGoNext": True,
                "CanGoPrevious": True,
                "CanPlay": True,
                "CanPause": True,
                "CanSeek": False,
                "CanControl": True,
            }
        else:
            raise dbus.exceptions.DBusException(
                'org.freedesktop.DBus.Error.UnknownInterface',
                'The interface ' + interface_name + ' is not supported')

    @dbus.service.method(PROPERTIES_PREFIX, in_signature='ssv')
    def Set(self, interface_name, property_name, new_value):
        if interface_name == MPRIS_PLAYER_PREFIX:
            if property_name == "LoopStatus":
                # new_value is a dbus string variant
                val = str(new_value)
                if self.player_manager:
                     current = "Playlist" if self.player_manager.is_repeat else "None"
                     if val != current:
                        self.player_manager.page.run_task(self._async_toggle_repeat)
            elif property_name == "Shuffle":
                val = bool(new_value)
                if self.player_manager and self.player_manager.is_shuffle != val:
                    self.player_manager.page.run_task(self._async_toggle_shuffle)
            elif property_name == "Volume":
                val = float(new_value)
                if self.player_manager:
                    self.player_manager.set_volume(val)
                    self.PropertiesChanged(MPRIS_PLAYER_PREFIX, {"Volume": val}, [])
        else:
            raise dbus.exceptions.DBusException(
                'org.freedesktop.DBus.Error.UnknownInterface',
                'The interface ' + interface_name + ' is not supported')

    # --- org.mpris.MediaPlayer2 Interface ---

    @dbus.service.method(MPRIS_PREFIX, out_signature="s")
    def Raise(self):
        pass

    @dbus.service.method(MPRIS_PREFIX, out_signature="")
    def Quit(self):
        pass

    # --- org.mpris.MediaPlayer2.Player Interface ---

    @dbus.service.method(MPRIS_PLAYER_PREFIX)
    def Next(self):
        if self.player_manager:
            self.player_manager.page.run_task(self._async_next)

    async def _async_next(self):
        self.player_manager.next_track()

    @dbus.service.method(MPRIS_PLAYER_PREFIX)
    def Previous(self):
        if self.player_manager:
            self.player_manager.page.run_task(self._async_prev)

    async def _async_prev(self):
        self.player_manager.prev_track()

    @dbus.service.method(MPRIS_PLAYER_PREFIX)
    def Pause(self):
        if self.player_manager and self.player_manager.is_playing:
            self.player_manager.page.run_task(self._async_toggle)

    @dbus.service.method(MPRIS_PLAYER_PREFIX)
    def PlayPause(self):
        if self.player_manager:
            self.player_manager.page.run_task(self._async_toggle)

    async def _async_toggle(self):
        self.player_manager.toggle_play_pause()

    @dbus.service.method(MPRIS_PLAYER_PREFIX)
    def Stop(self):
        if self.player_manager and self.player_manager.is_playing:
            self.player_manager.page.run_task(self._async_toggle)

    @dbus.service.method(MPRIS_PLAYER_PREFIX)
    def Play(self):
        if self.player_manager and not self.player_manager.is_playing:
            self.player_manager.page.run_task(self._async_toggle)

    @dbus.service.method(MPRIS_PLAYER_PREFIX, in_signature="x")
    def Seek(self, offset):
        pass

    @dbus.service.method(MPRIS_PLAYER_PREFIX, in_signature="ox")
    def SetPosition(self, track_id, position):
        pass

    @dbus.service.method(MPRIS_PLAYER_PREFIX, in_signature="s")
    def OpenUri(self, uri):
        pass

    # --- Signals ---
    
    @dbus.service.signal(PROPERTIES_PREFIX, signature="sa{sv}as")
    def PropertiesChanged(self, interface_name, changed_properties, invalidated_properties):
        pass

    # --- Helper methods ---

    def update_metadata_signal(self, track):
        """Update internal metadata and emit PropertiesChanged signal"""
        new_meta = dbus.Dictionary({
            "mpris:trackid": dbus.ObjectPath(f"/org/mpris/MediaPlayer2/TrackList/{int(time.time())}"),
            "mpris:length": dbus.Int64(self.player_manager.duration * 1000000),
            "xesam:title": track.get('title', 'Unknown'),
            "xesam:artist": dbus.Array([track.get('artist', 'Unknown')], signature='s'),
            "xesam:album": track.get('album', ''),
        }, signature='sv')
        
        # Handle cover art
        cover = track.get('cover')
        if cover:
            if not cover.startswith('http') and not cover.startswith('file://'):
                 # Ensure absolute path for local files
                import os
                if not os.path.isabs(cover):
                     pass # Assume absolute or let it be
                new_meta["mpris:artUrl"] = f"file://{cover}" if not cover.startswith('file://') else cover
            else:
                new_meta["mpris:artUrl"] = cover
        
        self._metadata = new_meta
        self.PropertiesChanged(MPRIS_PLAYER_PREFIX, {"Metadata": self._metadata}, [])

    def update_playback_status_signal(self, is_playing):
        status = "Playing" if is_playing else "Paused"
        self.PropertiesChanged(MPRIS_PLAYER_PREFIX, {"PlaybackStatus": status}, [])
    
    # Async helpers for property setters
    async def _async_toggle_repeat(self):
        self.player_manager.toggle_repeat()
        self.PropertiesChanged(MPRIS_PLAYER_PREFIX, {"LoopStatus": "Playlist" if self.player_manager.is_repeat else "None"}, [])

    async def _async_toggle_shuffle(self):
        self.player_manager.toggle_shuffle()
        self.PropertiesChanged(MPRIS_PLAYER_PREFIX, {"Shuffle": self.player_manager.is_shuffle}, [])


class MPRISBackend:
    """
    Manages the DBus connection and GLib MainLoop for MPRIS.
    """
    def __init__(self, player_manager):
        self.player_manager = player_manager
        self.loop = None
        self.loop_thread = None
        self.mpris_obj = None
        self.bus = None
        
        try:
            # Initialize DBus GMainLoop
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            self.bus = dbus.SessionBus()
            
            # Create MPRIS object
            self.mpris_obj = DeezTrackerMPRIS(self.bus, player_manager)
            
            # Start GLib MainLoop in a separate thread
            self.loop = GLib.MainLoop()
            self.loop_thread = threading.Thread(target=self.loop.run, daemon=True)
            self.loop_thread.start()
            
        except Exception as e:
            print(f"Failed to initialize MPRIS backend: {e}")

    def update_metadata(self, track: dict):
        if self.mpris_obj:
            try:
                self.mpris_obj.update_metadata_signal(track)
                
                # Explicit notification using notify-send
                self._send_notification(track)
            except Exception as e:
                print(f"Error updating MPRIS metadata: {e}")

    def _send_notification(self, track: dict):
        """Send a system notification using notify-send"""
        try:
            title = track.get('title', 'Unknown Title')
            artist = track.get('artist', 'Unknown Artist')
            cover = track.get('cover')
            
            cmd = [
                "notify-send",
                "🎵 Now Playing",
                f"{title}\n{artist}",
                "-a", "DeezTracker",
                "-t", "3000"
            ]
            
            # Add icon if available
            if cover:
                # If it's a local file URL, convert to path
                if cover.startswith('file://'):
                    cover_path = cover[7:]
                    cmd.extend(["-i", cover_path])
                elif not cover.startswith('http'):
                    # Assume absolute path
                    cmd.extend(["-i", cover])
                else:
                    # For http URLs, we might use a default icon or download it (skipping download for now)
                    cmd.extend(["-i", "audio-player"])
            else:
                cmd.extend(["-i", "audio-player"])
                
            subprocess.run(cmd, check=False)
            
        except Exception as e:
            print(f"Error sending notification: {e}")

    def update_playback_state(self, is_playing: bool):
        if self.mpris_obj:
            try:
                self.mpris_obj.update_playback_status_signal(is_playing)
            except Exception as e:
                print(f"Error updating MPRIS status: {e}")

    def cleanup(self):
        if self.loop:
            self.loop.quit()
        if self.mpris_obj:
            self.mpris_obj.remove_from_connection()
