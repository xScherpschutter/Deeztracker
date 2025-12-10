import flet as ft
from ui import theme
import os
import sys
import hashlib
import tempfile
import mutagen
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from mutagen.flac import FLAC
from features.downloader.utils import get_os_name, get_music_folder, get_deeztracker_music_folder, get_custom_music_folder

# Cover cache directory
COVER_CACHE_DIR = os.path.join(tempfile.gettempdir(), "deeztracker_covers")
os.makedirs(COVER_CACHE_DIR, exist_ok=True)

def get_music_directories(custom_path: str = None):
    directories = []
    
    if custom_path and os.path.exists(custom_path):
        directories.append(custom_path)
    else:
        directories.append(get_deeztracker_music_folder())  
    
    directories.append(get_music_folder())  
    
    user_home = os.path.expanduser("~")
    
    if get_os_name() == "windows":
        # Windows additional paths
        directories.extend([
            os.path.join(user_home, "Downloads"),
            os.path.join(user_home, "OneDrive", "Music"),
            os.path.join(user_home, "OneDrive", "Música"),
        ])
    else:
        # Linux / macOS additional paths
        directories.extend([
            os.path.join(user_home, "Downloads"),
        ])
    
    # Remove duplicates and non-existent dirs
    return list(set(d for d in directories if os.path.exists(d)))


