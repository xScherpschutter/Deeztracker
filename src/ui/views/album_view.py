import flet as ft
from ui import theme
from ui.components import appbar, list_items
from features.api.types import AlbumResponse
import asyncio

class AlbumView(ft.View):
    def __init__(self, app_state, album_id: str):
        super().__init__(route=f"/album/{album_id}", bgcolor=theme.BG_COLOR)
        self.app_state = app_state
        self.api = app_state["api"]
        self.downloader = app_state["downloader"]
        self.album_id = album_id
        self.album_data: AlbumResponse = None # Para almacenar datos del álbum
        self.snackbar = ft.SnackBar(content=ft.Text(""))

        self.album_title = ft.Text("Cargando...", style=theme.title_style, size=22, text_align=ft.TextAlign.CENTER)
        self.artist_name = ft.Text("", color=theme.SECONDARY_TEXT, text_align=ft.TextAlign.CENTER)
        self.album_cover = ft.Image(
            width=200, height=200, fit=ft.ImageFit.COVER, border_radius=ft.border_radius.all(10)
        )
        
        self.tracks_column = ft.ListView(spacing=5, expand=True, padding=ft.padding.only(bottom=100))

        # Main content column, initially invisible
        self.content_column = ft.Column(
            [
                # --- Non-scrolling part ---
                ft.Column(
                    [
                        ft.Row([self.album_cover], alignment=ft.MainAxisAlignment.CENTER),
                        self.album_title,
                        self.artist_name,
                        ft.ElevatedButton(
                            "Descargar Álbum Completo",
                            icon=ft.Icons.DOWNLOAD,
                            on_click=lambda e: self.page.run_task(self._download_album_full, e),
                            bgcolor=theme.ACCENT_COLOR,
                            color=theme.BG_COLOR
                        ),
                        ft.Divider(),
                    ],
                    spacing=15,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                # --- Scrolling part ---
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
                 raise Exception("Álbum no encontrado")

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
            print(f"Error cargando álbum: {e}")
            self.progress_container.content = ft.Text("Error al cargar datos del álbum.", color=theme.ERROR_COLOR)
        
        self.update()



    async def _download_album_full(self, e):
        downloader = self.app_state["downloader"]
        album_title = self.album_data.title # Get album title from stored data

        self.snackbar.content = ft.Text(f"Iniciando descarga de álbum '{album_title}'...")
        self.page.open(self.snackbar)
        try:
            album_url = f"https://www.deezer.com/album/{self.album_data.id}"
            download_format = await self.page.client_storage.get_async("download_format")
            await downloader.download_album(album_url, convert_to=download_format)
            self.snackbar.content = ft.Text(f"Álbum '{album_title}' descargado con éxito!")
            self.snackbar.bgcolor = theme.SUCCESS_COLOR
            self.page.open(self.snackbar)
        except Exception as ex:
            print(f"Error al descargar álbum {album_title}: {ex}")
            self.snackbar.content = ft.Text(f"Error al descargar álbum '{album_title}': {ex}")
            self.snackbar.bgcolor = theme.ERROR_COLOR
            self.page.open(self.snackbar)

    async def download_track(self, page: ft.Page, data, is_album=False):
        downloader = self.app_state["downloader"]
        item_title = data.title_short if not is_album else data.title
        
        self.snackbar.content = ft.Text(f"Iniciando descarga de '{item_title}'...")
        page.open(self.snackbar)
        try:
            download_format = await page.client_storage.get_async("download_format")
            download_quality = await page.client_storage.get_async("download_quality")
            print(download_quality)
            await downloader.download_track(data.link, quality_download=download_quality, convert_to=download_format)
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

