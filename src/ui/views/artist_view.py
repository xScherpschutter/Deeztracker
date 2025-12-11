import flet as ft
from ui import theme
from ui.components import appbar, list_items
import asyncio

class ArtistView(ft.View):
    def __init__(self, app_state, artist_id):
        super().__init__(
            route=f"/artist/{artist_id}", 
            bgcolor=theme.BG_COLOR
        )
        self.snackbar = ft.SnackBar(content=ft.Text(""))
        self.app_state = app_state
        self.translator = app_state.get("translator")
        self.api = app_state["api"]
        self.artist_id = artist_id
        
        self.artist_name = ft.Text(self.translator.t("artist.loading") if self.translator else "Loading...", style=theme.title_style, size=24)
        self.artist_image = ft.Image(
            width=150, height=150, fit=ft.ImageFit.COVER, border_radius=ft.border_radius.all(75)
        )
        self.fan_count = ft.Text("", color=theme.SECONDARY_TEXT)
        
        self.albums_row = ft.Row(scroll=ft.ScrollMode.ADAPTIVE, spacing=15)
        self.top_tracks_list = ft.ListView(spacing=5, expand=True, padding=ft.padding.only(bottom=100))
        
        # Store text controls for language updates
        self.albums_label = ft.Text(self.translator.t("artist.albums") if self.translator else "Albums", style=theme.subtitle_style)
        self.top_songs_label = ft.Text(self.translator.t("artist.top_tracks") if self.translator else "Top Songs", style=theme.subtitle_style)
        
        self.content_column = ft.Column(
            [
                ft.Row([self.artist_image], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([self.artist_name], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([self.fan_count], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(),
                self.albums_label,
                self.albums_row,
                ft.Divider(),
                self.top_songs_label,
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
        """Called when the view is mounted. Starts loading data."""
        self.page.run_task(self.load_artist_data)
        
    async def load_artist_data(self):
        """Loads the artist data, their albums and top tracks concurrently."""
        try:
            # Make API calls in parallel
            results = await asyncio.gather(
                self.api.get_artist_info(self.artist_id),
                self.api.get_artist_albums(self.artist_id),
                self.api._request(f"artist/{self.artist_id}/top?limit=10")
            )
            artist_info, artist_albums, top_tracks_response = results

            # Populate artist information
            self.artist_name.value = artist_info.name
            self.artist_image.src = artist_info.picture_big
            self.fan_count.value = self.translator.t('artist.fans', count=f"{artist_info.nb_fan:,}") if self.translator else f"{artist_info.nb_fan:,} fans"
            
            # Populate albums
            if artist_albums:
                for album in artist_albums:
                    self.albums_row.controls.append(
                        list_items.AlbumCard(page=self.page, album_data=album)
                    )
            
            # Populate top tracks
            if top_tracks_response and top_tracks_response.get('data'):
                for track in top_tracks_response['data']:
                    # The /top response is slightly different, we adapt it
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
            print(f"Error loading artist: {e}")
            self.progress_container.visible = False
            self.content_column.controls.clear()
            self.content_column.controls.append(ft.Text(self.translator.t("artist.error_loading") if self.translator else "Error loading artist data.", color=theme.ERROR_COLOR))
            self.content_column.visible = True
        
        self.update()



    async def download_track(self, page: ft.Page, track_data):
        downloader = self.app_state["downloader"]
        start_msg = self.translator.t("artist.download_started", title=track_data.title_short) if self.translator else f"Starting download of '{track_data.title_short}'..."
        self.snackbar.content = ft.Text(start_msg)
        page.open(self.snackbar)
        try:
            download_format = await page.client_storage.get_async("download_format")
            download_quality = await page.client_storage.get_async("download_quality")
            await downloader.download_track(track_data.link, convert_to=download_format, quality_download=download_quality)
            success_msg = self.translator.t("artist.download_success", title=track_data.title_short) if self.translator else f"'{track_data.title_short}' downloaded successfully!"
            self.snackbar.content = ft.Text(success_msg)
            self.snackbar.bgcolor = theme.SUCCESS_COLOR
            page.open(self.snackbar)
            
        except Exception as e:
            print(f"Error downloading {track_data.title_short}: {e}")
            error_msg = self.translator.t("artist.error_download", title=track_data.title_short, error=str(e)) if self.translator else f"Error downloading '{track_data.title_short}': {e}"
            self.snackbar.content = ft.Text(error_msg)
            self.snackbar.bgcolor = theme.ERROR_COLOR
            page.open(self.snackbar)


