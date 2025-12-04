import flet as ft
from ui import theme

def CustomAppBar(title: str, page: ft.Page):
    """
    Crea una AppBar personalizada. Flet manejará automáticamente el botón de 'atrás'.
    """
    return ft.AppBar(
        title=ft.Text(title, size=20, weight=ft.FontWeight.BOLD),
        center_title=True,
        bgcolor=theme.CONTENT_BG,
    )
