import flet as ft
from ui import theme
from ui.components import appbar, list_items

class SearchView(ft.View):
    def __init__(self, app_state):
        super().__init__(route="/search", bgcolor=theme.BG_COLOR)
        self.app_state = app_state
        self.api = app_state["api"]
        self.next_url = None
        self.current_query = ""
        self.current_tab_index = 0

        self.search_field = ft.TextField(
            hint_text="Busca un artista, álbum, canción...",
            on_submit=self.perform_search,
            border_radius=10,
            border_color=theme.ACCENT_COLOR,
            autofocus=True,
        )

        self.snackbar = ft.SnackBar(content=ft.Text(""))
        
        self.results_column = ft.ListView(
            spacing=10,
            expand=True,
            padding=ft.padding.only(bottom=100) # Add padding for MiniPlayer
        )

        self.progress_container = ft.Container(
            content=ft.ProgressRing(),
            alignment=ft.alignment.center,
            visible=False # Inicialmente invisible
        )

        self.load_more_button = ft.ElevatedButton(
            text="Cargar más",
            on_click=self.load_more,
            visible=False,
            bgcolor=theme.ACCENT_COLOR,
            color=theme.PRIMARY_TEXT
        )
        
        self.load_more_container = ft.Container(
            content=self.load_more_button,
            alignment=ft.alignment.center,
            padding=10
        )
        
        self.search_tabs = ft.Tabs(
            selected_index=0,
            on_change=self.tab_changed,
            tabs=[
                ft.Tab("Artista"),
                ft.Tab("Álbum"),
                ft.Tab("Canción"),
                ft.Tab("Playlist"),
            ],
            indicator_color=theme.ACCENT_COLOR,
        )

        self.controls = [
            ft.Column([
                self.search_field,
                self.search_tabs,
                ft.Stack(
                    [
                        self.results_column,
                        self.progress_container
                    ],
                    expand=True
                ),
            ], expand=True, spacing=10, alignment=ft.MainAxisAlignment.START)
        ]

    async def download_track(self, page: ft.Page, track_data):
        downloader = self.app_state["downloader"]
        self.snackbar.content = ft.Text(f"Iniciando descarga de '{track_data.title}'...")
        page.open(ft.SnackBar(ft.Text(f"Iniciando descarga de '{track_data.title}'...")))   

        try:
            download_format = await page.client_storage.get_async("download_format")
            download_quality = await page.client_storage.get_async("download_quality")
            await downloader.download_track(track_data.link, convert_to=download_format, quality_download=download_quality)
            self.snackbar.content = ft.Text(f"'{track_data.title}' descargado con éxito!")
            self.snackbar.bgcolor = theme.SUCCESS_COLOR
            page.open(self.snackbar)
            
        except Exception as e:
            print(f"Error al descargar {track_data.title}: {e}")
            self.snackbar.content = ft.Text(f"Error al descargar '{track_data.title}': {e}")
            self.snackbar.bgcolor = theme.ERROR_COLOR
            page.open(self.snackbar)

    async def perform_search(self, e):
        """Ejecuta la búsqueda cuando el usuario presiona Enter."""
        query = self.search_field.value.strip()
        if not query:
            return

        self.results_column.controls.clear()
        self.results_column.controls.append(ft.Text("Buscando...", color=theme.SECONDARY_TEXT))
        self.progress_container.visible = True
        self.load_more_button.visible = False
        self.current_query = query
        self.update()

        try:
            selected_tab = self.search_tabs.selected_index
            item_type = ""
            response = None
            on_download = None

            if selected_tab == 0:
                item_type = "artist"
                response = await self.api.search_artists(query)
            elif selected_tab == 1:
                item_type = "album"
                response = await self.api.search_albums(query)
            elif selected_tab == 2:
                item_type = "track"
                response = await self.api.search_tracks(query)
                on_download = self.download_track
            elif selected_tab == 3:
                item_type = "playlist"
                response = await self.api.search_playlists(query)

            self.current_tab_index = selected_tab

            self.results_column.controls.clear()
            if response and response.data:
                for item in response.data:
                    self.results_column.controls.append(
                        list_items.SearchResultItem(
                            page=self.page, 
                            item_data=item, 
                            item_type=item_type,
                            on_download=on_download
                        )
                    )
            else:
                self.results_column.controls.append(
                    ft.Text("No se encontraron resultados.", color=theme.SECONDARY_TEXT)
                )
            
            if response and response.next:
                self.next_url = response.next
                self.results_column.controls.append(self.load_more_container)
                self.load_more_button.visible = True
            else:
                self.next_url = None
                self.load_more_button.visible = False

        except Exception as ex:
            print(f"Error en la búsqueda: {ex}")
            self.results_column.controls.clear()
            self.results_column.controls.append(
                ft.Text("Error al realizar la búsqueda.", color=theme.ERROR_COLOR)
            )
        finally:
            self.progress_container.visible = False
            self.update()

    async def load_more(self, e):
        if not self.next_url:
            return

        self.load_more_button.disabled = True
        self.load_more_button.text = "Cargando..."
        # Remove button temporarily to avoid duplicates or issues during update
        if self.load_more_container in self.results_column.controls:
            self.results_column.controls.remove(self.load_more_container)
        self.update()

        try:
            selected_tab = self.current_tab_index
            item_type = ""
            response = None
            on_download = None

            if selected_tab == 0:
                item_type = "artist"
                response = await self.api.search_artists(self.current_query, next=self.next_url)
            elif selected_tab == 1:
                item_type = "album"
                response = await self.api.search_albums(self.current_query, next=self.next_url)
            elif selected_tab == 2:
                item_type = "track"
                response = await self.api.search_tracks(self.current_query, next=self.next_url)
                on_download = self.download_track
            elif selected_tab == 3:
                item_type = "playlist"
                response = await self.api.search_playlists(self.current_query, next=self.next_url)

            if response and response.data:
                for item in response.data:
                    self.results_column.controls.append(
                        list_items.SearchResultItem(
                            page=self.page, 
                            item_data=item, 
                            item_type=item_type,
                            on_download=on_download
                        )
                    )
            
            if response and response.next:
                self.next_url = response.next
                self.results_column.controls.append(self.load_more_container)
                self.load_more_button.visible = True
            else:
                self.next_url = None
                self.load_more_button.visible = False

        except Exception as ex:
            print(f"Error al cargar más resultados: {ex}")
            self.page.open(ft.SnackBar(ft.Text(f"Error al cargar más resultados: {ex}", color=theme.ERROR_COLOR)))
        finally:
            self.load_more_button.disabled = False
            self.load_more_button.text = "Cargar más"
            self.update()

    async def tab_changed(self, e):
        """Vuelve a ejecutar la búsqueda si hay texto cuando se cambia de tab."""
        if self.search_field.value.strip():
            await self.perform_search(e)
