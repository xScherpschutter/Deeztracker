import flet as ft
from ui import theme
from features.api.service import DeezerAPIService
from features.downloader.service import DeezloaderService

class LoginView(ft.View):
    def __init__(self, app_state):
        super().__init__(route="/login", bgcolor=theme.BG_COLOR)
        self.app_state = app_state

        self.arl_input = ft.TextField(
            label="Token ARL de Deezer",
            password=True,
            can_reveal_password=True,
            border_color=theme.ACCENT_COLOR,
            autofocus=True,
        )

        self.login_button = ft.ElevatedButton(
            text="Iniciar Sesión",
            icon=ft.Icons.LOGIN,
            on_click=self.login_clicked,
            bgcolor=theme.ACCENT_COLOR,
            color=theme.BG_COLOR,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )

        self.status_text = ft.Text(value="", color=theme.ERROR_COLOR)
        self.progress_ring = ft.ProgressRing(visible=False)

        self.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(name=ft.Icons.MUSIC_NOTE, size=60, color=theme.ACCENT_COLOR),
                        ft.Text("Deeztracker", style=theme.title_style, size=32),
                        ft.Text("Inicia sesión con tu ARL Token", color=theme.SECONDARY_TEXT),
                        self.arl_input,
                        ft.Row(
                            [self.login_button, self.progress_ring],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        self.status_text,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
                alignment=ft.alignment.center,
                expand=True,
            )
        ]

    async def login_clicked(self, e):
        """Maneja el evento de clic en el botón de login."""
        arl_token = self.arl_input.value.strip()
        if not arl_token:
            self.status_text.value = "Por favor, introduce un token ARL."
            self.update()
            return

        self.login_button.disabled = True
        self.progress_ring.visible = True
        self.status_text.value = ""
        self.update()

        try:
            # La validación del token se hace intentando inicializar el servicio de descarga.
            # Este es un supuesto basado en la estructura de DeezloaderService.
            downloader = DeezloaderService(arl=arl_token)
            
            # Si la inicialización es exitosa, guardamos el estado y navegamos.
            self.app_state["arl"] = arl_token
            self.app_state["api"] = DeezerAPIService()
            self.app_state["downloader"] = downloader
            
            # Guardar ARL en client_storage para persistencia
            await self.page.client_storage.set_async("arl_token", arl_token)
            
            self.page.go("/search")

        except Exception as ex:
            print(f"Error de login: {ex}")
            self.status_text.value = "Token ARL inválido o error de conexión."
            self.login_button.disabled = False
            self.progress_ring.visible = False
            self.update()
