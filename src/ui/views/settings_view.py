import flet as ft
from ui import theme
from features.downloader.utils import get_deeztracker_music_folder

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

        self.music_path_text = ft.Text(
            get_deeztracker_music_folder(),
            size=12,
            color=theme.SECONDARY_TEXT,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        self.folder_picker = ft.FilePicker(on_result=self.folder_picker_result)

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

                    # Music Path Configuration Section
                    ft.Text("Carpeta de Música", size=18, weight=ft.FontWeight.BOLD, color=theme.PRIMARY_TEXT),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Ruta actual:", size=14, color=theme.PRIMARY_TEXT),
                            self.music_path_text,
                            ft.Row([
                                ft.ElevatedButton(
                                    "Cambiar Carpeta",
                                    icon=ft.Icons.FOLDER_OPEN,
                                    on_click=lambda _: self.folder_picker.get_directory_path(
                                        dialog_title="Seleccionar carpeta de música"
                                    ),
                                    bgcolor=theme.ACCENT_COLOR,
                                    color=ft.Colors.WHITE,
                                ),
                                ft.TextButton(
                                    "Restaurar",
                                    icon=ft.Icons.RESTORE,
                                    on_click=self.reset_music_path,
                                ),
                            ], spacing=10),
                        ], spacing=10),
                        padding=ft.padding.only(top=5),
                    ),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=theme.SECONDARY_TEXT),
                            ft.Text(
                                "Esta carpeta se usará para guardar las descargas\ny para buscar música local.",
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
        # Add FilePicker to overlay
        self.page.overlay.append(self.folder_picker)
        self.page.update()
        self.page.run_task(self.load_preferences)

    async def load_preferences(self):
        saved_format = await self.page.client_storage.get_async("download_format")
        if saved_format:
            self.format_dropdown.value = saved_format
        
        # Load saved music path
        saved_path = await self.page.client_storage.get_async("music_folder_path")
        if saved_path:
            self.music_path_text.value = saved_path
        
        self.update()

    async def folder_picker_result(self, e: ft.FilePickerResultEvent):
        if e.path:
            self.music_path_text.value = e.path
            await self.page.client_storage.set_async("music_folder_path", e.path)
            
            # Update downloader service with new path
            if self.app_state.get("downloader"):
                self.app_state["downloader"].output_dir = e.path
            
            print(f"Carpeta de música guardada: {e.path}")
            self.update()

    async def reset_music_path(self, e):
        default_path = get_deeztracker_music_folder()
        self.music_path_text.value = default_path
        await self.page.client_storage.remove_async("music_folder_path")
        
        # Update downloader service with default path
        if self.app_state.get("downloader"):
            self.app_state["downloader"].output_dir = default_path
        
        print(f"Carpeta de música restaurada: {default_path}")
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
