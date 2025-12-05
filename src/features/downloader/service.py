import asyncio
from deezspot import DeeLogin
from pydantic import HttpUrl
from features.downloader.utils import get_deeztracker_music_folder

class DeezloaderService:
    VALID_QUALITY_DOWNLOAD = ["FLAC", "MP3_320", "MP3_128"]
    VALID_CONVERT_TO = ["flac", "mp3-128", "mp3-320"]
    
    def __init__(self, arl: str, output_dir: str = None, quality_download: str = "FLAC", convert_to: str = "flac", recursive_quality: bool = True):
        self.deez: DeeLogin = DeeLogin(arl=arl)
        self.output_dir = output_dir if output_dir else get_deeztracker_music_folder()
        self.quality_download = quality_download if quality_download in self.VALID_QUALITY_DOWNLOAD else self.VALID_QUALITY_DOWNLOAD[0]
        self.recursive_quality = recursive_quality
        self.convert_to = convert_to if convert_to in self.VALID_CONVERT_TO else self.VALID_CONVERT_TO[0]
        
    async def download_track(self, track_url: str | HttpUrl, quality_download: str = None, convert_to: str = None) -> None:
        """Descarga una pista de forma asíncrona, ejecutando la llamada síncrona en un hilo."""
        
        q_download = quality_download if quality_download else self.quality_download
        c_to = convert_to if convert_to else self.convert_to
        print(f"Formato de descarga: {q_download}")
        print(f"Convertir a: {c_to}")
        
        try:
            await asyncio.to_thread(
                self.deez.download_trackdee,
                link_track=str(track_url),
                output_dir=self.output_dir,
                quality_download=q_download,
                convert_to=c_to,
                recursive_quality=self.recursive_quality
            )
            print(f"Descarga de pista completada: {track_url}")
        except Exception as e:
            print(f"Ocurrió un error en la descarga de la pista: {e}")
    
    async def download_album(self, album_url: str | HttpUrl, quality_download: str = None, convert_to: str = None) -> None:
        """Descarga un álbum de forma asíncrona, ejecutando la llamada síncrona en un hilo."""
        
        q_download = quality_download if quality_download else self.quality_download
        c_to = convert_to if convert_to else self.convert_to
        print(f"Formato de descarga: {q_download}")
        print(f"Convertir a: {c_to}")

        try:
            await asyncio.to_thread(
                self.deez.download_albumdee,
                link_album=str(album_url),
                output_dir=self.output_dir,
                quality_download=q_download,
                convert_to=c_to,
                recursive_quality=self.recursive_quality,
                make_zip=False
            )
            print(f"Descarga de álbum completada: {album_url}")
        except Exception as e:
            print(f"Ocurrió un error en la descarga del álbum: {e}")
    
    async def download_playlist(self, playlist_url: str | HttpUrl, quality_download: str = None, convert_to: str = None) -> None:
        """Descarga una playlist de forma asíncrona, ejecutando la llamada síncrona en un hilo."""
        
        q_download = quality_download if quality_download else self.quality_download
        c_to = convert_to if convert_to else self.convert_to

        try:
            await asyncio.to_thread(
                self.deez.download_playlistdee,
                link_playlist=str(playlist_url),
                output_dir=self.output_dir,
                quality_download=q_download,
                convert_to=c_to,
                recursive_quality=self.recursive_quality,
            )
            print(f"Descarga de playlist completada: {playlist_url}")
        except Exception as e:
            print(f"Ocurrió un error en la descarga de la playlist: {e}")