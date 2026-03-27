import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { useNotificationStore } from '../../../stores/useNotificationStore';
import type { Track } from '../../search/models/search';

export interface DownloadProgress {
  trackId: string;
  status: 'pending' | 'downloading' | 'completed' | 'error';
  error: string | null;
}

export interface BatchProgress {
  total: number;
  current: number;
  failed: number;
}

export const useDownloadStore = defineStore('download', () => {
  const downloadedTrackIds = ref<Set<string>>(new Set());
  const activeDownloads = ref<Map<string, string>>(new Map());
  const batchProgress = ref<BatchProgress | null>(null);
  const isInitialized = ref(false);

  // Initialize and load downloaded track list
  async function init() {
    if (isInitialized.value) return;
    
    try {
      const tracks = await invoke<Track[]>('get_downloads');
      downloadedTrackIds.value = new Set(tracks.map(t => t.ids.deezer).filter(Boolean) as string[]);
      
      // Setup event listeners
      await setupListeners();
      
      isInitialized.value = true;
    } catch (e) {
      console.error('Failed to initialize DownloadStore', e);
    }
  }

  async function setupListeners() {
    // Listen for individual track progress
    await listen<DownloadProgress>('download-progress', (event) => {
      const { trackId, status, error } = event.payload;
      
      if (status === 'completed') {
        activeDownloads.value.delete(trackId);
        downloadedTrackIds.value.add(trackId);
      } else if (status === 'error') {
        activeDownloads.value.set(trackId, 'error');
        const notificationStore = useNotificationStore();
        notificationStore.notify(`Error al descargar track ${trackId}: ${error}`, 'error');
      } else {
        activeDownloads.value.set(trackId, status);
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
  async function downloadTrack(trackId: string) {
    if (downloadedTrackIds.value.has(trackId) || activeDownloads.value.has(trackId)) return;
    
    try {
      activeDownloads.value.set(trackId, 'pending');
      await invoke('download_track_node', { trackId });
    } catch (e) {
      activeDownloads.value.delete(trackId);
      console.error('Download command failed', e);
    }
  }

  async function downloadAlbum(albumId: string) {
    try {
      await invoke('download_album_node', { albumId });
    } catch (e) {
      console.error('Album download command failed', e);
    }
  }

  async function downloadPlaylist(playlistId: string) {
    try {
      await invoke('download_playlist_node', { playlistId });
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
  const isDownloaded = (trackId: string | undefined) => {
    if (!trackId) return false;
    return downloadedTrackIds.value.has(trackId);
  };

  const getDownloadStatus = (trackId: string | undefined) => {
    if (!trackId) return null;
    return activeDownloads.value.get(trackId) || null;
  };

  const isDownloading = (trackId: string | undefined) => {
    const status = getDownloadStatus(trackId);
    return status === 'downloading' || status === 'pending';
  };

  return {
    downloadedTrackIds: computed(() => downloadedTrackIds.value),
    activeDownloads: computed(() => activeDownloads.value),
    batchProgress,
    init,
    downloadTrack,
    downloadAlbum,
    downloadPlaylist,
    cancelAll,
    isDownloaded,
    getDownloadStatus,
    isDownloading
  };
});
