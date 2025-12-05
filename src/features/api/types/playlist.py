from typing import List, Optional
from pydantic import BaseModel

class PlaylistUser(BaseModel):
    id: int
    name: str
    tracklist: str
    type: str  


class Playlist(BaseModel):
    id: int
    title: str
    link: str
    picture: Optional[str]
    picture_small: Optional[str]
    picture_medium: Optional[str]
    picture_big: Optional[str]
    picture_xl: Optional[str]
    picture_type: Optional[str]
    md5_image: Optional[str]
    nb_tracks: int
    creation_date: str
    mod_date: str
    add_date: str
    public: bool
    checksum: str
    tracklist: str
    type: str
    user: Optional[PlaylistUser] = None

class PlaylistSearchResponse(BaseModel):
    data: List[Playlist]
    total: Optional[int] = None
    next: Optional[str] = None
