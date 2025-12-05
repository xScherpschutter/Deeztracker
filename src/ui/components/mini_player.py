import flet as ft
from ui import theme

class MiniPlayer(ft.Container):
    def __init__(self, page: ft.Page, app_state):
        super().__init__()
        self.page = page
        self.app_state = app_state
        self.player_manager = app_state["player_manager"]
        
        self.visible = False # Hidden by default until a track is loaded
        self.bgcolor = theme.CONTENT_BG
        self.padding = 10
        self.border_radius = ft.border_radius.only(top_left=15, top_right=15)
        self.height = 80
        self.on_click = self.open_full_player
        
        # UI Elements
        self.track_title = ft.Text("", weight=ft.FontWeight.BOLD, size=14, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
        self.artist_name = ft.Text("", size=12, color=theme.SECONDARY_TEXT, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
        self.cover_image = ft.Image(src="https://via.placeholder.com/50", width=50, height=50, fit=ft.ImageFit.COVER, border_radius=5)
        
        self.play_pause_btn = ft.IconButton(
            icon=ft.Icons.PLAY_ARROW,
            icon_color=theme.PRIMARY_TEXT,
            on_click=self.toggle_play_pause
        )
        
        self.content = ft.Row(
            [
                self.cover_image,
                ft.Column(
                    [
                        self.track_title,
                        self.artist_name
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=2,
                    expand=True
                ),
                self.play_pause_btn
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        
        # Register callbacks
        self.player_manager.subscribe(
            on_track_change=self.on_track_change,
            on_state_change=self.on_state_change
        )

    def on_track_change(self, track):
        self.track_title.value = track.get('title', 'Desconocido')
        self.artist_name.value = track.get('artist', 'Desconocido')
        
        # Use cover if exists and not empty, otherwise placeholder
        cover = track.get('cover', '')
        if cover and cover.strip():
            self.cover_image.src = cover
        else:
            self.cover_image.src = "https://via.placeholder.com/50"
        
        # Only show if not on player view
        if self.page.route != "/player":
            self.visible = True
        else:
            self.visible = False
            
        self.play_pause_btn.icon = ft.Icons.PAUSE
        self.update()

    def on_state_change(self, is_playing):
        self.play_pause_btn.icon = ft.Icons.PAUSE if is_playing else ft.Icons.PLAY_ARROW
        self.update()

    def toggle_play_pause(self, e):
        e.control.icon = ft.Icons.PLAY_ARROW if self.player_manager.is_playing else ft.Icons.PAUSE
        self.player_manager.toggle_play_pause()
        self.update()

    def open_full_player(self, e):
        # Prevent opening if clicking the button (handled by button's on_click, but event propagation might need check)
        # In Flet, button click usually stops propagation if handled.
        self.page.go("/player")
