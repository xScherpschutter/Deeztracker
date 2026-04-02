import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Track } from '../../search/models/search';
import { PlaybackService } from '../services/playbackService';
import { SearchService } from '../../search/services/searchService';
import { useNotificationStore } from '../../../stores/useNotificationStore';
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { LrcParser, type LrcLine } from '../utils/lrcParser';
import { useI18n } from 'vue-i18n';

export const usePlaybackStore = defineStore('playback', () => {
  const { t } = useI18n();
  const notificationStore = useNotificationStore();

  // State
  const queue = ref<Track[]>([]);
  const currentIndex = ref(-1);
  const isPlaying = ref(false);
  const isBuffering = ref(false);
  const volume = ref(0.8);
  const progress = ref(0);
  const duration = ref(0);
  const repeatMode = ref<'off' | 'one' | 'all'>('off');
  const isShuffle = ref(false);
  const shuffledIndices = ref<number[]>([]);
  const lyrics = ref<LrcLine[]>([]);
  const isLoadingLyrics = ref(false);
  const showQueue = ref(false);
  const _listenersInitialized = ref(false);

  // Getters
  const currentTrack = computed(() => {
    if (currentIndex.value >= 0 && currentIndex.value < queue.value.length) {
      return queue.value[currentIndex.value];
    }
    return null;
  });

  const currentLineIndex = computed(() => {
    return LrcParser.getActiveLineIndex(lyrics.value, progress.value * 1000);
  });

  const hasNext = computed(() => {
    if (repeatMode.value === 'all') return queue.value.length > 0;
    return currentIndex.value < queue.value.length - 1;
  });

  const hasPrev = computed(() => {
    if (repeatMode.value === 'all') return queue.value.length > 0;
    return currentIndex.value > 0;
  });

  const nextTrackInQueue = computed((): Track | null => {
    if (queue.value.length === 0) return null;
    if (isShuffle.value) {
      const currentShufflePos = shuffledIndices.value.indexOf(currentIndex.value);
      if (currentShufflePos < shuffledIndices.value.length - 1) {
        return queue.value[shuffledIndices.value[currentShufflePos + 1]];
      } else if (repeatMode.value === 'all') {
        return queue.value[shuffledIndices.value[0]];
      }
    } else {
      if (currentIndex.value < queue.value.length - 1) {
        return queue.value[currentIndex.value + 1];
      } else if (repeatMode.value === 'all') {
        return queue.value[0];
      }
    }
    return null;
  });

  // Actions
  async function initMediaControls() {
    if (_listenersInitialized.value) return;
    _listenersInitialized.value = true;

    const handlePlay = () => { if (!isPlaying.value) togglePlay(); };
    const handlePause = () => { if (isPlaying.value) togglePlay(); };
    const handleToggle = () => { togglePlay(); };
    const handleNext = () => { next(); };
    const handlePrev = () => { prev(); };

    // 1. Listen to OS media control events from Rust (Souvlaki)
    listen('media-play', handlePlay);
    listen('media-pause', handlePause);
    listen('media-toggle', handleToggle);
    listen('media-next', handleNext);
    listen('media-prev', handlePrev);

    // Sync with backend on init
    await syncWithBackend();
  }

  async function syncWithBackend() {
    try {
      const state = await invoke<{ track_id: string | null, position_ms: number, is_playing: boolean }>('audio_get_state');
      if (state.track_id) {
        if (currentTrack.value?.ids.deezer !== state.track_id) {
          let track = queue.value.find(t => t.ids.deezer === state.track_id);
          if (!track) {
            try {
              track = await invoke<Track>('get_track', { id: state.track_id });
              queue.value = [track];
              currentIndex.value = 0;
            } catch (e) {
              console.error('Failed to fetch track for sync:', e);
            }
          } else {
            currentIndex.value = queue.value.indexOf(track);
          }
        }

        if (currentTrack.value) {
          progress.value = state.position_ms / 1000;
          isPlaying.value = state.is_playing;
          duration.value = (currentTrack.value.duration_ms || 0) / 1000;

          // Re-attach listeners in service
          const service = PlaybackService.getInstance();
          service.reconnect(
            currentTrack.value,
            () => onTrackEnd(),
            () => { isPlaying.value = true; },
            () => { isPlaying.value = false; },
            (p, browserDuration) => {
              progress.value = p;
              if (browserDuration && isFinite(browserDuration) && browserDuration > 0) {
                duration.value = browserDuration;
              }
            }
          );

          if (lyrics.value.length === 0) {
            fetchLyrics(currentTrack.value);
          }
        }
      }
    } catch (e) {
      console.error('Failed to sync with backend:', e);
    }
  }

  async function playTrack(track: Track, context?: { type: 'album' | 'playlist' | 'radio' | 'top', items: Track[] }) {
    if (currentTrack.value?.ids.deezer === track.ids.deezer) {
      if (!isPlaying.value) {
        startPlayback();
      }
      return;
    }

    resetProgress();
    lyrics.value = [];
    if (context) {
      queue.value = context.items;
      currentIndex.value = queue.value.findIndex(t => t.ids.deezer === track.ids.deezer);
    } else {
      queue.value = [track];
      currentIndex.value = 0;
      fetchRadio(track.ids.deezer!);
    }

    if (isShuffle.value) {
      generateShuffledIndices();
    }

    await startPlayback();
  }

  async function startPlayback() {
    const track = currentTrack.value;
    if (!track) return;

    const trackDurationMs = track.duration_ms || (track as any).duration * 1000 || 200000;
    duration.value = trackDurationMs / 1000;
    isBuffering.value = true;

    fetchLyrics(track);

    const service = PlaybackService.getInstance();
    await service.play(
      track,
      () => onTrackEnd(),
      () => { isPlaying.value = true; },
      () => { isPlaying.value = false; },
      (p, browserDuration) => {
        progress.value = p;
        if (browserDuration && isFinite(browserDuration) && browserDuration > 0) {
          duration.value = browserDuration;
        }
      },
      () => { isBuffering.value = false; },
      (buffering) => { isBuffering.value = buffering; },
    );

    triggerPreload();
  }

  function triggerPreload() {
    const nextTrack = nextTrackInQueue.value;
    if (nextTrack) {
      PlaybackService.getInstance().preload(nextTrack);
    }
  }

  async function fetchLyrics(track: Track) {
    isLoadingLyrics.value = true;
    lyrics.value = [];
    try {
      const lrcContent = await invoke<string | null>('get_lyrics', {
        artist: track.artists[0]?.name || '',
        title: track.title,
        album: track.album.title,
        durationMs: track.duration_ms
      });

      if (lrcContent) {
        lyrics.value = LrcParser.parse(lrcContent);
      }
    } catch (e) {
      console.error('Failed to fetch lyrics:', e);
    } finally {
      isLoadingLyrics.value = false;
    }
  }

  function togglePlay() {
    const service = PlaybackService.getInstance();
    if (isPlaying.value) {
      service.pause();
    } else {
      if (currentIndex.value === -1 && queue.value.length > 0) {
        resetProgress();
        currentIndex.value = 0;
        startPlayback();
      } else {
        const track = currentTrack.value;
        if (track) {
          startPlayback();
        }
      }
    }
  }

  function playFromQueue(index: number) {
    resetProgress();
    currentIndex.value = index;
    startPlayback();
  }

  function next() {
    resetProgress();
    if (repeatMode.value === 'one') {
      PlaybackService.getInstance().resetTrackId();
      startPlayback();
      return;
    }

    if (isShuffle.value) {
      const currentShufflePos = shuffledIndices.value.indexOf(currentIndex.value);
      if (currentShufflePos < shuffledIndices.value.length - 1) {
        currentIndex.value = shuffledIndices.value[currentShufflePos + 1];
      } else if (repeatMode.value === 'all') {
        currentIndex.value = shuffledIndices.value[0];
      } else {
        return;
      }
    } else {
      if (currentIndex.value < queue.value.length - 1) {
        currentIndex.value++;
      } else if (repeatMode.value === 'all') {
        currentIndex.value = 0;
      } else {
        return;
      }
    }
    startPlayback();
  }

  function prev() {
    if (progress.value > 3) {
      seek(0);
      return;
    }

    resetProgress();
    if (isShuffle.value) {
      const currentShufflePos = shuffledIndices.value.indexOf(currentIndex.value);
      if (currentShufflePos > 0) {
        currentIndex.value = shuffledIndices.value[currentShufflePos - 1];
      } else if (repeatMode.value === 'all') {
        currentIndex.value = shuffledIndices.value[shuffledIndices.value.length - 1];
      } else {
        seek(0);
        return;
      }
    } else {
      if (currentIndex.value > 0) {
        currentIndex.value--;
      } else if (repeatMode.value === 'all') {
        currentIndex.value = queue.value.length - 1;
      } else {
        seek(0);
        return;
      }
    }
    startPlayback();
  }

  function seek(seconds: number) {
    PlaybackService.getInstance().seek(seconds);
  }

  function setVolume(v: number) {
    volume.value = Math.min(Math.max(v, 0), 1);
    PlaybackService.getInstance().setVolume(volume.value);
  }

  function stop() {
    const service = PlaybackService.getInstance();
    service.pause();
    isPlaying.value = false;
    currentIndex.value = -1;
    queue.value = [];
    resetProgress();
    lyrics.value = [];
  }

  function toggleShuffle() {
    isShuffle.value = !isShuffle.value;
    if (isShuffle.value) {
      generateShuffledIndices();
    }
  }

  function toggleRepeat() {
    const modes: ('off' | 'all' | 'one')[] = ['off', 'all', 'one'];
    const nextIdx = (modes.indexOf(repeatMode.value) + 1) % modes.length;
    repeatMode.value = modes[nextIdx];
  }

  function toggleQueue() {
    showQueue.value = !showQueue.value;
  }

  function addToQueue(track: Track) {
    const exists = queue.value.some(t => t.ids.deezer === track.ids.deezer);
    if (exists) {
      notificationStore.notify(t('playback.already_in_queue', { name: track.title }), 'error');
      return;
    }

    queue.value.push(track);
    if (isShuffle.value) {
      shuffledIndices.value.push(queue.value.length - 1);
    }
    notificationStore.notify(t('playback.added_to_queue', { name: track.title }), 'success');
  }

  function addTracksToQueue(tracks: Track[]) {
    let addedCount = 0;
    tracks.forEach(track => {
      const exists = queue.value.some(t => t.ids.deezer === track.ids.deezer);
      if (!exists) {
        queue.value.push(track);
        if (isShuffle.value) {
          shuffledIndices.value.push(queue.value.length - 1);
        }
        addedCount++;
      }
    });

    if (addedCount > 0) {
      notificationStore.notify(t('playback.batch_added_to_queue', { n: addedCount }), 'success');
    } else {
      notificationStore.notify(t('playback.all_already_in_queue'), 'info');
    }
  }

  function removeFromQueue(originalIndex: number) {
    if (originalIndex === currentIndex.value) return;

    const track = queue.value[originalIndex];
    queue.value.splice(originalIndex, 1);

    if (originalIndex < currentIndex.value) {
      currentIndex.value--;
    }

    if (isShuffle.value) {
      const shufflePos = shuffledIndices.value.indexOf(originalIndex);
      if (shufflePos !== -1) {
        shuffledIndices.value.splice(shufflePos, 1);
      }
      shuffledIndices.value = shuffledIndices.value.map(idx => idx > originalIndex ? idx - 1 : idx);
    }

    notificationStore.notify(t('playback.removed_from_queue', { name: track.title }), 'info');
  }

  function moveUp(originalIndex: number) {
    if (isShuffle.value || originalIndex <= 0) return;
    const targetIndex = originalIndex - 1;
    if (originalIndex === currentIndex.value || targetIndex === currentIndex.value) return;

    const track = queue.value[originalIndex];
    queue.value.splice(originalIndex, 1);
    queue.value.splice(targetIndex, 0, track);
  }

  function moveDown(originalIndex: number) {
    if (isShuffle.value || originalIndex >= queue.value.length - 1) return;
    const targetIndex = originalIndex + 1;
    if (originalIndex === currentIndex.value || targetIndex === currentIndex.value) return;

    const track = queue.value[originalIndex];
    queue.value.splice(originalIndex, 1);
    queue.value.splice(targetIndex, 0, track);
  }

  function reorderQueue(oldIndex: number, newIndex: number) {
    if (isShuffle.value || oldIndex < 0 || oldIndex >= queue.value.length || newIndex < 0 || newIndex >= queue.value.length || oldIndex === newIndex) return;

    const track = queue.value[oldIndex];
    const newQueue = [...queue.value];
    newQueue.splice(oldIndex, 1);
    newQueue.splice(newIndex, 0, track);

    let nextIdx = currentIndex.value;
    if (currentIndex.value === oldIndex) {
      nextIdx = newIndex;
    } else if (oldIndex < currentIndex.value && newIndex >= currentIndex.value) {
      nextIdx--;
    } else if (oldIndex > currentIndex.value && newIndex <= currentIndex.value) {
      nextIdx++;
    }

    queue.value = newQueue;
    currentIndex.value = nextIdx;
  }

  function resetProgress() {
    progress.value = 0;
    duration.value = 0;
    isBuffering.value = false;
  }

  function onTrackEnd() {
    if (repeatMode.value === 'one') {
      resetProgress();
      PlaybackService.getInstance().resetTrackId();
      startPlayback();
    } else {
      next();
    }
  }

  async function fetchRadio(trackId: string) {
    try {
      const relatedTracks = await SearchService.getTrackRadio(trackId);
      if (currentTrack.value?.ids.deezer !== trackId) return;
      const newTracks = relatedTracks.filter(rt => !queue.value.some(q => q.ids.deezer === rt.ids.deezer));
      queue.value.push(...newTracks);
      if (isShuffle.value) {
        generateShuffledIndices();
      }
    } catch (e) {}
  }

  function generateShuffledIndices() {
    const indices = Array.from({ length: queue.value.length }, (_, i) => i);
    for (let i = indices.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [indices[i], indices[j]] = [indices[j], indices[i]];
    }
    shuffledIndices.value = indices;
  }

  return {
    queue, currentIndex, isPlaying, isBuffering, volume, progress, duration,
    repeatMode, isShuffle, shuffledIndices, lyrics, isLoadingLyrics, showQueue,
    currentTrack, currentLineIndex, hasNext, hasPrev, nextTrackInQueue,
    initMediaControls, playTrack, togglePlay, playFromQueue, next, prev,
    seek, setVolume, stop, toggleShuffle, toggleRepeat, toggleQueue,
    addToQueue, addTracksToQueue, removeFromQueue, moveUp, moveDown, reorderQueue
  };
});
