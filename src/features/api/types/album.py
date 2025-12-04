from typing import List, Optional
from pydantic import BaseModel, HttpUrl


class Artist(BaseModel):
    id: int
    name: str
    link: Optional[str] = None
    picture: Optional[str]
    picture_small: Optional[str]
    picture_medium: Optional[str]
    picture_big: Optional[str]
    picture_xl: Optional[str]
    tracklist: Optional[str]
    type: str


class Album(BaseModel):
    id: int
    title: str
    link: str
    cover: Optional[str]
    cover_small: Optional[str]
    cover_medium: Optional[str]
    cover_big: Optional[str]
    cover_xl: Optional[str]
    md5_image: Optional[str]
    record_type: str                    
    explicit_lyrics: bool
    genre_id: Optional[int]
    nb_tracks: Optional[int]
    tracklist: Optional[str]
    type: str
    artist: Artist

class ArtistMini(BaseModel):
    id: int
    name: str
    link: Optional[HttpUrl] = None

class AlbumResponse(BaseModel):
    id: int
    title: str
    cover: Optional[HttpUrl]
    cover_small: Optional[HttpUrl]
    cover_medium: Optional[HttpUrl]
    cover_big: Optional[HttpUrl]
    cover_xl: Optional[HttpUrl]
    nb_tracks: Optional[int] = None
    record_type: Optional[str] = None
    artist: Optional[ArtistMini] = None
    release_date: Optional[str] = None
    tracklist: Optional[HttpUrl] = None
    type: Optional[str] = None

class AlbumSearchResponse(BaseModel):
    data: List[Album]
    next: Optional[str] = None
    total: Optional[int] = None          
           
class ArtistMiniAlbum(BaseModel):
    id: int
    name: str
    tracklist: Optional[HttpUrl] = None
    type: Optional[str] = None

class Track(BaseModel):
    id: int
    readable: bool
    title: str
    title_short: str
    title_version: Optional[str] = ''
    link: Optional[HttpUrl] = None
    duration: int
    rank: int
    explicit_lyrics: bool
    explicit_content_lyrics: Optional[int] = None
    explicit_content_cover: Optional[int] = None
    preview: Optional[HttpUrl] = None
    disk_number: Optional[int] = None
    track_position: Optional[int] = None
    md5_image: Optional[str] = None
    isrc: Optional[str] = None
    type: Optional[str] = None
    artist: ArtistMiniAlbum

class AlbumTracksResponse(BaseModel):
    data: List[Track]
