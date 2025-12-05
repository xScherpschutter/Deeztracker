import flet as ft
from ui import theme
import asyncio

class PlayerView(ft.View):
    def __init__(self, app_state):
        super().__init__(route="/player", bgcolor=theme.BG_COLOR, padding=20)
        self.app_state = app_state
        self.player_manager = app_state["player_manager"]
        
        # UI Elements
        self.cover_image = ft.Container(
            content=ft.Image(
                src="https://via.placeholder.com/300",
                width=300, height=300,
                fit=ft.ImageFit.COVER,
                border_radius=10,
            ),
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK54),
            border_radius=10
        )
        
        self.track_title = ft.Text(
            "Desconocido",
            size=24,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS
        )
        
        self.artist_name = ft.Text(
            "Desconocido",
            size=18,
            color=theme.SECONDARY_TEXT,
            text_align=ft.TextAlign.CENTER,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS
        )
        
        self.position_slider = ft.Slider(
            min=0, max=100,
            on_change_end=self.seek_audio,
            active_color=theme.ACCENT_COLOR
        )
        
        self.position_text = ft.Text("0:00", color=theme.SECONDARY_TEXT, size=12)
        self.duration_text = ft.Text("0:00", color=theme.SECONDARY_TEXT, size=12)
        
        # Controls
        self.shuffle_btn = ft.IconButton(
            icon=ft.Icons.SHUFFLE,
            icon_color=theme.SECONDARY_TEXT,
            on_click=self.toggle_shuffle
        )
        
        self.prev_btn = ft.IconButton(
            icon=ft.Icons.SKIP_PREVIOUS,
            icon_size=40,
            icon_color=theme.PRIMARY_TEXT,
            on_click=lambda _: self.player_manager.prev_track()
        )
        
        self.play_pause_btn = ft.IconButton(
            icon=ft.Icons.PLAY_CIRCLE_FILLED,
            icon_size=64,
            icon_color=theme.ACCENT_COLOR,
            on_click=lambda _: self.player_manager.toggle_play_pause()
        )
        
        self.next_btn = ft.IconButton(
            icon=ft.Icons.SKIP_NEXT,
            icon_size=40,
            icon_color=theme.PRIMARY_TEXT,
            on_click=lambda _: self.player_manager.next_track()
        )
        
        self.repeat_btn = ft.IconButton(
            icon=ft.Icons.REPEAT,
            icon_color=theme.SECONDARY_TEXT,
            on_click=self.toggle_repeat
        )
        
        self.controls = [
            ft.Column(
                [
                    ft.Container(height=20), # Spacer
                    ft.Container(
                        content=self.cover_image,
                        alignment=ft.alignment.center,
                        expand=True
                    ),
                    ft.Container(height=20),
                    self.track_title,
                    self.artist_name,
                    ft.Container(height=20),
                    ft.Column(
                        [
                            self.position_slider,
                            ft.Row(
                                [self.position_text, self.duration_text],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            )
                        ]
                    ),
                    ft.Container(height=10),
                    ft.Row(
                        [
                            self.shuffle_btn,
                            self.prev_btn,
                            self.play_pause_btn,
                            self.next_btn,
                            self.repeat_btn
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True
            )
        ]
        
    def did_mount(self):
        # Register callbacks
        self.player_manager.subscribe(
            on_track_change=self.update_track_info,
            on_state_change=self.update_play_state,
            on_position_change=self.update_position
        )
        
        # Load current state
        self.update_track_info(self.player_manager.playlist[self.player_manager.current_index] if self.player_manager.playlist else {})
        self.update_play_state(self.player_manager.is_playing)
        
        # Sync shuffle/repeat state
        self.shuffle_btn.icon_color = theme.ACCENT_COLOR if self.player_manager.is_shuffle else theme.SECONDARY_TEXT
        self.repeat_btn.icon_color = theme.ACCENT_COLOR if self.player_manager.is_repeat else theme.SECONDARY_TEXT
        self.update()

    def will_unmount(self):
        self.player_manager.unsubscribe(
            on_track_change=self.update_track_info,
            on_state_change=self.update_play_state,
            on_position_change=self.update_position
        )

    def update_track_info(self, track):
        self.track_title.value = track.get('title', 'Desconocido')
        self.artist_name.value = track.get('artist', 'Desconocido')
        
        # Use cover if exists and not empty, otherwise placeholder
        cover = track.get('cover', '')
        if cover and cover.strip():
            self.cover_image.content.src = cover
        else:
            self.cover_image.content.src = "https://via.placeholder.com/300"
        
        self.update()

    def update_play_state(self, is_playing):
        self.play_pause_btn.icon = ft.Icons.PAUSE_CIRCLE_FILLED if is_playing else ft.Icons.PLAY_CIRCLE_FILLED
        self.update()

    def update_position(self, position, duration):
        if duration > 0:
            self.position_slider.max = duration
            self.position_slider.value = position
            self.position_text.value = self.format_time(position)
            self.duration_text.value = self.format_time(duration)
            self.update()

    def seek_audio(self, e):
        self.player_manager.seek(int(e.control.value))

    def toggle_shuffle(self, e):
        is_shuffle = self.player_manager.toggle_shuffle()
        self.shuffle_btn.icon_color = theme.ACCENT_COLOR if is_shuffle else theme.SECONDARY_TEXT
        self.update()

    def toggle_repeat(self, e):
        is_repeat = self.player_manager.toggle_repeat()
        self.repeat_btn.icon_color = theme.ACCENT_COLOR if is_repeat else theme.SECONDARY_TEXT
        self.update()

    def format_time(self, milliseconds):
        seconds = int(milliseconds / 1000)
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02}"
