import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { useNotificationStore } from '../../../stores/useNotificationStore';
import type { Track } from '../../search/models/search';

// Corregido: Coincidir con los nombres de campos de Rust (snake_case por defecto en Tauri)
export interface DownloadProgress {
  track_id: string;
  status: 'pending' | 'downloading' | 'completed' | 'error';
  error: string | null;
}

export interface BatchProgress {
  total: number;
  current: number;
  failed: number;
}

export const useDownloadStore = defineStore('download', () => {
  const downloadedTracks = ref<Track[]>([]);
  const downloadedTrackIds = ref<Set<string>>(new Set());
  const activeDownloads = ref<Map<string, string>>(new Map());
  const batchProgress = ref<BatchProgress | null>(null);
  const isInitialized = ref(false);

  // Initialize and load downloaded track list
  async function init() {
    if (isInitialized.value) return;
    
    try {
      await loadDownloadedTracks();
      await setupListeners();
      isInitialized.value = true;
    } catch (e) {
      console.error('Failed to initialize DownloadStore', e);
    }
  }

  async function loadDownloadedTracks() {
    try {
      const tracks = await invoke<Track[]>('get_downloads');
      downloadedTracks.value = tracks;
      // Aseguramos que los IDs en el Set sean strings
      downloadedTrackIds.value = new Set(
        tracks.map(t => String(t.ids.deezer)).filter(id => id !== 'undefined' && id !== 'null')
      );
    } catch (e) {
      console.error('Failed to load downloaded tracks', e);
    }
  }

  async function checkIntegrity() {
    try {
      await invoke('check_downloads_integrity');
      await loadDownloadedTracks();
    } catch (e) {
      console.error('Failed to check downloads integrity', e);
    }
  }

  async function setupListeners() {
    // Listen for individual track progress
    await listen<DownloadProgress>('download-progress', async (event) => {
      const { track_id, status, error } = event.payload;
      
      if (status === 'completed') {
        activeDownloads.value.delete(track_id);
        await loadDownloadedTracks(); 
      } else if (status === 'error') {
        activeDownloads.value.set(track_id, 'error');
        const notificationStore = useNotificationStore();
        notificationStore.notify(`Error al descargar: ${error}`, 'error');
      } else {
        activeDownloads.value.set(track_id, status);
      }
    });

    // Listen for batch progress (Album/Playlist)
    await listen<BatchProgress>('batch-progress', (event) => {
      batchProgress.value = event.payload;
      
      if (event.payload.current === event.payload.total) {
        setTimeout(() => {
          batchProgress.value = null;
        }, 3000);
      }
    });
  }

  // Actions
  async function downloadTrack(trackId: string | number) {
    const idStr = String(trackId);
    if (downloadedTrackIds.value.has(idStr) || activeDownloads.value.has(idStr)) return;
    
    try {
      activeDownloads.value.set(idStr, 'pending');
      await invoke('download_track_node', { trackId: idStr });
    } catch (e) {
      activeDownloads.value.delete(idStr);
      console.error('Download command failed', e);
    }
  }

  async function downloadAlbum(albumId: string | number) {
    try {
      await invoke('download_album_node', { albumId: String(albumId) });
    } catch (e) {
      console.error('Album download command failed', e);
    }
  }

  async function downloadPlaylist(playlistId: string | number) {
    try {
      await invoke('download_playlist_node', { playlistId: String(playlistId) });
    } catch (e) {
      console.error('Playlist download command failed', e);
    }
  }

  async function cancelAll() {
    try {
      await invoke('cancel_all_downloads');
      activeDownloads.value.clear();
      batchProgress.value = null;
    } catch (e) {
      console.error('Failed to cancel downloads', e);
    }
  }

  // Getters
  const isDownloaded = (trackId: string | number | undefined) => {
    if (!trackId) return false;
    return downloadedTrackIds.value.has(String(trackId));
  };

  const getDownloadStatus = (trackId: string | number | undefined) => {
    if (!trackId) return null;
    return activeDownloads.value.get(String(trackId)) || null;
  };

  const isDownloading = (trackId: string | number | undefined) => {
    const status = getDownloadStatus(trackId);
    return status === 'downloading' || status === 'pending';
  };

  return {
    downloadedTracks: computed(() => downloadedTracks.value),
    downloadedTrackIds: computed(() => downloadedTrackIds.value),
    activeDownloads: computed(() => activeDownloads.value),
    batchProgress,
    init,
    loadDownloadedTracks,
    checkIntegrity,
    downloadTrack,
    downloadAlbum,
    downloadPlaylist,
    cancelAll,
    isDownloaded,
    getDownloadStatus,
    isDownloading
  };
});