class LocalView(ft.View):
    def __init__(self, app_state):
        super().__init__(route="/local", bgcolor=theme.BG_COLOR)
        self.app_state = app_state
        self.player_manager = app_state["player_manager"]
        self.custom_music_path = None  # Will be loaded from storage
        
        self.music_files = []
        self.filtered_files = []
        self.tracks_column = ft.ListView(spacing=5, expand=True, padding=ft.padding.only(bottom=100))
        
        self.search_field = ft.TextField(
            hint_text="Buscar en música local...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self.filter_tracks,
            border_color=theme.ACCENT_COLOR,
            text_style=ft.TextStyle(color=theme.PRIMARY_TEXT),
            on_focus=lambda e: self.app_state.__setitem__("search_field_focused", True),
            on_blur=lambda e: self.app_state.__setitem__("search_field_focused", False)
        )

        # OS Info display
        os_name = "Windows" if sys.platform == "win32" else "Linux/macOS"
        self.os_info = ft.Text(f"Sistema: {os_name}", size=12, color=theme.SECONDARY_TEXT)
        self.scan_info = ft.Text("", size=12, color=theme.SECONDARY_TEXT)

        self.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row([
                            ft.Text("Encuentra tu música", size=24, weight=ft.FontWeight.BOLD, color=theme.PRIMARY_TEXT),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.Icons.REFRESH,
                                icon_color=theme.ACCENT_COLOR,
                                tooltip="Reescanear música",
                                on_click=lambda e: self.page.run_task(self.load_local_music)
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row([self.os_info, self.scan_info], spacing=20),
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
        self.page.run_task(self.load_and_scan_music)

    async def load_and_scan_music(self):
        # Load custom music path from storage
        self.custom_music_path = await self.page.client_storage.get_async("music_folder_path")
        await self.load_local_music()

    def _scan_directories_sync(self, scan_dirs):
        """Synchronous file scanning - runs in a separate thread."""
        music_files = []
        seen_paths = set()  # Track already-added files to avoid duplicates
        
        for directory in scan_dirs:
            try:
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        if file.lower().endswith(('.mp3', '.flac', '.wav', '.m4a', '.ogg', '.wma')):
                            full_path = os.path.normpath(os.path.join(root, file))
                            
                            # Skip if already added (handles overlapping directories)
                            if full_path in seen_paths:
                                continue
                            seen_paths.add(full_path)
                            
                            try:
                                metadata = self.get_metadata(full_path)
                                music_files.append(metadata)
                            except Exception as e:
                                print(f"Error reading file {full_path}: {e}")
                                music_files.append({
                                    "path": full_path,
                                    "title": os.path.splitext(os.path.basename(full_path))[0],
                                    "artist": "Unknown",
                                    "album": "Unknown",
                                    "cover": ""
                                })
            except PermissionError:
                print(f"No permissions to access: {directory}")
            except Exception as e:
                print(f"Error scanning {directory}: {e}")
        
        return music_files

    async def load_local_music(self):
        import asyncio
        
        self.tracks_column.controls.clear()
        self.tracks_column.controls.append(
            ft.Row([
                ft.ProgressRing(width=20, height=20, stroke_width=2),
                ft.Text("Scanning music files...", color=theme.SECONDARY_TEXT)
            ], spacing=10)
        )
        self.update()
        
        # Get OS-specific directories with custom path
        scan_dirs = get_music_directories(self.custom_music_path)
        self.scan_info.value = f"Scanning {len(scan_dirs)} directories..."
        self.update()
        
        # Run blocking file scan in a separate thread
        try:
            self.music_files = await asyncio.to_thread(self._scan_directories_sync, scan_dirs)
        except Exception as e:
            print(f"Error in file scanning: {e}")
            self.music_files = []
        
        self.scan_info.value = f"Total: {len(self.music_files)} files found"
        self.filtered_files = self.music_files
        self.update_list()

    def filter_tracks(self, e):
        query = self.search_field.value.lower()
        if not query:
            self.filtered_files = self.music_files
        else:
            self.filtered_files = [
                f for f in self.music_files 
                if query in f["title"].lower() or query in f["artist"].lower() or query in f["album"].lower()
            ]
        self.update_list()

    def update_list(self):
        self.tracks_column.controls.clear()
        
        if not self.filtered_files:
            self.tracks_column.controls.append(
                ft.Column([
                    ft.Icon(ft.Icons.MUSIC_OFF, size=48, color=theme.SECONDARY_TEXT),
                    ft.Text("No music files found.", color=theme.SECONDARY_TEXT),
                    ft.Text("Files must be in the system Music folders.", 
                            color=theme.SECONDARY_TEXT, size=12)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
            )
        else:
            for track in self.filtered_files:
                # Use cover image if available, otherwise icon placeholder
                cover = track.get("cover", "")
                if cover and os.path.exists(cover):
                    leading_control = ft.Image(
                        src=cover,
                        width=50,
                        height=50,
                        fit=ft.ImageFit.COVER,
                        border_radius=5
                    )
                else:
                    leading_control = ft.Container(
                        content=ft.Icon(ft.Icons.MUSIC_NOTE, color=theme.ACCENT_COLOR),
                        width=50,
                        height=50,
                        bgcolor=theme.CONTENT_BG,
                        border_radius=5,
                        alignment=ft.alignment.center
                    )

                self.tracks_column.controls.append(
                    ft.ListTile(
                        leading=leading_control,
                        title=ft.Text(track["title"], color=theme.PRIMARY_TEXT, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        subtitle=ft.Text(f"{track['artist']} • {track['album']}", color=theme.SECONDARY_TEXT, size=12, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        on_click=lambda e, t=track: self.play_track(t)
                    )
                )
        
        self.tracks_column.update()

    def get_metadata(self, file_path):
        """Extract metadata and cover art from audio file. Cover is cached to temp file."""
        title = os.path.splitext(os.path.basename(file_path))[0]
        artist = "Unknown"
        album = "Unknown"
        cover = ""
        
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
                
                # Cover Art - save to cache file
                cover = self._extract_cover(audio, file_path)

        except Exception as e:
            print(f"Error extracting metadata for {file_path}: {e}")
            
        return {
            "path": file_path,
            "title": title,
            "artist": artist,
            "album": album,
            "cover": cover
        }

    def _extract_cover(self, audio, file_path):
        """Extract cover art and save to cache file. Returns file path or empty string."""
        # Generate unique filename from file path hash
        path_hash = hashlib.md5(file_path.encode()).hexdigest()[:16]
        cover_path = os.path.join(COVER_CACHE_DIR, f"{path_hash}.jpg")
        
        # Check if already cached
        if os.path.exists(cover_path):
            return cover_path
        
        cover_data = None
        
        try:
            # MP3 (ID3)
            if isinstance(audio, MP3) and audio.tags:
                for tag in audio.tags.values():
                    if isinstance(tag, APIC):
                        cover_data = tag.data
                        break
            # FLAC
            elif isinstance(audio, FLAC):
                if audio.pictures:
                    cover_data = audio.pictures[0].data
            
            # Save to file if cover found
            if cover_data:
                with open(cover_path, 'wb') as f:
                    f.write(cover_data)
                return cover_path
                
        except Exception as e:
            print(f"Error extracting cover for {file_path}: {e}")
        
        return ""

    def play_track(self, track):
        self.player_manager.play_track(track, self.filtered_files)
        self.page.go("/player")
