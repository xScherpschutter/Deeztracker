# mpris_notifier.py
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
import subprocess

DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()

def on_properties_changed(interface, changed, invalidated):
    if interface == "org.mpris.MediaPlayer2.Player":
        if "Metadata" in changed:
            metadata = changed["Metadata"]
            title = metadata.get("xesam:title", "Unknown")
            artists = metadata.get("xesam:artist", ["Unknown"])
            artist = artists[0] if artists else "Unknown"
            
            # Notificación
            subprocess.run([
                "notify-send",
                "🎵 Now Playing",
                f"{title}\n{artist}",
                "-i", "audio-player",
                "-t", "3000"
            ])

bus.add_signal_receiver(
    on_properties_changed,
    signal_name="PropertiesChanged",
    dbus_interface="org.freedesktop.DBus.Properties",
    bus_name="org.mpris.MediaPlayer2.deeztracker",
    path="/org/mpris/MediaPlayer2"
)

print("Listening for MPRIS notifications...")
loop = GLib.MainLoop()
loop.run()