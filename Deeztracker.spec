# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[('/usr/lib/x86_64-linux-gnu/libvlc.so.5', '.'), ('/usr/lib/x86_64-linux-gnu/libvlccore.so.9', '.'), ('/usr/lib/x86_64-linux-gnu/librsvg-2.so.2', '.'), ('/usr/lib/x86_64-linux-gnu/gdk-pixbuf-2.0/2.10.0/loaders/libpixbufloader-svg.so', 'gdk-pixbuf-2.0/2.10.0/loaders')],
    datas=[('/usr/lib/x86_64-linux-gnu/girepository-1.0', 'girepository-1.0'), ('/usr/lib/x86_64-linux-gnu/vlc/plugins', 'vlc_plugins'), ('assets', 'assets')],
    hiddenimports=['gi', 'gi.repository.GLib', 'dbus.mainloop.glib'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Deeztracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon_windows.png'],
)
