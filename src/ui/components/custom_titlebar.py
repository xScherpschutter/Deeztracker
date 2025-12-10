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
        
        # Back button (hidden by default, shown when navigation stack has previous views)
        self.back_btn = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            icon_size=20,
            icon_color=theme.SECONDARY_TEXT,
            tooltip="Atrás",
            on_click=self.go_back,
            visible=False,  # Hidden by default
            style=ft.ButtonStyle(
                overlay_color={
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.1, theme.ACCENT_COLOR)
                }
            )
        )
        
        # Navigation buttons (hidden by default until user logs in)
        self.search_btn = ft.IconButton(
            icon=ft.Icons.SEARCH,
            icon_size=20,
            icon_color=theme.ACCENT_COLOR if page.route == "/search" else theme.SECONDARY_TEXT,
            tooltip="Buscar",
            on_click=lambda _: self.smart_navigate("/search"),
            visible=False,  # Hidden by default
            style=ft.ButtonStyle(
                overlay_color={
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.1, theme.ACCENT_COLOR)
                }
            )
        )
        
        self.local_btn = ft.IconButton(
            icon=ft.Icons.LIBRARY_MUSIC,
            icon_size=20,
            icon_color=theme.ACCENT_COLOR if page.route == "/local" else theme.SECONDARY_TEXT,
            tooltip="Música Local",
            on_click=lambda _: self.smart_navigate("/local"),
            visible=False,  # Hidden by default
            style=ft.ButtonStyle(
                overlay_color={
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.1, theme.ACCENT_COLOR)
                }
            )
        )
        
        self.settings_btn = ft.IconButton(
            icon=ft.Icons.SETTINGS,
            icon_size=20,
            icon_color=theme.ACCENT_COLOR if page.route == "/settings" else theme.SECONDARY_TEXT,
            tooltip="Configuración",
            on_click=lambda _: self.smart_navigate("/settings"),
            visible=False,  # Hidden by default
            style=ft.ButtonStyle(
                overlay_color={
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.1, theme.ACCENT_COLOR)
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
                    # Back button (appears when there are previous views)
                    self.back_btn,
                    # Navigation buttons
                    self.search_btn,
                    self.local_btn,
                    self.settings_btn,
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
        
        import platform
        if platform.system() == "Linux":
             self.minimize_btn.visible = False
             self.maximize_btn.visible = False
             self.close_btn.visible = False

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
    
    def set_navigation_visible(self, visible: bool):
        """Show or hide navigation buttons based on authentication state"""
        self.search_btn.visible = visible
        self.local_btn.visible = visible
        self.settings_btn.visible = visible
    
    def smart_navigate(self, target_route: str):
        """Navigate to a route, backtracking if it exists in the stack"""
        # Check if the target route exists in the current stack
        for i, view in enumerate(self.page.views):
            if view.route == target_route:
                # Found the route in the stack, pop everything after it
                while len(self.page.views) > i + 1:
                    self.page.views.pop()
                # Update route and refresh
                self.page.route = target_route
                self.page.update()
                self.update_back_button()
                return
        
        # Route not in stack, navigate normally (will add to stack)
        self.page.go(target_route)
    
    def go_back(self, e):
        """Navigate to the previous view"""
        if len(self.page.views) > 1:
            self.page.views.pop()
            top_view = self.page.views[-1]
            # Update the route without triggering route_change
            self.page.route = top_view.route
            self.page.update()
            # Update back button visibility
            self.update_back_button()
    
    def update_back_button(self):
        """Show or hide back button based on navigation stack"""
        # Show back button if there are previous views to go back to
        should_show = len(self.page.views) > 1
        self.back_btn.visible = should_show
        try:
            self.page.update()
        except:
            pass  # Ignore if page is not ready yet
