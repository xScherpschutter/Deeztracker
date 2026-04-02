import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { useNotificationStore } from '../../../stores/useNotificationStore';
import { useI18n } from 'vue-i18n';
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
  track_id: string | null;
}

export const useDownloadStore = defineStore('download', () => {
  const downloadedTracks = ref<Track[]>([]);
  const downloadedTrackIds = ref<Set<string>>(new Set());
  const activeDownloads = ref<Map<string, string>>(new Map());
  const batchProgress = ref<BatchProgress | null>(null);
  const isInitialized = ref(false);
  const { t } = useI18n();

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
      const notificationStore = useNotificationStore();
      
      if (status === 'completed') {
        activeDownloads.value.delete(track_id);
        await loadDownloadedTracks(); 
        
        // Only notify if there's NO batch progress to avoid overlapping
        if (!batchProgress.value) {
          const track = downloadedTracks.value.find(t => String(t.ids.deezer) === track_id);
          if (track) {
            notificationStore.notify(t('playback.download_success', { name: track.title }), 'success');
          } else {
            notificationStore.notify(t('playback.downloaded'), 'success');
          }
        }
      } else if (status === 'error') {
        activeDownloads.value.set(track_id, 'error');
        notificationStore.notify(`${t('playback.download_error')}: ${error || 'Unknown'}`, 'error');
      } else {
        activeDownloads.value.set(track_id, status);
      }
    });

    // Listen for batch progress (Album/Playlist)
    await listen<BatchProgress>('batch-progress', (event) => {
      const payload = event.payload;

      // Ensure we have a valid batchProgress state
      if (!batchProgress.value) {
        batchProgress.value = { 
          total: payload.total,
          current: payload.current,
          failed: payload.failed,
          track_id: null 
        };
      } else {
        // Only update if the new current or failed is greater or equal to the current ones
        // to prevent UI flicker/reversion if events arrive out of order
        const newCurrent = Math.max(batchProgress.value.current, payload.current);
        const newFailed = Math.max(batchProgress.value.failed, payload.failed);

        batchProgress.value = {
          total: payload.total,
          current: newCurrent,
          failed: newFailed,
          track_id: batchProgress.value.track_id
        };
      }

      // Use the local variables for the finish check to avoid null issues
      const bp = batchProgress.value;
      if (!bp) return;

      const isFinished = bp.total > 0 && (bp.current >= bp.total);

      if (isFinished) {
        const notificationStore = useNotificationStore();
        if (bp.failed > 0) {
          notificationStore.notify(t('playback.batch_download_finished_errors', { n: bp.failed }), 'info');
        } else {
          notificationStore.notify(t('playback.batch_download_completed'), 'success');
        }

        // Delay clearing progress to allow the UI to show completion
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
    if (batchProgress.value) return; // Prevent multiple batch downloads
    
    const idStr = String(albumId);
    try {
      batchProgress.value = { current: 0, total: 0, failed: 0, track_id: idStr };
      await invoke('download_album_node', { albumId: idStr });
    } catch (e) {
      batchProgress.value = null;
      console.error('Album download command failed', e);
    }
  }

  async function downloadPlaylist(playlistId: string | number) {
    if (batchProgress.value) return; // Prevent multiple batch downloads
    
    const idStr = String(playlistId);
    try {
      batchProgress.value = { current: 0, total: 0, failed: 0, track_id: idStr };
      await invoke('download_playlist_node', { playlistId: idStr });
    } catch (e) {
      batchProgress.value = null;
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
