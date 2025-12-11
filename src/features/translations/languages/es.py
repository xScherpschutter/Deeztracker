"""
Spanish translations for Deeztracker.
"""

translations = {
    # Cadenas comunes usadas en toda la aplicación
    "common": {
        "unknown": "Desconocido",
        "loading": "Cargando...",
        "error": "Error",
        "search": "Buscar",
        "settings": "Configuración",
        "close": "Cerrar",
        "minimize": "Minimizar",
        "maximize": "Maximizar",
        "back": "Atrás",
        "artist": "Artista",
    },
    
    # Vista de inicio de sesión
    "login": {
        "title": "Deeztracker",
        "subtitle": "Inicia sesión con tu ARL Token",
        "arl_label": "Token ARL de Deezer",
        "button": "Iniciar Sesión",
        "error_empty": "Por favor, introduce un token ARL.",
        "error_invalid": "Token ARL inválido o error de conexión.",
    },
    
    # Vista de búsqueda
    "search": {
        "title": "Descubre tu música favorita",
        "hint": "Busca un artista, álbum, canción...",
        "subtitle": "Busca artistas, álbumes, canciones o playlists",
        "searching": "Buscando...",
        "no_results": "No se encontraron resultados.",
        "error": "Error al realizar la búsqueda.",
        "load_more": "Cargar más",
        "loading_more": "Cargando...",
        "tip_search": "Escribe en la barra superior",
        "tip_tabs": "Selecciona el tipo de búsqueda",
        "tip_download": "Descarga tus canciones favoritas",
        "tab_artist": "Artista",
        "tab_album": "Álbum",
        "tab_song": "Canción",
        "tab_playlist": "Playlist",
        "error_download": "Error al descargar '{title}': {error}",
        "download_started": "Iniciando descarga de '{title}'...",
        "download_success": "'{title}' descargado con éxito!",
    },
    
    # Vista de música local
    "local": {
        "title": "Encuentra tu música",
        "system": "Sistema",
        "hint_search": "Buscar en música local...",
        "tooltip_refresh": "Reescanear música",
        "scanning": "Escaneando archivos de música...",
        "scanning_dirs": "Escaneando {count} directorios...",
        "total_files": "Total: {count} archivos encontrados",
        "no_files": "No se encontraron archivos de música.",
        "no_files_help": "Los archivos deben estar en las carpetas de Música del sistema.",
    },
    
    # Vista de artista
    "artist": {
        "loading": "Cargando...",
        "fans": "{count} fans",
        "albums": "Álbumes",
        "top_tracks": "Top Canciones",
        "error_loading": "Error al cargar datos del artista.",
        "error_download": "Error al descargar '{title}': {error}",
        "download_started": "Iniciando descarga de '{title}'...",
        "download_success": "'{title}' descargado con éxito!",
    },
    
    # Vista de álbum
    "album": {
        "loading": "Cargando...",
        "button_download": "Descargar Álbum Completo",
        "error_loading": "Error al cargar datos del álbum.",
        "download_started": "Iniciando descarga de álbum '{title}'...",
        "download_success": "Álbum '{title}' descargado con éxito!",
        "error_download_album": "Error descargando álbum '{title}': {error}",
        "download_track_started": "Iniciando descarga de '{title}'...",
        "download_track_success": "'{title}' descargado con éxito!",
        "error_download_track": "Error descargando '{title}': {error}",
    },
    
    # Vista de playlist
    "playlist": {
        "loading": "Cargando...",
        "button_download": "Descargar Playlist Completa",
        "not_found": "Playlist no encontrada",
        "error_loading": "Error al cargar datos de la playlist.",
        "download_started": "Iniciando descarga de playlist '{title}'...",
        "download_success": "Playlist '{title}' descargada con éxito!",
        "error_download_playlist": "Error al descargar playlist '{title}': {error}",
        "download_track_started": "Iniciando descarga de '{title}'...",
        "download_track_success": "'{title}' descargado con éxito!",
        "error_download_track": "Error al descargar '{title}': {error}",
    },
    
    # Vista de configuración
    "settings": {
        "title": "Configuración",
        "downloads": "Descargas",
        "download_format": "Formato de Descarga",
        "format_note": "Nota: La conversión a FLAC solo está disponible\\nsi se tiene FFmpeg instalado, de lo contrario será MP3.",
        "music_folder": "Carpeta de Música",
        "current_path": "Ruta actual:",
        "button_change": "Cambiar Carpeta",
        "button_restore": "Restaurar",
        "folder_note": "Esta carpeta se usará para guardar las descargas\\ny para buscar música local.",
        "session": "Sesión",
        "button_logout": "Cerrar Sesión",
        "language": "Idioma",
        "language_english": "English",
        "language_spanish": "Español",
    },
    
    # Tooltips de la barra de título
    "titlebar": {
        "minimize": "Minimizar",
        "maximize": "Maximizar",
        "close": "Cerrar",
        "back": "Atrás",
        "search": "Buscar",
        "local_music": "Música Local",
        "settings": "Configuración",
    },
    
    # Tooltips de AppBar
    "appbar": {
        "search": "Buscar",
        "local_music": "Música Local",
        "settings": "Configuración",
    },
    
    # Reproductor mini
    "mini_player": {
        "unknown_title": "Desconocido",
        "unknown_artist": "Desconocido",
    },
    
    # Vista del reproductor
    "player": {
        "unknown_title": "Desconocido",
        "unknown_artist": "Desconocido",
    },
}
