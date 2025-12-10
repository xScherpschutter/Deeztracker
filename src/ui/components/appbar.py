import flet as ft
from ui import theme

def CustomAppBar(title: str, page: ft.Page):
    """
    Creates a custom AppBar. Flet will automatically handle the 'back' button.
    """
    return ft.AppBar(
        title=ft.Text(title, size=20, weight=ft.FontWeight.BOLD),
        center_title=True,
        bgcolor=theme.CONTENT_BG,
        actions=[
            ft.IconButton(
                icon=ft.Icons.SEARCH,
                tooltip="Buscar",
                icon_color=theme.ACCENT_COLOR if page.route == "/search" else theme.SECONDARY_TEXT,
                on_click=lambda _: page.go("/search")
            ),
            ft.IconButton(
                icon=ft.Icons.MUSIC_NOTE,
                tooltip="Música Local",
                icon_color=theme.ACCENT_COLOR if page.route == "/local" else theme.SECONDARY_TEXT,
                on_click=lambda _: page.go("/local")
            ),
            ft.IconButton(
                icon=ft.Icons.SETTINGS,
                tooltip="Configuración",
                icon_color=theme.ACCENT_COLOR if page.route == "/settings" else theme.SECONDARY_TEXT,
                on_click=lambda _: page.go("/settings")
            ),
            ft.Container(width=10) # Spacer
        ]
    )
