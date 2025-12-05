import httpx
from features.api.types import *
from typing import List

class DeezerAPIService:
    BASE_URL = "https://api.deezer.com/"

    async def _request_query(self, endpoint: str, query: str = None, next: str = None):
        url = next if next else f"{self.BASE_URL}{endpoint}?q={query}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        
    async def _request(self, endpoint: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}{endpoint}")
            response.raise_for_status()
            return response.json()

    async def search_tracks(self, query: str, next: str = None) -> TrackSearchResponse:
        data = await self._request_query("search/track", query, next)
        return TrackSearchResponse(**data)

    async def search_albums(self, query: str, next: str = None) -> AlbumSearchResponse:
        data = await self._request_query("search/album", query, next)
        return AlbumSearchResponse(**data)
    
    
    async def search_artists(self, query: str, next: str = None) -> ArtistSearchResponse:
        data = await self._request_query("search/artist", query, next)
        return ArtistSearchResponse(**data)

    async def search_playlists(self, query: str, next: str = None) -> PlaylistSearchResponse:
        data = await self._request_query("search/playlist", query, next)
        return PlaylistSearchResponse(**data)
    
    async def get_artist_info(self, artist_id: str) -> Artist:
        data = await self._request(f"artist/{artist_id}")
        return Artist(**data)
    
    async def get_artist_albums(self, artist_id: str) -> List[AlbumResponse]:
        data = await self._request(f"artist/{artist_id}/albums")
        albums_data = data.get('data', []) 
        albums = [AlbumResponse(**album) for album in albums_data]
        return albums

    async def get_album_info(self, album_id: str) -> AlbumResponse:
        data = await self._request(f"album/{album_id}")
        return AlbumResponse(**data)

    async def get_album_tracks(self, album_id: str) -> AlbumTracksResponse:
        data = await self._request(f"album/{album_id}/tracks")
        return AlbumTracksResponse(**data)
        
    async def get_playlist_info(self, playlist_id: str) -> Playlist:
        data = await self._request(f"playlist/{playlist_id}")
        return Playlist(**data)
    
    async def get_playlist_tracks(self, playlist_id: str) -> AlbumTracksResponse:
        data = await self._request(f"playlist/{playlist_id}/tracks")
        return AlbumTracksResponse(**data)
