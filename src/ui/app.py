import flet as ft
from features.api.service import DeezerAPIService
from features.downloader.service import DeezloaderService

# Importar vistas
from ui.views import login_view, search_view, artist_view, album_view, playlist_view, settings_view, local_view, player_view
from ui.components import appbar
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
    page.window_height = 850
    page.window_resizable = False

    # Initialize PlayerManager
    player_manager = PlayerManager(page)
    APP_STATE["player_manager"] = player_manager

    # Initialize MiniPlayer
    from ui.components.mini_player import MiniPlayer
    mini_player = MiniPlayer(page, APP_STATE)
    mini_player.bottom = 0
    mini_player.left = 0
    mini_player.right = 0
    page.overlay.append(mini_player)

    # Intentar cargar ARL de client_storage
    arl_token = await page.client_storage.get_async("arl_token")
    if arl_token:
        print("ARL token encontrado en storage. Inicializando servicios...")
        try:
            downloader = DeezloaderService(arl=arl_token)
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
            # La vista de login no tiene AppBar
            page.views.append(view)        
        # Vistas principales de la app
        else:
            if page.route == "/search":
                view = search_view.SearchView(APP_STATE)
                view.appbar = appbar.CustomAppBar(title="Buscar", page=page)
                page.views.append(view)
            
            elif page.route.startswith("/artist"):
                artist_id = page.route.split("/")[-1]
                view = artist_view.ArtistView(APP_STATE, artist_id)
                view.appbar = appbar.CustomAppBar(title="Artista", page=page)
                page.views.append(view)

            elif page.route.startswith("/album"):
                album_id = page.route.split("/")[-1]
                view = album_view.AlbumView(APP_STATE, album_id)
                view.appbar = appbar.CustomAppBar(title="Álbum", page=page)
                page.views.append(view)
            
            elif page.route.startswith("/playlist"):
                playlist_id = page.route.split("/")[-1]
                view = playlist_view.PlaylistView(APP_STATE, playlist_id)
                view.appbar = appbar.CustomAppBar(title="Playlist", page=page)
                page.views.append(view)

            elif page.route == "/settings":
                view = settings_view.SettingsView(APP_STATE)
                view.appbar = appbar.CustomAppBar(title="Configuración", page=page)
                page.views.append(view)

            elif page.route == "/local":
                view = local_view.LocalView(APP_STATE)
                view.appbar = appbar.CustomAppBar(title="Música Local", page=page)
                page.views.append(view)

            elif page.route == "/player":
                view = player_view.PlayerView(APP_STATE)
                page.views.append(view)

            # Añadir una ruta de fallback o una página 404
            else:
                 if not page.views:
                    view = search_view.SearchView(APP_STATE)
                    view.appbar = appbar.CustomAppBar(title="Buscar", page=page)
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
    
    # Iniciar en la ruta inicial determinada
    page.go(initial_route)
