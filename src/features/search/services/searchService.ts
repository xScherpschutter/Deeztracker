import { invoke } from '@tauri-apps/api/core';
import type { Track, Album, Artist, Playlist } from '../models/search';

export class SearchService {
  static async searchTracks(query: string, limit: number = 20, index: number = 0): Promise<Track[]> {
    if (!query.trim()) return [];
    return await invoke<Track[]>('search_tracks', { query, limit, index });
  }

  static async searchAlbums(query: string, limit: number = 20, index: number = 0): Promise<Album[]> {
    if (!query.trim()) return [];
    return await invoke<Album[]>('search_albums', { query, limit, index });
  }

  static async searchArtists(query: string, limit: number = 20, index: number = 0): Promise<Artist[]> {
    if (!query.trim()) return [];
    return await invoke<Artist[]>('search_artists', { query, limit, index });
  }

  static async searchPlaylists(query: string, limit: number = 20, index: number = 0): Promise<Playlist[]> {
    if (!query.trim()) return [];
    return await invoke<Playlist[]>('search_playlists', { query, limit, index });
  }

  static async searchAll(query: string, limit: number = 10): Promise<{
    tracks: Track[];
    albums: Album[];
    artists: Artist[];
    playlists: Playlist[];
  }> {
    if (!query.trim()) return { tracks: [], albums: [], artists: [], playlists: [] };

    const [tracks, albums, artists, playlists] = await Promise.all([
      this.searchTracks(query, limit, 0),
      this.searchAlbums(query, limit, 0),
      this.searchArtists(query, limit, 0),
      this.searchPlaylists(query, limit, 0)
    ]);

    return { tracks, albums, artists, playlists };
  }

  static async getAlbum(id: string): Promise<Album> {
    return await invoke<Album>('get_album', { id });
  }

  static async getArtist(id: string): Promise<Artist> {
    return await invoke<Artist>('get_artist', { id });
  }

  static async getPlaylist(id: string): Promise<Playlist> {
    return await invoke<Playlist>('get_playlist', { id });
  }

  static async getArtistTopTracks(id: string, limit: number = 10): Promise<Track[]> {
    return await invoke<Track[]>('get_artist_top_tracks', { id, limit });
  }

  static async getArtistAlbums(id: string, limit: number = 20): Promise<Album[]> {
    return await invoke<Album[]>('get_artist_albums', { id, limit });
  }
}
