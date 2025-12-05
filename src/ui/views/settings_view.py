import flet as ft
from ui import theme
from flet_permission_handler import PermissionHandler, PermissionType, PermissionStatus

class SettingsView(ft.View):
    def __init__(self, app_state):
        super().__init__(route="/settings", bgcolor=theme.BG_COLOR, scroll=ft.ScrollMode.ADAPTIVE)
        self.app_state = app_state
        self.permission_handler = app_state.get("permission_handler")
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

        # Permission Status Text
        self.permission_status_text = ft.Text("Estado de permisos: Desconocido", color=theme.SECONDARY_TEXT)

        self.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text("Configuración", size=24, weight=ft.FontWeight.BOLD, color=theme.PRIMARY_TEXT),
                    ft.Divider(color=theme.ACCENT_COLOR),
                    
                    ft.Text("Descargas", size=18, weight=ft.FontWeight.BOLD, color=theme.PRIMARY_TEXT),
                    self.format_dropdown,
                    ft.Divider(color=theme.SECONDARY_TEXT),

                    ft.Text("Permisos", size=18, weight=ft.FontWeight.BOLD, color=theme.PRIMARY_TEXT),
                    self.permission_status_text,
                    ft.ElevatedButton(
                        "Verificar Permisos de Almacenamiento", 
                        on_click=self.check_permissions,
                        bgcolor=theme.ACCENT_COLOR,
                        color=theme.TEXT_COLOR if hasattr(theme, 'TEXT_COLOR') else theme.BG_COLOR # Fallback or fix theme
                    ),
                    ft.ElevatedButton(
                        "Solicitar Permisos de Almacenamiento", 
                        on_click=self.request_permissions,
                        bgcolor=theme.ACCENT_COLOR,
                        color=theme.TEXT_COLOR if hasattr(theme, 'TEXT_COLOR') else theme.BG_COLOR
                    ),
                    ft.ElevatedButton(
                        "Abrir Configuración del Sistema", 
                        on_click=self.open_app_settings,
                        bgcolor=theme.SECONDARY_TEXT,
                        color=theme.PRIMARY_TEXT
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
                padding=20,
                expand=True
            )
        ]
        
        # Load initial preferences
    def did_mount(self):
        # Load preferences and check permissions when view mounts
        self.page.run_task(self.init_settings)

    async def init_settings(self):
        await self.load_preferences()
        await self.check_permissions(None)

    async def load_preferences(self):
        saved_format = await self.page.client_storage.get_async("download_format")
        if saved_format:
            self.format_dropdown.value = saved_format
            self.update()

    async def save_format_preference(self, e):
        music_format = self.format_dropdown.value
        await self.page.client_storage.set_async("download_format", music_format)
        await self.page.client_storage.set_async("download_quality", self.format_mapper.get(music_format, "FLAC"))
        print(f"Formato de descarga guardado: {self.format_mapper.get(music_format, "FLAC")}")

    async def logout(self, e):
        await self.page.client_storage.remove_async("arl_token")
        self.app_state["arl"] = None
        self.app_state["api"] = None
        self.app_state["downloader"] = None
        self.page.go("/login")

    async def check_permissions(self, e):
        if self.permission_handler:
            status = await self.permission_handler.check_permission(PermissionType.STORAGE)
            self.permission_status_text.value = f"Estado de permisos: {status.name}"
            self.update()
        else:
             self.permission_status_text.value = "Handler de permisos no disponible"
             self.update()

    async def request_permissions(self, e):
        if self.permission_handler:
            status = await self.permission_handler.request_permission(PermissionType.STORAGE)
            self.permission_status_text.value = f"Estado de permisos: {status.name}"
            self.update()

    async def open_app_settings(self, e):
        if self.permission_handler:
            await self.permission_handler.open_app_settings()

