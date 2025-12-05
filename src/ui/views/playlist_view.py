import flet as ft
from ui import theme
from ui.components import list_items
from features.api.types import Playlist
import asyncio

class PlaylistView(ft.View):
    def __init__(self, app_state, playlist_id: str):
        super().__init__(route=f"/playlist/{playlist_id}", bgcolor=theme.BG_COLOR)
        self.app_state = app_state
        self.api = app_state["api"]
        self.downloader = app_state["downloader"]
        self.playlist_id = playlist_id
        self.playlist_data: Playlist = None
        self.snackbar = ft.SnackBar(content=ft.Text(""))

        self.playlist_title = ft.Text("Cargando...", style=theme.title_style, size=22, text_align=ft.TextAlign.CENTER)
        self.creator_name = ft.Text("", color=theme.SECONDARY_TEXT, text_align=ft.TextAlign.CENTER)
        self.playlist_cover = ft.Image(
            width=200, height=200, fit=ft.ImageFit.COVER, border_radius=ft.border_radius.all(10)
        )
        
        self.tracks_column = ft.ListView(spacing=5, expand=True)

        self.content_column = ft.Column(
            [
                ft.Column(
                    [
                        ft.Row([self.playlist_cover], alignment=ft.MainAxisAlignment.CENTER),
                        self.playlist_title,
                        self.creator_name,
                        ft.ElevatedButton(
                            "Descargar Playlist Completa",
                            icon=ft.Icons.DOWNLOAD,
                            on_click=lambda e: self.page.run_task(self._download_playlist_full, e),
                            bgcolor=theme.ACCENT_COLOR,
                            color=theme.BG_COLOR
                        ),
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
            visible=False,
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
        self.page.run_task(self.load_playlist_data)

    async def load_playlist_data(self):
        try:
            playlist_info, tracks_response = await asyncio.gather(
                self.api.get_playlist_info(self.playlist_id),
                self.api.get_playlist_tracks(self.playlist_id)
            )

            if not playlist_info:
                 raise Exception("Playlist no encontrada")

            self.playlist_data = playlist_info

            self.playlist_title.value = self.playlist_data.title
            self.creator_name.value = self.playlist_data.user.name if self.playlist_data.user else "Deezer"
            self.playlist_cover.src = self.playlist_data.picture_big
            
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
            print(f"Error cargando playlist: {e}")
            self.progress_container.content = ft.Text("Error al cargar datos de la playlist.", color=theme.ERROR_COLOR)
        
        self.update()




    async def _download_playlist_full(self, e):
        downloader = self.app_state["downloader"]
        playlist_title = self.playlist_data.title

        self.snackbar.content = ft.Text(f"Iniciando descarga de playlist '{playlist_title}'...")
        self.page.open(self.snackbar)
        try:
            download_format = await self.page.client_storage.get_async("download_format")
            await downloader.download_playlist(self.playlist_data.link, convert_to=download_format)
            self.snackbar.content = ft.Text(f"Playlist '{playlist_title}' descargada con éxito!")
            self.snackbar.bgcolor = theme.SUCCESS_COLOR
            self.page.open(self.snackbar)
        except Exception as ex:
            print(f"Error al descargar playlist {playlist_title}: {ex}")
            self.snackbar.content = ft.Text(f"Error al descargar playlist '{playlist_title}': {ex}")
            self.snackbar.bgcolor = theme.ERROR_COLOR
            self.page.open(self.snackbar)

    async def download_track(self, page: ft.Page, data, is_album=False):
        downloader = self.app_state["downloader"]
        item_title = data.title_short
        
        self.snackbar.content = ft.Text(f"Iniciando descarga de '{item_title}'...")
        page.open(self.snackbar)
        try:
            download_format = await page.client_storage.get_async("download_format")
            download_quality = await page.client_storage.get_async("download_quality")
            await downloader.download_track(data.link, convert_to=download_format, quality_download=download_quality)
            self.snackbar.content = ft.Text(f"'{item_title}' descargado con éxito!")
            self.snackbar.bgcolor = theme.SUCCESS_COLOR
            page.open(self.snackbar)
            
        except Exception as e:
            print(f"Error al descargar {item_title}: {e}")
            self.snackbar.content = ft.Text(f"Error al descargar '{item_title}': {e}")
            self.snackbar.bgcolor = theme.ERROR_COLOR
            page.open(self.snackbar)
    
    async def close_dialog(self, dialog):
        dialog.open = False
        self.page.update()
