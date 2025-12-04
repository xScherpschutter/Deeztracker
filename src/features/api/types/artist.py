from typing import List, Optional
from pydantic import BaseModel

class Artist(BaseModel):
    id: int
    name: str
    link: str
    nb_album: int
    nb_fan: int
    picture: Optional[str]
    picture_small: Optional[str]
    picture_medium: Optional[str]
    picture_big: Optional[str]
    picture_xl: Optional[str]
    radio: bool
    tracklist: str
    type: str

class ArtistSearchResponse(BaseModel):
    data: List[Artist]
    total: Optional[int] = None
    next: Optional[str] = None