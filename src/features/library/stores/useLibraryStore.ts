import { defineStore } from 'pinia';
import { ref } from 'vue';
import { invoke } from '@tauri-apps/api/core';
import type { Track } from '../../search/models/search';
import { useNotificationStore } from '../../../stores/useNotificationStore';

export interface LocalPlaylist {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  preview_covers: string[];
}

export const useLibraryStore = defineStore('library', () => {
  const favorites = ref<Track[]>([]);
  const playlists = ref<LocalPlaylist[]>([]);
  const isLoading = ref(false);

  // Favorites
  async function loadFavorites() {
    try {
      favorites.value = await invoke<Track[]>('get_favorites');
    } catch (e) {
      console.error('Failed to load favorites', e);
    }
  }

  async function toggleFavorite(track: Track) {
    const notificationStore = useNotificationStore();
    try {
      const result = await invoke<Track | null>('toggle_favorite', { track });
      if (result) {
        // Add to local state with the backend-provided added_at timestamp
        favorites.value = [result, ...favorites.value];
        notificationStore.notify(`${track.title} añadido a favoritos`);
      } else {
        // Remove from local state
        favorites.value = favorites.value.filter(t => t.ids.deezer !== track.ids.deezer);
        notificationStore.notify(`${track.title} eliminado de favoritos`, 'info');
      }
      return !!result;
    } catch (e) {
      console.error('Failed to toggle favorite', e);
      return false;
    }
  }

  function isTrackFavorite(trackId: string | undefined): boolean {
    if (!trackId) return false;
    return favorites.value.some(t => t.ids.deezer === trackId);
  }

  // Playlists
  async function loadPlaylists() {
    try {
      playlists.value = await invoke<LocalPlaylist[]>('get_playlists');
    } catch (e) {
      console.error('Failed to load playlists', e);
    }
  }

  async function createPlaylist(name: string, description?: string) {
    const notificationStore = useNotificationStore();
    try {
      const id = await invoke<number>('create_playlist', { name, description });
      await loadPlaylists();
      notificationStore.notify(`Playlist "${name}" creada`);
      return id;
    } catch (e) {
      console.error('Failed to create playlist', e);
      notificationStore.notify('Error al crear la playlist', 'error');
      return null;
    }
  }

  async function deletePlaylist(id: number) {
    try {
      await invoke('delete_playlist', { id });
      playlists.value = playlists.value.filter(p => p.id !== id);
    } catch (e) {
      console.error('Failed to delete playlist', e);
    }
  }

  async function addTrackToPlaylist(playlistId: number, track: Track) {
    try {
      await invoke('add_track_to_playlist', { playlistId, track });
      await loadPlaylists(); // Refresh preview_covers
    } catch (e) {
      console.error('Failed to add track to playlist', e);
    }
  }

  async function removeTrackFromPlaylist(playlistId: number, trackId: string) {
    try {
      await invoke('remove_track_from_playlist', { playlistId, trackId });
      await loadPlaylists(); // Refresh preview_covers
    } catch (e) {
      console.error('Failed to remove track from playlist', e);
    }
  }

  async function getPlaylistTracks(playlistId: number): Promise<Track[]> {
    try {
      return await invoke<Track[]>('get_playlist_tracks', { playlistId });
    } catch (e) {
      console.error('Failed to get playlist tracks', e);
      return [];
    }
  }

  async function init() {
    isLoading.value = true;
    await Promise.all([loadFavorites(), loadPlaylists()]);
    isLoading.value = false;
  }

  return {
    favorites,
    playlists,
    isLoading,
    toggleFavorite,
    isTrackFavorite,
    loadFavorites,
    loadPlaylists,
    createPlaylist,
    deletePlaylist,
    addTrackToPlaylist,
    removeTrackFromPlaylist,
    getPlaylistTracks,
    init
  };
});
