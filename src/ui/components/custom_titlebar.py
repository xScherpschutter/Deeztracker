import flet as ft
from ui import theme

class CustomTitleBar(ft.WindowDragArea):
    def __init__(self, page: ft.Page):
        self.page = page
        
        # Window control buttons
        self.minimize_btn = ft.IconButton(
            icon=ft.Icons.MINIMIZE,
            icon_size=16,
            icon_color=theme.SECONDARY_TEXT,
            tooltip="Minimizar",
            on_click=self.minimize_window,
            style=ft.ButtonStyle(
                overlay_color={
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.1, theme.ACCENT_COLOR)
                }
            )
        )
        
        self.maximize_btn = ft.IconButton(
            icon=ft.Icons.CROP_SQUARE,
            icon_size=16,
            icon_color=theme.SECONDARY_TEXT,
            tooltip="Maximizar",
            on_click=self.toggle_maximize,
            style=ft.ButtonStyle(
                overlay_color={
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.1, theme.ACCENT_COLOR)
                }
            )
        )
        
        self.close_btn = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_size=16,
            icon_color=theme.SECONDARY_TEXT,
            tooltip="Cerrar",
            on_click=self.close_window,
            style=ft.ButtonStyle(
                overlay_color={
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.3, ft.Colors.RED)
                }
            )
        )
        
        # Title bar content
        titlebar_content = ft.Container(
            content=ft.Row(
                [
                    ft.Container(width=10),  # Left padding
                    ft.Icon(ft.Icons.MUSIC_NOTE, color=theme.ACCENT_COLOR, size=20),
                    ft.Container(width=8),
                    ft.Text(
                        "Deeztracker",
                        size=14,
                        weight=ft.FontWeight.W_500,
                        color=theme.PRIMARY_TEXT
                    ),
                    ft.Container(width=15),  # Separator between branding and navigation
                    # Navigation buttons (moved to left)
                    ft.IconButton(
                        icon=ft.Icons.SEARCH,
                        icon_size=20,
                        icon_color=theme.ACCENT_COLOR if page.route == "/search" else theme.SECONDARY_TEXT,
                        tooltip="Buscar",
                        on_click=lambda _: page.go("/search"),
                        style=ft.ButtonStyle(
                            overlay_color={
                                ft.ControlState.HOVERED: ft.Colors.with_opacity(0.1, theme.ACCENT_COLOR)
                            }
                        )
                    ),
                    ft.IconButton(
                        icon=ft.Icons.LIBRARY_MUSIC,
                        icon_size=20,
                        icon_color=theme.ACCENT_COLOR if page.route == "/local" else theme.SECONDARY_TEXT,
                        tooltip="Música Local",
                        on_click=lambda _: page.go("/local"),
                        style=ft.ButtonStyle(
                            overlay_color={
                                ft.ControlState.HOVERED: ft.Colors.with_opacity(0.1, theme.ACCENT_COLOR)
                            }
                        )
                    ),
                    ft.IconButton(
                        icon=ft.Icons.SETTINGS,
                        icon_size=20,
                        icon_color=theme.ACCENT_COLOR if page.route == "/settings" else theme.SECONDARY_TEXT,
                        tooltip="Configuración",
                        on_click=lambda _: page.go("/settings"),
                        style=ft.ButtonStyle(
                            overlay_color={
                                ft.ControlState.HOVERED: ft.Colors.with_opacity(0.1, theme.ACCENT_COLOR)
                            }
                        )
                    ),
                    ft.Container(expand=True),  # Spacer (moved to right of navigation)
                    self.minimize_btn,
                    self.maximize_btn,
                    self.close_btn,
                ],
                spacing=0,
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            bgcolor=theme.BG_COLOR,
            height=40,
            padding=ft.padding.only(right=5)
        )
        
        super().__init__(content=titlebar_content, maximizable=True)
    
    def minimize_window(self, e):
        """Minimize the window"""
        self.page.window.minimized = True
        self.page.update()
    
    def toggle_maximize(self, e):
        """Toggle between maximized and normal window state"""
        if self.page.window.maximized:
            self.page.window.maximized = False
            self.maximize_btn.icon = ft.Icons.CROP_SQUARE
        else:
            self.page.window.maximized = True
            self.maximize_btn.icon = ft.Icons.FILTER_NONE
        self.page.update()
    
    def close_window(self, e):
        """Close the application"""
        self.page.window.close()
