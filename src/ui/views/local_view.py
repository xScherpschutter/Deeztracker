import flet as ft
from ui import theme
import os
import base64
import mutagen
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
from mutagen.flac import FLAC, Picture
from ui.components import list_items

class LocalView(ft.View):
    def __init__(self, app_state):
        super().__init__(route="/local", bgcolor=theme.BG_COLOR)
        self.app_state = app_state
        self.player_manager = app_state["player_manager"]
        
        self.music_files = []
        self.filtered_files = []
        self.filtered_files = []
        self.tracks_column = ft.ListView(spacing=5, expand=True, padding=ft.padding.only(bottom=100))
        
        self.search_field = ft.TextField(
            hint_text="Buscar en música local...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self.filter_tracks,
            border_color=theme.ACCENT_COLOR,
            text_style=ft.TextStyle(color=theme.PRIMARY_TEXT),
        )

        self.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Música Local", size=24, weight=ft.FontWeight.BOLD, color=theme.PRIMARY_TEXT),
                        self.search_field,
                        ft.Divider(color=theme.ACCENT_COLOR),
                        self.tracks_column
                    ],
                    expand=True,
                ),
                padding=20,
                expand=True
            )
        ]

    def did_mount(self):
        self.page.run_task(self.load_local_music)

    async def load_local_music(self):
        self.tracks_column.controls.clear()
        self.tracks_column.controls.append(ft.Text("Escaneando archivos...", color=theme.SECONDARY_TEXT))
        self.update()
        
        # Directories to scan
        scan_dirs = [
            "./music_downloads",
            os.path.expanduser("~/Music"),
            os.path.expanduser("~/Música")
        ]
        
        self.music_files = []
        
        for directory in scan_dirs:
            if os.path.exists(directory):
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        if file.lower().endswith(('.mp3', '.flac', '.wav', '.m4a')):
                            full_path = os.path.join(root, file)
                            metadata = self.get_metadata(full_path)
                            self.music_files.append(metadata)
        
        self.filtered_files = self.music_files
        self.update_list()

    def filter_tracks(self, e):
        query = self.search_field.value.lower()
        if not query:
            self.filtered_files = self.music_files
        else:
            self.filtered_files = [
                f for f in self.music_files 
                if query in f["title"].lower() or query in f["artist"].lower()
            ]
        self.update_list()

    def update_list(self):
        self.tracks_column.controls.clear()
        
        if not self.filtered_files:
            self.tracks_column.controls.append(ft.Text("No se encontraron archivos de música.", color=theme.SECONDARY_TEXT))
        else:
            for track in self.filtered_files:
                # Determine leading control (Image or Icon)
                if track["cover"].startswith("data:image"):
                    leading_control = ft.Image(
                        src=track["cover"],
                        width=50,
                        height=50,
                        fit=ft.ImageFit.COVER,
                        border_radius=5
                    )
                else:
                    leading_control = ft.Icon(ft.Icons.MUSIC_NOTE, color=theme.ACCENT_COLOR)

                self.tracks_column.controls.append(
                    ft.ListTile(
                        leading=leading_control,
                        title=ft.Text(track["title"], color=theme.PRIMARY_TEXT, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        subtitle=ft.Text(f"{track['artist']} • {track['album']}", color=theme.SECONDARY_TEXT, size=12, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        on_click=lambda e, t=track: self.play_track(t)
                    )
                )
        
        self.update()

    def get_metadata(self, file_path):
        title = os.path.splitext(os.path.basename(file_path))[0]
        artist = "Desconocido"
        album = "Desconocido"
        cover = "https://via.placeholder.com/50"
        
        try:
            audio = mutagen.File(file_path)
            if audio:
                # Title
                if 'TIT2' in audio:
                    title = str(audio['TIT2'])
                elif 'title' in audio:
                    title = str(audio['title'][0])
                
                # Artist
                if 'TPE1' in audio:
                    artist = str(audio['TPE1'])
                elif 'artist' in audio:
                    artist = str(audio['artist'][0])
                
                # Album
                if 'TALB' in audio:
                    album = str(audio['TALB'])
                elif 'album' in audio:
                    album = str(audio['album'][0])
                
                # Cover Art
                # MP3 (ID3)
                if isinstance(audio, MP3) or isinstance(audio, ID3):
                    for tag in audio.tags.values():
                        if isinstance(tag, APIC):
                            cover_data = tag.data
                            base64_img = base64.b64encode(cover_data).decode('utf-8')
                            cover = f"data:image/jpeg;base64,{base64_img}"
                            break
                # FLAC
                elif isinstance(audio, FLAC):
                    if audio.pictures:
                        cover_data = audio.pictures[0].data
                        base64_img = base64.b64encode(cover_data).decode('utf-8')
                        cover = f"data:image/jpeg;base64,{base64_img}"

        except Exception as e:
            print(f"Error extracting metadata for {file_path}: {e}")
            
        return {
            "path": file_path,
            "title": title,
            "artist": artist,
            "album": album,
            "cover": cover
        }

    def play_track(self, track):
        self.player_manager.play_track(track, self.filtered_files)
        self.page.go("/player")
