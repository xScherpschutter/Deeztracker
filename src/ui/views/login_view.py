import flet as ft
from ui import theme
from features.api.service import DeezerAPIService
from features.downloader.service import DeezloaderService

class LoginView(ft.View):
    def __init__(self, app_state):
        super().__init__(route="/login", bgcolor=theme.BG_COLOR)
        self.app_state = app_state
        self.translator = app_state.get("translator")

        self.arl_input = ft.TextField(
            label=self.translator.t("login.arl_label") if self.translator else "Deezer ARL Token",
            password=True,
            can_reveal_password=True,
            border_color=theme.ACCENT_COLOR,
            autofocus=True,
        )

        self.login_button = ft.ElevatedButton(
            text=self.translator.t("login.button") if self.translator else "Sign In",
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
                        ft.Text(self.translator.t("login.title") if self.translator else "Deeztracker", style=theme.title_style, size=32),
                        ft.Text(self.translator.t("login.subtitle") if self.translator else "Sign in with your ARL Token", color=theme.SECONDARY_TEXT),
                        self.arl_input,
                        ft.Row(
                            [self.login_button, self.progress_ring],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        self.status_text,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                ),
                alignment=ft.alignment.center,
                expand=True,
                padding=20,
            )
        ]
        
        # Subscribe to language changes
        if self.translator:
            self.translator.subscribe(self.on_language_change)
    
    def on_language_change(self, language_code):
        """Called when the language changes."""
        if not self.translator:
            return
        
        self.arl_input.label = self.translator.t("login.arl_label")
        self.login_button.text = self.translator.t("login.button")
        
        # Update static text elements
        self.controls[0].content.controls[2].value = self.translator.t("login.subtitle")
        
        try:
            self.update()
        except:
            pass  # Ignore if view is not mounted

    async def login_clicked(self, e):
        """Handles the login button click event."""
        arl_token = self.arl_input.value.strip()
        if not arl_token:
            self.status_text.value = self.translator.t("login.error_empty") if self.translator else "Please enter an ARL token."
            self.update()
            return

        self.login_button.disabled = True
        self.progress_ring.visible = True
        self.status_text.value = ""
        self.update()

        try:
            # Token validation is done by attempting to initialize the download service.
            # This is based on the structure of DeezloaderService.
            downloader = DeezloaderService(arl=arl_token)
            
            # If initialization is successful, save state and navigate.
            self.app_state["arl"] = arl_token
            self.app_state["api"] = DeezerAPIService()
            self.app_state["downloader"] = downloader
            
            # Save ARL to client_storage for persistence
            await self.page.client_storage.set_async("arl_token", arl_token)
            
            # Show navigation buttons after successful login
            if self.app_state.get("titlebar"):
                self.app_state["titlebar"].set_navigation_visible(True)
            
            self.page.go("/search")

        except Exception as ex:
            print(f"Login error: {ex}")
            self.status_text.value = self.translator.t("login.error_invalid") if self.translator else "Invalid ARL token or connection error."
            self.login_button.disabled = False
            self.progress_ring.visible = False
            self.update()
