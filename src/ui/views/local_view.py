import flet as ft
from ui import theme

class LocalView(ft.View):
    def __init__(self, app_state):
        super().__init__(route="/local", bgcolor=theme.BG_COLOR)
        self.app_state = app_state
        
        self.controls = [
            ft.Container(
                content=ft.Text("Música Local (Próximamente)", size=20, color=theme.PRIMARY_TEXT),
                alignment=ft.alignment.center,
                expand=True
            )
        ]
