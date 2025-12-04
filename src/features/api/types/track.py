from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class Album(BaseModel):
    id: int
    title: str
    cover: HttpUrl
    cover_small: HttpUrl
    cover_medium: HttpUrl
    cover_big: HttpUrl
    cover_xl: HttpUrl
    md5_image: str
    tracklist: HttpUrl
    type: str

class Artist(BaseModel):
    id: int
    name: str
    link: HttpUrl
    picture: HttpUrl
    picture_small: HttpUrl
    picture_medium: HttpUrl
    picture_big: HttpUrl
    picture_xl: HttpUrl
    tracklist: HttpUrl
    type: str


class Track(BaseModel):
    id: int
    readable: bool
    title: str
    title_short: str
    title_version: str
    link: HttpUrl
    duration: int
    rank: int
    explicit_lyrics: bool
    explicit_content_lyrics: int
    explicit_content_cover: int
    preview: Optional[HttpUrl]
    md5_image: Optional[str]
    artist: Artist
    album: Album
    type: str


class TrackSearchResponse(BaseModel):
    data: List[Track]
    next: Optional[str] = None
    total: Optional[int] = None