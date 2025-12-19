import flet as ft
from ui import theme
from ui.components import appbar, list_items
from features.api.types import AlbumResponse
import asyncio

class AlbumView(ft.View):
    def __init__(self, app_state, album_id: str):
        super().__init__(route=f"/album/{album_id}", bgcolor=theme.BG_COLOR)
        self.app_state = app_state
        self.translator = app_state.get("translator")
        self.api = app_state["api"]
        self.downloader = app_state["downloader"]
        self.album_id = album_id
        self.album_data: AlbumResponse = None 
        self.snackbar = ft.SnackBar(content=ft.Text(""))

        self.album_title = ft.Text(self.translator.t("album.loading") if self.translator else "Loading...", style=theme.title_style, size=22, text_align=ft.TextAlign.CENTER)
        self.artist_name = ft.Text("", color=theme.SECONDARY_TEXT, text_align=ft.TextAlign.CENTER)
        self.album_cover = ft.Image(
            width=200, height=200, fit=ft.ImageFit.COVER, border_radius=ft.border_radius.all(10)
        )
        
        self.tracks_column = ft.ListView(spacing=5, expand=True, padding=ft.padding.only(bottom=100))

        self.download_button = ft.ElevatedButton(
            text=self.translator.t("album.button_download") if self.translator else "Download Full Album",
            icon=ft.Icons.DOWNLOAD,
            on_click=lambda e: self.page.run_task(self._download_album_full),
            bgcolor=theme.ACCENT_COLOR,
            color=theme.BG_COLOR
        )

        self.content_column = ft.Column(
            [
                ft.Column(
                    [
                        ft.Row([self.album_cover], alignment=ft.MainAxisAlignment.CENTER),
                        self.album_title,
                        self.artist_name,
                        self.download_button,
                        ft.Divider(),
                    ],
                    spacing=15,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Stack(
                    [
                        self.tracks_column
                    ],
                    expand=True
                )
            ],
            expand=True,
            visible=False, # Initially hidden
        )

        self.progress_container = ft.Container(
            content=ft.ProgressRing(),
            alignment=ft.alignment.center
        )

        self.controls = [
            ft.Stack(
                [
                    self.content_column,
                    self.progress_container,
                ],
                expand=True
            )
        ]

    def did_mount(self):
        self.page.run_task(self.load_album_data)

    async def load_album_data(self):
        try:
            album_info, tracks_response = await asyncio.gather(
                self.api.get_album_info(self.album_id),
                self.api.get_album_tracks(self.album_id)
            )

            if not album_info:
                 raise Exception("Album not found")

            self.album_data = album_info

            self.album_title.value = self.album_data.title
            self.artist_name.value = self.album_data.artist.name
            self.album_cover.src = self.album_data.cover_big
            
            if tracks_response and tracks_response.data:
                for track in tracks_response.data:
                    self.tracks_column.controls.append(
                        list_items.TrackListItem(
                            page=self.page,
                            track_data=track,
                            on_download=self.download_track
                        )
                    )

            self.progress_container.visible = False
            self.content_column.visible = True
        except Exception as e:
            print(f"Error loading album data: {e}")
            self.progress_container.content = ft.Text("Error loading album data.", color=theme.ERROR_COLOR)
        
        self.update()



    async def _download_album_full(self, e):
        downloader = self.app_state["downloader"]
        album_title = self.album_data.title # Get album title from stored data

        start_msg = self.translator.t("album.download_started", title=album_title) if self.translator else f"Starting download of album '{album_title}'..."
        self.snackbar.content = ft.Text(start_msg)
        self.page.open(self.snackbar)
        try:
            album_url = f"https://www.deezer.com/album/{self.album_data.id}"
            download_format = await self.page.client_storage.get_async("download_format")
            await downloader.download_album(album_url, convert_to=download_format)
            success_msg = self.translator.t("album.download_success", title=album_title) if self.translator else f"Album '{album_title}' downloaded successfully!"
            self.snackbar.content = ft.Text(success_msg)
            self.snackbar.bgcolor = theme.SUCCESS_COLOR
            self.page.open(self.snackbar)
        except Exception as ex:
            print(f"Error downloading album {album_title}: {ex}")
            error_msg = self.translator.t("album.error_download_album", title=album_title, error=str(ex)) if self.translator else f"Error downloading album '{album_title}': {ex}"
            self.snackbar.content = ft.Text(error_msg)
            self.snackbar.bgcolor = theme.ERROR_COLOR
            self.page.open(self.snackbar)

    async def download_track(self, page: ft.Page, data, is_album=False):
        downloader = self.app_state["downloader"]
        item_title = data.title_short if not is_album else data.title
        
        start_msg = self.translator.t("album.download_track_started", title=item_title) if self.translator else f"Starting download of '{item_title}'..."
        self.snackbar.content = ft.Text(start_msg)
        page.open(self.snackbar)
        try:
            download_format = await page.client_storage.get_async("download_format")
            download_quality = await page.client_storage.get_async("download_quality")
            print(download_quality)
            await downloader.download_track(data.link, quality_download=download_quality, convert_to=download_format)
            success_msg = self.translator.t("album.download_track_success", title=item_title) if self.translator else f"'{item_title}' downloaded successfully!"
            self.snackbar.content = ft.Text(success_msg)
            self.snackbar.bgcolor = theme.SUCCESS_COLOR
            page.open(self.snackbar)
            
        except Exception as e:
            print(f"Error loading {item_title}: {e}")
            error_msg = self.translator.t("album.error_download_track", title=item_title, error=str(e)) if self.translator else f"Error downloading '{item_title}': {e}"
            self.snackbar.content = ft.Text(error_msg)
            self.snackbar.bgcolor = theme.ERROR_COLOR
            page.open(self.snackbar)
    
    async def close_dialog(self, dialog):
        dialog.open = False
        self.page.update()

