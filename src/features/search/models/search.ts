export interface IDs {
  deezer?: string;
  isrc?: string;
  upc?: string;
}

export interface Image {
  url: string;
  width: number;
  height: number;
}

export interface ReleaseDate {
  year: number;
  month: number;
  day: number;
}

export interface Artist {
  type: string;
  name: string;
  genres: string[];
  images: Image[];
  ids: IDs;
  nb_album?: number;
  nb_fan?: number;
}

export interface ArtistTrack {
  type: string;
  name: string;
  ids: IDs;
}

export interface ArtistTrackAlbum {
  type: string;
  name: string;
  ids: IDs;
}

export interface TrackAlbum {
  type: string;
  title: string;
  disc_number: number;
  track_number: number;
  duration_ms: number;
  explicit: boolean;
  genres: string[];
  ids: IDs;
  artists: ArtistTrackAlbum[];
}

export interface AlbumTrack {
  type: string;
  album_type: string;
  title: string;
  release_date: ReleaseDate;
  total_tracks: number;
  total_discs: number;
  genres: string[];
  images: Image[];
  ids: IDs;
  artists: ArtistTrack[];
}

export interface Track {
  type: string;
  title: string;
  disc_number: number;
  track_number: number;
  duration_ms: number;
  explicit: boolean;
  genres: string[];
  album: AlbumTrack;
  artists: ArtistTrack[];
  ids: IDs;
  added_at?: string;
}

export interface Album {
  type: string;
  album_type: string;
  title: string;
  release_date: ReleaseDate;
  total_tracks: number;
  total_discs: number;
  genres: string[];
  images: Image[];
  ids: IDs;
  artists: ArtistTrack[];
  tracks: TrackAlbum[];
}

export interface Playlist {
  type: string;
  title: string;
  description: string;
  duration_ms: number;
  nb_tracks: number;
  public: boolean;
  images: Image[];
  ids: IDs;
  user?: {
    name: string;
    ids: IDs;
  };
  tracks: Track[];
}

export type SearchType = 'all' | 'tracks' | 'albums' | 'artists' | 'playlists';

export interface SearchResults {
  tracks: Track[];
  albums: Album[];
  artists: Artist[];
  playlists: Playlist[];
}
