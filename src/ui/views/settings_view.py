import flet as ft
from ui import theme
from features.downloader.utils import get_deeztracker_music_folder
from features.translations import AVAILABLE_LANGUAGES, LANGUAGE_NAMES

class SettingsView(ft.View):
    def __init__(self, app_state):
        super().__init__(route="/settings", bgcolor=theme.BG_COLOR, scroll=ft.ScrollMode.ADAPTIVE)
        self.app_state = app_state
        self.translator = app_state.get("translator")
        self.format_mapper = {
            "flac": "FLAC",
            "mp3-320": "MP3_320",
            "mp3-128": "MP3_128"
        }
        
        # Download Format Selection
        self.format_dropdown = ft.Dropdown(
            label=self.translator.t("settings.download_format") if self.translator else "Download Format",
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

        # Language Selection - dynamically generate options
        self.language_dropdown = ft.Dropdown(
            label="Idioma / Language",
            width=200,
            options=[
                ft.dropdown.Option(key=lang_code, text=lang_name)
                for lang_code, lang_name in LANGUAGE_NAMES.items()
            ],
            value="en",
            on_change=self.save_language_preference,
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

        # Store references to text controls for language updates
        self.title_text = ft.Text(self.translator.t("settings.title") if self.translator else "Settings", size=24, weight=ft.FontWeight.BOLD, color=theme.PRIMARY_TEXT)
        self.downloads_text = ft.Text(self.translator.t("settings.downloads") if self.translator else "Downloads", size=18, weight=ft.FontWeight.BOLD, color=theme.PRIMARY_TEXT)
        self.format_note_text = ft.Text(
            self.translator.t("settings.format_note") if self.translator else "Note: FLAC conversion is only available\nif FFmpeg is installed, otherwise it will be MP3.",
            size=12,
            color=theme.SECONDARY_TEXT,
        )
        self.music_folder_text = ft.Text(self.translator.t("settings.music_folder") if self.translator else "Music Folder", size=18, weight=ft.FontWeight.BOLD, color=theme.PRIMARY_TEXT)
        self.current_path_label = ft.Text(self.translator.t("settings.current_path") if self.translator else "Current path:", size=14, color=theme.PRIMARY_TEXT)
        self.change_folder_btn = ft.ElevatedButton(
            self.translator.t("settings.button_change") if self.translator else "Change Folder",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=lambda _: self.folder_picker.get_directory_path(
                dialog_title="Seleccionar carpeta de música"
            ),
            bgcolor=theme.ACCENT_COLOR,
            color=ft.Colors.WHITE,
        )
        self.restore_btn = ft.TextButton(
            self.translator.t("settings.button_restore") if self.translator else "Restore",
            icon=ft.Icons.RESTORE,
            on_click=self.reset_music_path,
        )
        self.folder_note_text = ft.Text(
            self.translator.t("settings.folder_note") if self.translator else "This folder will be used to save downloads\nand to search for local music.",
            size=12,
            color=theme.SECONDARY_TEXT,
        )
        self.session_text = ft.Text(self.translator.t("settings.session") if self.translator else "Session", size=18, weight=ft.FontWeight.BOLD, color=theme.PRIMARY_TEXT)
        self.logout_btn = ft.ElevatedButton(
            self.translator.t("settings.button_logout") if self.translator else "Sign Out", 
            on_click=self.logout,
            bgcolor=theme.ERROR_COLOR,
            color=ft.Colors.WHITE
        )

        self.controls = [
            ft.Container(
                content=ft.Column([
                    self.title_text,
                    ft.Divider(color=theme.ACCENT_COLOR),
                    
                    self.downloads_text,
                    self.format_dropdown,
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=theme.SECONDARY_TEXT),
                            self.format_note_text,
                        ], spacing=8),
                        padding=ft.padding.only(top=5),
                    ),
                    ft.Divider(color=theme.SECONDARY_TEXT),

                    # Language Section
                    ft.Text("Idioma / Language", size=18, weight=ft.FontWeight.BOLD, color=theme.PRIMARY_TEXT),
                    self.language_dropdown,
                    ft.Divider(color=theme.SECONDARY_TEXT),

                    # Music Path Configuration Section
                    self.music_folder_text,
                    ft.Container(
                        content=ft.Column([
                            self.current_path_label,
                            self.music_path_text,
                            ft.Row([
                                self.change_folder_btn,
                                self.restore_btn,
                            ], spacing=10),
                        ], spacing=10),
                        padding=ft.padding.only(top=5),
                    ),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=theme.SECONDARY_TEXT),
                            self.folder_note_text,
                        ], spacing=8),
                        padding=ft.padding.only(top=5),
                    ),
                    ft.Divider(color=theme.SECONDARY_TEXT),

                    self.session_text,
                    self.logout_btn,

                ], spacing=20),
                padding=ft.padding.only(left=20, top=20, right=20, bottom=100),
                expand=True
            )
        ]
        
        # Subscribe to language changes
        if self.translator:
            self.translator.subscribe(self.on_language_change)
    
    def on_language_change(self, language_code):
        """Update UI when language changes"""
        if not self.translator:
            return
        
        # Update all text elements using the stored references
        self.format_dropdown.label = self.translator.t("settings.download_format")
        self.title_text.value = self.translator.t("settings.title")
        self.downloads_text.value = self.translator.t("settings.downloads")
        self.format_note_text.value = self.translator.t("settings.format_note")
        self.music_folder_text.value = self.translator.t("settings.music_folder")
        self.current_path_label.value = self.translator.t("settings.current_path")
        self.change_folder_btn.text = self.translator.t("settings.button_change")
        self.restore_btn.text = self.translator.t("settings.button_restore")
        self.folder_note_text.value = self.translator.t("settings.folder_note")
        self.session_text.value = self.translator.t("settings.session")
        self.logout_btn.text = self.translator.t("settings.button_logout")
        
        try:
            self.update()
        except:
            pass
        
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
        
        # Load saved language
        saved_language = await self.page.client_storage.get_async("app_language")
        if saved_language in AVAILABLE_LANGUAGES:
            self.language_dropdown.value = saved_language
        
        self.update()

    async def folder_picker_result(self, e: ft.FilePickerResultEvent):
        if e.path:
            self.music_path_text.value = e.path
            await self.page.client_storage.set_async("music_folder_path", e.path)
            
            # Update downloader service with new path
            if self.app_state.get("downloader"):
                self.app_state["downloader"].output_dir = e.path
            
            print(f"Music folder saved: {e.path}")
            self.update()

    async def reset_music_path(self, e):
        default_path = get_deeztracker_music_folder()
        self.music_path_text.value = default_path
        await self.page.client_storage.remove_async("music_folder_path")
        
        # Update downloader service with default path
        if self.app_state.get("downloader"):
            self.app_state["downloader"].output_dir = default_path
        
        print(f"Music folder restored: {default_path}")
        self.update()

    async def save_format_preference(self, e):
        music_format = self.format_dropdown.value
        await self.page.client_storage.set_async("download_format", music_format)
        await self.page.client_storage.set_async("download_quality", self.format_mapper.get(music_format, "FLAC"))
        print(f"Download format saved: {self.format_mapper.get(music_format, 'FLAC')}")
    
    async def save_language_preference(self, e):
        language = self.language_dropdown.value
        await self.page.client_storage.set_async("app_language", language)
        
        # Update translator language
        if self.app_state.get("translator"):
            self.app_state["translator"].set_language(language)
        
        print(f"Language saved: {language}")

    async def logout(self, e):
        # Stop player and clear playlist
        if "player_manager" in self.app_state and self.app_state["player_manager"]:
            player_manager = self.app_state["player_manager"]
            player_manager._stop_position_updates()
            if player_manager.player and player_manager.player.is_playing():
                player_manager.player.stop()
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
        
        # Hide navigation buttons
        if self.app_state.get("titlebar"):
            self.app_state["titlebar"].set_navigation_visible(False)
        
        self.page.go("/login")
