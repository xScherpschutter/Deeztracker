# Deeztracker

Deeztracker app.

## Packaging

### Linux

#### System Dependencies

To package the application on Linux, ensure you have the following system dependencies installed (names may vary by distribution, these are for Debian/Ubuntu):

- `vlc`
- `libvlc-dev`
- `libgirepository1.0-dev`
- `libcairo2-dev`
- `libdbus-1-dev`
- `libdbus-glib-1-dev`
- `pkg-config`
- `python3-dev`
- `gir1.2-gtk-3.0`

#### Build Command

```bash
uv run flet pack src/main.py \
  -i assets/icon_windows.png \
  --name Deeztracker \
  --debug-console DEBUG_CONSOLE \
  --add-binary "/usr/lib/x86_64-linux-gnu/libvlc.so.5:." \
  --add-binary "/usr/lib/x86_64-linux-gnu/libvlccore.so.9:." \
  --add-data "/usr/lib/x86_64-linux-gnu/girepository-1.0:girepository-1.0" \
  --add-data "/usr/lib/x86_64-linux-gnu/vlc/plugins:vlc_plugins" \
  --hidden-import "gi" \
  --hidden-import "gi.repository.GLib" \
  --hidden-import "dbus.mainloop.glib" \
  -y
```

### Windows

#### Build Command

```powershell
uv run flet pack src/main.py -i assets/icon_windows.png --name "Deeztracker" --product-name "Deeztracker" --file-version "0.0.1" -y
```
