import flet as ft
from ui import theme

class SettingsView(ft.View):
    def __init__(self, app_state):
        super().__init__(route="/settings", bgcolor=theme.BG_COLOR, scroll=ft.ScrollMode.ADAPTIVE)
        self.app_state = app_state
        self.format_mapper = {
            "flac": "FLAC",
            "mp3-320": "MP3_320",
            "mp3-128": "MP3_128"
        }
        
        # Download Format Selection
        self.format_dropdown = ft.Dropdown(
            label="Formato de Descarga",
            width=200,
            options=[
                ft.dropdown.Option("flac"),
                ft.dropdown.Option("mp3-320"),
                ft.dropdown.Option("mp3-128"),
            ],
            value="mp3-320",
            on_change=self.save_format_preference,
            border_color=theme.ACCENT_COLOR,
            color=theme.PRIMARY_TEXT,
        )

        self.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text("Configuración", size=24, weight=ft.FontWeight.BOLD, color=theme.PRIMARY_TEXT),
                    ft.Divider(color=theme.ACCENT_COLOR),
                    
                    ft.Text("Descargas", size=18, weight=ft.FontWeight.BOLD, color=theme.PRIMARY_TEXT),
                    self.format_dropdown,
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=theme.SECONDARY_TEXT),
                            ft.Text(
                                "Nota: La conversión a FLAC solo está disponible \nsi se tiene FFmpeg instalado, de lo contrario será MP3.",
                                size=12,
                                color=theme.SECONDARY_TEXT,
                            ),
                        ], spacing=8),
                        padding=ft.padding.only(top=5),
                    ),
                    ft.Divider(color=theme.SECONDARY_TEXT),

                    ft.Text("Sesión", size=18, weight=ft.FontWeight.BOLD, color=theme.PRIMARY_TEXT),
                    ft.ElevatedButton(
                        "Cerrar Sesión", 
                        on_click=self.logout,
                        bgcolor=theme.ERROR_COLOR,
                        color=ft.Colors.WHITE
                    ),

                ], spacing=20),
                padding=ft.padding.only(left=20, top=20, right=20, bottom=100),
                expand=True
            )
        ]
        
    def did_mount(self):
        self.page.run_task(self.load_preferences)

    async def load_preferences(self):
        saved_format = await self.page.client_storage.get_async("download_format")
        if saved_format:
            self.format_dropdown.value = saved_format
            self.update()

    async def save_format_preference(self, e):
        music_format = self.format_dropdown.value
        await self.page.client_storage.set_async("download_format", music_format)
        await self.page.client_storage.set_async("download_quality", self.format_mapper.get(music_format, "FLAC"))
        print(f"Formato de descarga guardado: {self.format_mapper.get(music_format, 'FLAC')}")

    async def logout(self, e):
        # Stop player and clear playlist
        if "player_manager" in self.app_state and self.app_state["player_manager"]:
            player_manager = self.app_state["player_manager"]
            player_manager._stop_position_updates()
            if player_manager.playback.active:
                player_manager.playback.stop()
            player_manager.is_playing = False
            player_manager.playlist = []
            player_manager.current_index = -1
        
        # Hide mini player
        from ui.components.mini_player import MiniPlayer
        for control in self.page.overlay:
            if isinstance(control, MiniPlayer):
                control.visible = False
                control.update()
                break
        
        # Clear session data
        await self.page.client_storage.remove_async("arl_token")
        self.app_state["arl"] = None
        self.app_state["api"] = None
        self.app_state["downloader"] = None
        self.page.go("/login")
