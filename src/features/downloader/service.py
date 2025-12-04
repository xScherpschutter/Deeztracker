from deezspot import DeeLogin

class DeezloaderService:
    VALID_QUALITY_DOWNLOAD = ["FLAC", "MP3_320", "MP3_128"]
    VALID_CONVERT_TO = ["flac", "mp3-128", "mp3-320"]
    
    def __init__(self, arl: str, output_dir: str = "./music_downloads", quality_download: str = "FLAC", convert_to: str = "flac", recursive_quality: bool = True):
        self.deez: DeeLogin = DeeLogin(arl=arl)
        self.output_dir = output_dir
        self.quality_download = quality_download if quality_download in self.VALID_QUALITY_DOWNLOAD else self.VALID_QUALITY_DOWNLOAD[0]
        self.recursive_quality = recursive_quality
        self.convert_to = convert_to if convert_to in self.VALID_CONVERT_TO else self.VALID_CONVERT_TO[0]
        
    def download_track(self, track_url: str) -> None:
        try:
            self.deez.download_trackdee(
                link_track=track_url,
                output_dir=self.output_dir,
                quality_download=self.quality_download,
                convert_to=self.convert_to,
                recursive_quality=self.recursive_quality
            )
        except Exception as e:
            print(f"An error occurred: {e}")
    
    def download_album(self, album_url: str) -> None:
        try:
            self.deez.download_albumdee(
                link_album=album_url,
                output_dir=self.output_dir,
                quality_download=self.quality_download,
                convert_to=self.convert_to,
                recursive_quality=self.recursive_quality,
            )
        except Exception as e:
            print(f"An error occurred: {e}")
    
    def download_playlist(self, playlist_url: str) -> None:
        try:
            self.deez.download_playlistdee(
                link_playlist=playlist_url,
                output_dir=self.output_dir,
                quality_download=self.quality_download,
                convert_to=self.convert_to,
                recursive_quality=self.recursive_quality,
            )
        except Exception as e:
            print(f"An error occurred: {e}")