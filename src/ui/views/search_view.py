import flet as ft
from ui import theme
from ui.components import appbar, list_items

class SearchView(ft.View):
    def __init__(self, app_state):
        super().__init__(route="/search", bgcolor=theme.BG_COLOR)
        self.app_state = app_state
        self.api = app_state["api"]
        self.translator = app_state.get("translator")
        self.next_url = None
        self.current_query = ""
        self.current_tab_index = 0

        self.search_field = ft.TextField(
            hint_text=self.translator.t("search.hint") if self.translator else "Search for an artist, album, song...",
            on_submit=self.perform_search,
            border_radius=10,
            border_color=theme.ACCENT_COLOR,
            autofocus=True,
            on_focus=lambda e: self.app_state.__setitem__("search_field_focused", True),
            on_blur=lambda e: self.app_state.__setitem__("search_field_focused", False)
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
            visible=False # Initially invisible
        )

        self.load_more_button = ft.ElevatedButton(
            text=self.translator.t("search.load_more") if self.translator else "Load more",
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
        
        # Empty state for when no search has been performed
        self.empty_state = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.SEARCH_ROUNDED,
                        size=80,
                        color=theme.SECONDARY_TEXT
                    ),
                    ft.Container(height=20),
                    ft.Text(
                        self.translator.t("search.title") if self.translator else "Discover your favorite music",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=theme.PRIMARY_TEXT,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        self.translator.t("search.subtitle") if self.translator else "Search for artists, albums, songs or playlists",
                        size=14,
                        color=theme.SECONDARY_TEXT,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=30),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(ft.Icons.TIPS_AND_UPDATES, size=20, color=theme.ACCENT_COLOR),
                                        ft.Text(self.translator.t("search.tip_search") if self.translator else "Type in the search bar above", size=13, color=theme.SECONDARY_TEXT)
                                    ],
                                    spacing=10
                                ),
                                ft.Container(height=8),
                                ft.Row(
                                    [
                                        ft.Icon(ft.Icons.TAB, size=20, color=theme.ACCENT_COLOR),
                                        ft.Text(self.translator.t("search.tip_tabs") if self.translator else "Select the search type", size=13, color=theme.SECONDARY_TEXT)
                                    ],
                                    spacing=10
                                ),
                                ft.Container(height=8),
                                ft.Row(
                                    [
                                        ft.Icon(ft.Icons.DOWNLOAD, size=20, color=theme.ACCENT_COLOR),
                                        ft.Text(self.translator.t("search.tip_download") if self.translator else "Download your favorite songs", size=13, color=theme.SECONDARY_TEXT)
                                    ],
                                    spacing=10
                                ),
                            ],
                            spacing=0
                        ),
                        padding=20,
                        border_radius=10,
                        bgcolor=ft.Colors.with_opacity(0.05, theme.ACCENT_COLOR)
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            alignment=ft.alignment.center,
            expand=True,
            visible=True  # Initially visible
        )
        
        self.search_tabs = ft.Tabs(
            selected_index=0,
            on_change=self.tab_changed,
            tabs=[
                ft.Tab(self.translator.t("search.tab_artist") if self.translator else "Artist"),
                ft.Tab(self.translator.t("search.tab_album") if self.translator else "Album"),
                ft.Tab(self.translator.t("search.tab_song") if self.translator else "Song"),
                ft.Tab(self.translator.t("search.tab_playlist") if self.translator else "Playlist"),
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
                        self.empty_state,
                        self.progress_container
                    ],
                    expand=True
                ),
            ], expand=True, spacing=10, alignment=ft.MainAxisAlignment.START)
        ]
        
        # Subscribe to language changes
        if self.translator:
            self.translator.subscribe(self.on_language_change)
    
    def on_language_change(self, language_code):
        """Called when the language changes."""
        if not self.translator:
            return
        
        # Update dynamic text elements
        self.search_field.hint_text = self.translator.t("search.hint")
        self.load_more_button.text = self.translator.t("search.load_more")
        
        # Update empty state
        self.empty_state.content.controls[2].value = self.translator.t("search.title")
        self.empty_state.content.controls[4].value = self.translator.t("search.subtitle")
        tips_column = self.empty_state.content.controls[6].content
        tips_column.controls[0].controls[1].value = self.translator.t("search.tip_search")
        tips_column.controls[2].controls[1].value = self.translator.t("search.tip_tabs")
        tips_column.controls[4].controls[1].value = self.translator.t("search.tip_download")
        
        # Update tabs
        self.search_tabs.tabs[0].text = self.translator.t("search.tab_artist")
        self.search_tabs.tabs[1].text = self.translator.t("search.tab_album")
        self.search_tabs.tabs[2].text = self.translator.t("search.tab_song")
        self.search_tabs.tabs[3].text = self.translator.t("search.tab_playlist")
        
        try:
            self.update()
        except:
            pass  # Ignore if view is not mounted

    async def download_track(self, page: ft.Page, track_data):
        downloader = self.app_state["downloader"]
        start_msg = self.translator.t("search.download_started", title=track_data.title) if self.translator else f"Starting download of '{track_data.title}'..."
        self.snackbar.content = ft.Text(start_msg)
        page.open(ft.SnackBar(ft.Text(start_msg)))   

        try:
            download_format = await page.client_storage.get_async("download_format")
            download_quality = await page.client_storage.get_async("download_quality")
            await downloader.download_track(track_data.link, convert_to=download_format, quality_download=download_quality)
            success_msg = self.translator.t("search.download_success", title=track_data.title) if self.translator else f"'{track_data.title}' downloaded successfully!"
            self.snackbar.content = ft.Text(success_msg)
            self.snackbar.bgcolor = theme.SUCCESS_COLOR
            page.open(self.snackbar)
            
        except Exception as e:
            print(f"Error downloading {track_data.title}: {e}")
            error_msg = self.translator.t("search.error_download", title=track_data.title, error=str(e)) if self.translator else f"Error downloading '{track_data.title}': {e}"
            self.snackbar.content = ft.Text(error_msg)
            self.snackbar.bgcolor = theme.ERROR_COLOR
            page.open(self.snackbar)

    async def perform_search(self, e):
        """Executes the search when the user presses Enter."""
        query = self.search_field.value.strip()
        if not query:
            return

        # Hide empty state and show loading
        self.empty_state.visible = False
        self.results_column.controls.clear()
        self.results_column.controls.append(ft.Text(self.translator.t("search.searching") if self.translator else "Searching...", color=theme.SECONDARY_TEXT))
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
                    ft.Text(self.translator.t("search.no_results") if self.translator else "No results found.", color=theme.SECONDARY_TEXT)
                )
            
            if response and response.next:
                self.next_url = response.next
                self.results_column.controls.append(self.load_more_container)
                self.load_more_button.visible = True
            else:
                self.next_url = None
                self.load_more_button.visible = False

        except Exception as ex:
            print(f"Error in search: {ex}")
            self.results_column.controls.clear()
            self.results_column.controls.append(
                ft.Text(self.translator.t("search.error") if self.translator else "Error performing search.", color=theme.ERROR_COLOR)
            )
        finally:
            self.progress_container.visible = False
            self.update()

    async def load_more(self, e):
        if not self.next_url:
            return

        self.load_more_button.disabled = True
        self.load_more_button.text = self.translator.t("search.loading_more") if self.translator else "Loading..."
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
            print(f"Error loading more results: {ex}")
            self.page.open(ft.SnackBar(ft.Text(f"Error loading more results: {ex}", color=theme.ERROR_COLOR)))
        finally:
            self.load_more_button.disabled = False
            self.load_more_button.text = self.translator.t("search.load_more") if self.translator else "Load more"
            self.update()

    async def tab_changed(self, e):
        """Re-executes the search if there is text when the tab is changed."""
        if self.search_field.value.strip():
            await self.perform_search(e)
