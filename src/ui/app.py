import flet as ft
from features.api.service import DeezerAPIService
from features.downloader.service import DeezloaderService
from features.downloader.utils import get_custom_music_folder

# Views
from ui.views import login_view, search_view, artist_view, album_view, playlist_view, settings_view, local_view, player_view
from ui.components import appbar
from ui.components.custom_titlebar import CustomTitleBar
from ui import theme
from features.player.player_manager import PlayerManager
from features.translations import Translator, AVAILABLE_LANGUAGES


APP_STATE = {
    "arl": None,
    "api": None,
    "downloader": None,
    "player_manager": None,
    "search_field_focused": False,  # Track if user is typing in a search field
    "titlebar": None,  # Reference to custom titlebar for controlling navigation visibility
    "translator": None,  # Translation manager for i18n
}

async def main(page: ft.Page):
    """Main entry point for the Flet application."""
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
    custom_titlebar = CustomTitleBar(page, APP_STATE)
    custom_titlebar.top = 0
    custom_titlebar.left = 0
    custom_titlebar.right = 0
    APP_STATE["titlebar"] = custom_titlebar  # Store reference for controlling navigation
    page.overlay.append(custom_titlebar)

    # Initialize MiniPlayer
    from ui.components.mini_player import MiniPlayer
    mini_player = MiniPlayer(page, APP_STATE)
    mini_player.bottom = 0
    mini_player.left = 0
    mini_player.right = 0
    page.overlay.append(mini_player)

    # Initialize Translator
    translator = Translator(default_language="en")
    APP_STATE["translator"] = translator
    
    # Load language preference from storage
    saved_language = await page.client_storage.get_async("app_language")
    if saved_language in AVAILABLE_LANGUAGES:
        translator.set_language(saved_language)

    # Attempt to load ARL from client_storage
    arl_token = await page.client_storage.get_async("arl_token")
    custom_music_path = await page.client_storage.get_async("music_folder_path")
    
    if arl_token:
        print("ARL token found in storage. Initializing services...")
        try:
            output_dir = get_custom_music_folder(custom_music_path)
            downloader = DeezloaderService(arl=arl_token, output_dir=output_dir)
            APP_STATE["arl"] = arl_token
            APP_STATE["api"] = DeezerAPIService()
            APP_STATE["downloader"] = downloader
            custom_titlebar.set_navigation_visible(True)  # Show navigation when logged in
            initial_route = "/search"
        except Exception as e:
            print(f"Error initializing services with saved ARL: {e}")
            await page.client_storage.remove_async("arl_token") # Remove invalid token
            custom_titlebar.set_navigation_visible(False)  # Hide navigation on login error
            initial_route = "/login"
    else:
        custom_titlebar.set_navigation_visible(False)  # Hide navigation on login screen
        initial_route = "/login"
    
    async def route_change(route):
        """Route change handler for navigation."""
        # print(f"DEBUG: route_change called. page.route={page.route}, views_count={len(page.views)}")
        # if page.views:
        #     print(f"DEBUG: Current views in stack: {[v.route for v in page.views]}")
        
        # Remove any views with None route (Flet creates these automatically sometimes)
        while page.views and page.views[0].route is None:
            page.views.pop(0)

        # Login View (initial route if no ARL)
        if page.route == "/login" or not APP_STATE.get("arl"):
            # Clear views when going to login to reset navigation stack
            page.views.clear()
            # Hide navigation buttons on login screen
            if APP_STATE.get("titlebar"):
                APP_STATE["titlebar"].set_navigation_visible(False)
            view = login_view.LoginView(APP_STATE)
            view.padding = ft.padding.only(top=40)  # Add padding for custom title bar
            page.views.append(view)
        # Main Views
        else:
            # Show navigation buttons when logged in
            if APP_STATE.get("titlebar"):
                APP_STATE["titlebar"].set_navigation_visible(True)
            
            # If the previous view was login, clear the stack to prevent going back to login
            if page.views and page.views[-1].route == "/login":
                page.views.clear()
            
            # Check if we're already on this route (e.g., back button was used)
            # If so, don't add a new view
            if page.views and page.views[-1].route == page.route:
                pass  # Already on this route, don't add new view
            else:
                # We're navigating to a new route, create and add the view
                view = None
                if page.route == "/search":
                    view = search_view.SearchView(APP_STATE)
                    view.padding = ft.padding.only(top=40)  # Add padding for custom title bar
                
                elif page.route.startswith("/artist"):
                    artist_id = page.route.split("/")[-1]
                    view = artist_view.ArtistView(APP_STATE, artist_id)
                    view.padding = ft.padding.only(top=40)  # Add padding for custom title bar

                elif page.route.startswith("/album"):
                    album_id = page.route.split("/")[-1]
                    view = album_view.AlbumView(APP_STATE, album_id)
                    view.padding = ft.padding.only(top=40)  # Add padding for custom title bar
                
                elif page.route.startswith("/playlist"):
                    playlist_id = page.route.split("/")[-1]
                    view = playlist_view.PlaylistView(APP_STATE, playlist_id)
                    view.padding = ft.padding.only(top=40)  # Add padding for custom title bar

                elif page.route == "/settings":
                    view = settings_view.SettingsView(APP_STATE)
                    view.padding = ft.padding.only(top=40)  # Add padding for custom title bar

                elif page.route == "/local":
                    view = local_view.LocalView(APP_STATE)
                    view.padding = ft.padding.only(top=40)  # Add padding for custom title bar

                elif page.route == "/player":
                    view = player_view.PlayerView(APP_STATE)
                    view.padding = ft.padding.only(top=40)  # Add padding for custom title bar

                # Add a fallback route or a 404 page
                else:
                    if not page.views:
                        view = search_view.SearchView(APP_STATE)
                        view.padding = ft.padding.only(top=40)  # Add padding for custom title bar
                
                if view:
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
        
        # Update back button visibility based on navigation stack
        if APP_STATE.get("titlebar"):
            APP_STATE["titlebar"].update_back_button()

    async def view_pop(view):
        """Handler for the 'back' button."""
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
        # Search fields set APP_STATE["search_field_focused"] via on_focus/on_blur events
        is_typing = APP_STATE.get("search_field_focused", False)

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
