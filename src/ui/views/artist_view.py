import flet as ft
from ui import theme
from ui.components import appbar, list_items
import asyncio

class ArtistView(ft.View):
    def __init__(self, app_state, artist_id: str):
        super().__init__(
            route=f"/artist/{artist_id}", 
            bgcolor=theme.BG_COLOR
        )
        self.snackbar = ft.SnackBar(content=ft.Text(""))
        self.app_state = app_state
        self.api = app_state["api"]
        self.artist_id = artist_id
        
        self.artist_name = ft.Text("Cargando...", style=theme.title_style, size=24)
        self.artist_image = ft.Image(
            width=150, height=150, fit=ft.ImageFit.COVER, border_radius=ft.border_radius.all(75)
        )
        self.fan_count = ft.Text("", color=theme.SECONDARY_TEXT)
        
        self.albums_row = ft.Row(scroll=ft.ScrollMode.ADAPTIVE, spacing=15)
        self.top_tracks_list = ft.ListView(spacing=5, expand=True, padding=ft.padding.only(bottom=100))
        
        self.content_column = ft.Column(
            [
                ft.Row([self.artist_image], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([self.artist_name], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([self.fan_count], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(),
                ft.Text("Álbumes", style=theme.subtitle_style),
                self.albums_row,
                ft.Divider(),
                ft.Text("Top Canciones", style=theme.subtitle_style),
                self.top_tracks_list,
            ],
            spacing=15,
            visible=False,
            expand=True,
            scroll=ft.ScrollMode.ADAPTIVE,
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
        """Se llama cuando la vista se monta. Inicia la carga de datos."""
        self.page.run_task(self.load_artist_data)
        
    async def load_artist_data(self):
        """Carga los datos del artista, sus álbumes y top canciones de forma concurrente."""
        try:
            # Hacemos las llamadas a la API en paralelo
            results = await asyncio.gather(
                self.api.get_artist_info(self.artist_id),
                self.api.get_artist_albums(self.artist_id),
                self.api._request(f"artist/{self.artist_id}/top?limit=10")
            )
            artist_info, artist_albums, top_tracks_response = results

            # Poblar información del artista
            self.artist_name.value = artist_info.name
            self.artist_image.src = artist_info.picture_big
            self.fan_count.value = f"{artist_info.nb_fan:,} fans"
            
            # Poblar álbumes
            if artist_albums:
                for album in artist_albums:
                    self.albums_row.controls.append(
                        list_items.AlbumCard(page=self.page, album_data=album)
                    )
            
            # Poblar top canciones
            if top_tracks_response and top_tracks_response.get('data'):
                for track in top_tracks_response['data']:
                    # La respuesta de /top es un poco diferente, la adaptamos
                    track_obj_for_list = lambda t: type('obj', (object,), {
                        'id': t['id'],
                        'title_short': t['title_short'],
                        'duration': t['duration'],
                        'track_position': top_tracks_response['data'].index(t) + 1,
                        'preview': t.get('preview', ''),
                        'link': t['link']
                    })
                    self.top_tracks_list.controls.append(
                        list_items.TrackListItem(
                            page=self.page,
                            track_data=track_obj_for_list(track),
                            on_download=self.download_track
                        )
                    )

            self.progress_container.visible = False
            self.content_column.visible = True
        except Exception as e:
            print(f"Error cargando artista: {e}")
            self.progress_container.visible = False
            self.content_column.controls.clear()
            self.content_column.controls.append(ft.Text("Error al cargar datos del artista.", color=theme.ERROR_COLOR))
            self.content_column.visible = True
        
        self.update()



    async def download_track(self, page: ft.Page, track_data):
        downloader = self.app_state["downloader"]
        self.snackbar.content = ft.Text(f"Iniciando descarga de '{track_data.title_short}'...")
        page.open(self.snackbar)
        try:
            download_format = await page.client_storage.get_async("download_format")
            download_quality = await page.client_storage.get_async("download_quality")
            await downloader.download_track(track_data.link, convert_to=download_format, quality_download=download_quality)
            self.snackbar.content = ft.Text(f"'{track_data.title_short}' descargado con éxito!")
            self.snackbar.bgcolor = theme.SUCCESS_COLOR
            page.open(self.snackbar)
            
        except Exception as e:
            print(f"Error al descargar {track_data.title_short}: {e}")
            self.snackbar.content = ft.Text(f"Error al descargar '{track_data.title_short}': {e}")
            self.snackbar.bgcolor = theme.ERROR_COLOR
            page.open(self)


