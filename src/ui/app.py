import flet as ft
from features.api.service import DeezerAPIService
from features.downloader.service import DeezloaderService
from features.downloader.utils import get_custom_music_folder

# Importar vistas
from ui.views import login_view, search_view, artist_view, album_view, playlist_view, settings_view, local_view, player_view
from ui.components import appbar
from ui.components.custom_titlebar import CustomTitleBar
from ui import theme
from features.player.player_manager import PlayerManager

# Un diccionario simple para mantener el estado de la aplicación
APP_STATE = {
    "arl": None,
    "api": None,
    "downloader": None,
    "player_manager": None,
}

async def main(page: ft.Page):
    """Punto de entrada principal de la aplicación Flet."""
    page.title = "Deeztracker"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = theme.BG_COLOR
    page.window_width = 400
    page.window_height = 890  # 850 (original) + 40 (title bar)
    page.window_resizable = True
    page.window_min_width = 400
    page.window_min_height = 600
    
    import platform
    # Hide native title bar and use custom one, unless on Linux where we need it for resizing
    if platform.system() == "Linux":
        page.window.title_bar_hidden = False
    else:
        page.window.title_bar_hidden = True

    # Initialize PlayerManager
    player_manager = PlayerManager(page)
    APP_STATE["player_manager"] = player_manager

    # Initialize Custom Title Bar
    custom_titlebar = CustomTitleBar(page)
    custom_titlebar.top = 0
    custom_titlebar.left = 0
    custom_titlebar.right = 0
    page.overlay.append(custom_titlebar)

    # Initialize MiniPlayer
    from ui.components.mini_player import MiniPlayer
    mini_player = MiniPlayer(page, APP_STATE)
    mini_player.bottom = 0
    mini_player.left = 0
    mini_player.right = 0
    page.overlay.append(mini_player)

    # Intentar cargar ARL de client_storage
    arl_token = await page.client_storage.get_async("arl_token")
    custom_music_path = await page.client_storage.get_async("music_folder_path")
    
    if arl_token:
        print("ARL token encontrado en storage. Inicializando servicios...")
        try:
            output_dir = get_custom_music_folder(custom_music_path)
            downloader = DeezloaderService(arl=arl_token, output_dir=output_dir)
            APP_STATE["arl"] = arl_token
            APP_STATE["api"] = DeezerAPIService()
            APP_STATE["downloader"] = downloader
            initial_route = "/search"
        except Exception as e:
            print(f"Error al inicializar servicios con ARL guardado: {e}")
            await page.client_storage.remove_async("arl_token") # Eliminar token inválido
            initial_route = "/login"
    else:
        initial_route = "/login"
    
    async def route_change(route):
        """Manejador de cambio de ruta para la navegación."""
        print(f"Cambiando a la ruta: {page.route}")
        page.views.clear()

        # Vista de Login (ruta inicial si no hay ARL)
        if page.route == "/login" or not APP_STATE.get("arl"):
            view = login_view.LoginView(APP_STATE)
            view.padding = ft.padding.only(top=40)  # Add padding for custom title bar
            page.views.append(view)        
        # Vistas principales de la app
        else:
            if page.route == "/search":
                view = search_view.SearchView(APP_STATE)
                view.padding = ft.padding.only(top=40)  # Add padding for custom title bar
                page.views.append(view)
            
            elif page.route.startswith("/artist"):
                artist_id = page.route.split("/")[-1]
                view = artist_view.ArtistView(APP_STATE, artist_id)
                view.padding = ft.padding.only(top=40)  # Add padding for custom title bar
                page.views.append(view)

            elif page.route.startswith("/album"):
                album_id = page.route.split("/")[-1]
                view = album_view.AlbumView(APP_STATE, album_id)
                view.padding = ft.padding.only(top=40)  # Add padding for custom title bar
                page.views.append(view)
            
            elif page.route.startswith("/playlist"):
                playlist_id = page.route.split("/")[-1]
                view = playlist_view.PlaylistView(APP_STATE, playlist_id)
                view.padding = ft.padding.only(top=40)  # Add padding for custom title bar
                page.views.append(view)

            elif page.route == "/settings":
                view = settings_view.SettingsView(APP_STATE)
                view.padding = ft.padding.only(top=40)  # Add padding for custom title bar
                page.views.append(view)

            elif page.route == "/local":
                view = local_view.LocalView(APP_STATE)
                view.padding = ft.padding.only(top=40)  # Add padding for custom title bar
                page.views.append(view)

            elif page.route == "/player":
                view = player_view.PlayerView(APP_STATE)
                view.padding = ft.padding.only(top=40)  # Add padding for custom title bar
                page.views.append(view)

            # Añadir una ruta de fallback o una página 404
            else:
                 if not page.views:
                    view = search_view.SearchView(APP_STATE)
                    view.padding = ft.padding.only(top=40)  # Add padding for custom title bar
                    page.views.append(view)
        
        page.update()

        # Update MiniPlayer visibility
        if "player_manager" in APP_STATE and APP_STATE["player_manager"].current_index != -1:
            for control in page.overlay:
                if isinstance(control, MiniPlayer):
                    if page.route == "/player":
                        control.visible = False
                    else:
                        control.visible = True
                    control.update()
                    break

    async def view_pop(view):
        """Manejador para el botón de 'atrás'."""
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    def on_keyboard(e: ft.KeyboardEvent):
        if not APP_STATE["player_manager"]:
            return

        # Check if user is typing in a text field - if so, ignore keyboard shortcuts
        # (except for media keys which should always work)
        is_typing = False
        try:
            # Check if there's a focused control that's a TextField
            if page.views and len(page.views) > 0:
                current_view = page.views[-1]
                # Recursively check for focused TextFields
                def check_focused_textfield(control):
                    if isinstance(control, ft.TextField):
                        # TextField is considered focused if it has autofocus or if it's the active element
                        return True
                    if hasattr(control, 'controls'):
                        for child in control.controls:
                            if check_focused_textfield(child):
                                return True
                    if hasattr(control, 'content') and control.content:
                        if check_focused_textfield(control.content):
                            return True
                    return False
                
                # For simplicity, we'll check if the current route is /search
                # and if certain keys are pressed, we assume user might be typing
                if page.route == "/search" and e.key == " ":
                    # Spacebar in search view - likely typing
                    is_typing = True
        except:
            pass

        # Media keys should always work, even when typing
        if e.key == "MediaPlayPause":
            APP_STATE["player_manager"].toggle_play_pause()
            return
        elif e.key == "MediaTrackNext":
            APP_STATE["player_manager"].next_track()
            return
        elif e.key == "MediaTrackPrevious":
            APP_STATE["player_manager"].prev_track()
            return
        elif e.key == "AudioVolumeMute":
            # Simple mute toggle: if > 0 set to 0, else set to 0.5 (or previous if we tracked it)
            if APP_STATE["player_manager"].volume > 0:
                APP_STATE["player_manager"].set_volume(0)
            else:
                APP_STATE["player_manager"].set_volume(0.5) # Default un-mute volume
            return
        elif e.key == "AudioVolumeUp":
            current_vol = APP_STATE["player_manager"].volume
            new_vol = min(1.0, current_vol + 0.05)
            APP_STATE["player_manager"].set_volume(new_vol)
            return
        elif e.key == "AudioVolumeDown":
            current_vol = APP_STATE["player_manager"].volume
            new_vol = max(0.0, current_vol - 0.05)
            APP_STATE["player_manager"].set_volume(new_vol)
            return

        # If user is typing, ignore regular keyboard shortcuts
        if is_typing:
            return

        # Regular keyboard shortcuts
        if e.key == "ArrowUp":
            current_vol = APP_STATE["player_manager"].volume
            new_vol = min(1.0, current_vol + 0.05)
            APP_STATE["player_manager"].set_volume(new_vol)
        elif e.key == "ArrowDown":
            current_vol = APP_STATE["player_manager"].volume
            new_vol = max(0.0, current_vol - 0.05)
            APP_STATE["player_manager"].set_volume(new_vol)
        elif e.key == " ":  # Spacebar
            APP_STATE["player_manager"].toggle_play_pause()
        elif e.key == "ArrowRight":  # Next track
            APP_STATE["player_manager"].next_track()
        elif e.key == "ArrowLeft":  # Previous track
            APP_STATE["player_manager"].prev_track()

    page.on_keyboard_event = on_keyboard
    
    page.go(initial_route)
