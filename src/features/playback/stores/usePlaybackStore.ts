import { defineStore } from 'pinia';
import type { Track } from '../../search/models/search';
import { PlaybackService } from '../services/playbackService';
import { SearchService } from '../../search/services/searchService';
import { useNotificationStore } from '../../../stores/useNotificationStore';
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { LrcParser, type LrcLine } from '../utils/lrcParser';

export const usePlaybackStore = defineStore('playback', {
  state: () => ({
    queue: [] as Track[],
    currentIndex: -1,
    isPlaying: false,
    isBuffering: false,
    volume: 0.8,
    progress: 0,
    duration: 0,
    repeatMode: 'off' as 'off' | 'one' | 'all',
    isShuffle: false,
    shuffledIndices: [] as number[],
    lyrics: [] as LrcLine[],
    isLoadingLyrics: false,
    showQueue: false,
    _listenersInitialized: false,
  }),

  getters: {
    currentTrack(): Track | null {
      if (this.currentIndex >= 0 && this.currentIndex < this.queue.length) {
        return this.queue[this.currentIndex];
      }
      return null;
    },
    currentLineIndex(): number {
      return LrcParser.getActiveLineIndex(this.lyrics, this.progress * 1000);
    },
    hasNext(): boolean {
      if (this.repeatMode === 'all') return this.queue.length > 0;
      return this.currentIndex < this.queue.length - 1;
    },
    hasPrev(): boolean {
      if (this.repeatMode === 'all') return this.queue.length > 0;
      return this.currentIndex > 0;
    },
    nextTrackInQueue(): Track | null {
      if (this.queue.length === 0) return null;
      if (this.isShuffle) {
        const currentShufflePos = this.shuffledIndices.indexOf(this.currentIndex);
        if (currentShufflePos < this.shuffledIndices.length - 1) {
          return this.queue[this.shuffledIndices[currentShufflePos + 1]];
        } else if (this.repeatMode === 'all') {
          return this.queue[this.shuffledIndices[0]];
        }
      } else {
        if (this.currentIndex < this.queue.length - 1) {
          return this.queue[this.currentIndex + 1];
        } else if (this.repeatMode === 'all') {
          return this.queue[0];
        }
      }
      return null;
    }
  },

  actions: {
    async initMediaControls() {
      if (this._listenersInitialized) return;
      this._listenersInitialized = true;

      const handlePlay = () => { if (!this.isPlaying) this.togglePlay(); };
      const handlePause = () => { if (this.isPlaying) this.togglePlay(); };
      const handleToggle = () => { this.togglePlay(); };
      const handleNext = () => { this.next(); };
      const handlePrev = () => { this.prev(); };

      // 1. Listen to OS media control events from Rust (Souvlaki)
      listen('media-play', handlePlay);
      listen('media-pause', handlePause);
      listen('media-toggle', handleToggle);
      listen('media-next', handleNext);
      listen('media-prev', handlePrev);

      // 2. Listen to Browser Media Session events (WebView fallback)
      window.addEventListener('media-play', handlePlay);
      window.addEventListener('media-pause', handlePause);
      window.addEventListener('media-next', handleNext);
      window.addEventListener('media-prev', handlePrev);

      // Sync with backend on init
      await this.syncWithBackend();
    },

    async syncWithBackend() {
      try {
        const state = await invoke<{ track_id: string | null, position_ms: number, is_playing: boolean }>('audio_get_state');
        if (state.track_id) {
          // If we have a track in backend but not in frontend, or it's different
          if (this.currentTrack?.ids.deezer !== state.track_id) {
            // We need the full track object. If it's in the queue, we use it.
            let track = this.queue.find(t => t.ids.deezer === state.track_id);
            if (!track) {
              // Fetch track info if not in queue
              try {
                track = await invoke<Track>('get_track', { id: state.track_id });
                this.queue = [track];
                this.currentIndex = 0;
              } catch (e) {
                // If we can't get the track, we can't sync perfectly, but we at least know it's playing
                console.error('Failed to fetch track for sync:', e);
              }
            } else {
              this.currentIndex = this.queue.indexOf(track);
            }
          }

          if (this.currentTrack) {
            this.progress = state.position_ms / 1000;
            this.isPlaying = state.is_playing;
            this.duration = (this.currentTrack.duration_ms || 0) / 1000;

            // Re-attach listeners in service
            const service = PlaybackService.getInstance();
            service.reconnect(
              this.currentTrack,
              () => this.onTrackEnd(),
              () => { this.isPlaying = true; },
              () => this.isPlaying = false,
              (progress, browserDuration) => {
                this.progress = progress;
                if (browserDuration && isFinite(browserDuration) && browserDuration > 0) {
                  this.duration = browserDuration;
                }
              }
            );

            if (this.lyrics.length === 0) {
              this.fetchLyrics(this.currentTrack);
            }
          }
        }
      } catch (e) {
        console.error('Failed to sync with backend:', e);
      }
    },

    async playTrack(track: Track, context?: { type: 'album' | 'playlist' | 'radio' | 'top', items: Track[] }) {
      // If the same track is already active, just resume if paused
      if (this.currentTrack?.ids.deezer === track.ids.deezer) {
        if (!this.isPlaying) {
          this.startPlayback();
        }
        return;
      }

      this.resetProgress();
      this.lyrics = [];
      // Set the queue based on context
      if (context) {
        this.queue = context.items;
        this.currentIndex = this.queue.findIndex(t => t.ids.deezer === track.ids.deezer);
      } else {
        // Single track played: Clear queue, add track, and fetch radio for auto-queue
        this.queue = [track];
        this.currentIndex = 0;
        this.fetchRadio(track.ids.deezer!);
      }

      if (this.isShuffle) {
        this.generateShuffledIndices();
      }

      await this.startPlayback();
    },

    async startPlayback() {
      const track = this.currentTrack;
      if (!track) return;

      // Set duration from metadata immediately (in seconds)
      const trackDurationMs = track.duration_ms || (track as any).duration * 1000 || 200000;
      this.duration = trackDurationMs / 1000;
      this.isBuffering = true;

      // Fetch lyrics in parallel
      this.fetchLyrics(track);

      const service = PlaybackService.getInstance();
      await service.play(
        track,
        () => this.onTrackEnd(),
        () => { this.isPlaying = true; },
        () => this.isPlaying = false,
        (progress, browserDuration) => {
          this.progress = progress;
          // Only trust browser duration if it's a browser valid number and strictly greater than 0
          if (browserDuration && isFinite(browserDuration) && browserDuration > 0) {
            this.duration = browserDuration;
          }
        },
        () => { this.isBuffering = false; },
        (buffering) => { this.isBuffering = buffering; },
      );

      this.triggerPreload();
    },

    triggerPreload() {
      const nextTrack = this.nextTrackInQueue;
      if (nextTrack) {

        PlaybackService.getInstance().preload(nextTrack);
      }
    },

    async fetchLyrics(track: Track) {
      this.isLoadingLyrics = true;
      this.lyrics = [];
      try {
        const lrcContent = await invoke<string | null>('get_lyrics', {
          artist: track.artists[0]?.name || '',
          title: track.title,
          album: track.album.title,
          durationMs: track.duration_ms
        });

        if (lrcContent) {
          this.lyrics = LrcParser.parse(lrcContent);
        }
      } catch (e) {
        console.error('Failed to fetch lyrics:', e);
      } finally {
        this.isLoadingLyrics = false;
      }
    },

    togglePlay() {
      const service = PlaybackService.getInstance();
      if (this.isPlaying) {
        service.pause();
      } else {
        if (this.currentIndex === -1 && this.queue.length > 0) {
          this.resetProgress();
          this.currentIndex = 0;
          this.startPlayback();
        } else {
          // Resume if we have a track
          const track = this.currentTrack;
          if (track) {
            this.startPlayback();
          }
        }
      }
    },

    playFromQueue(index: number) {
      this.resetProgress();
      this.currentIndex = index;
      this.startPlayback();
    },

    next() {
      this.resetProgress();
      if (this.repeatMode === 'one') {
        PlaybackService.getInstance().resetTrackId();
        this.startPlayback();
        return;
      }

      if (this.isShuffle) {
        const currentShufflePos = this.shuffledIndices.indexOf(this.currentIndex);
        if (currentShufflePos < this.shuffledIndices.length - 1) {
          this.currentIndex = this.shuffledIndices[currentShufflePos + 1];
        } else if (this.repeatMode === 'all') {
          this.currentIndex = this.shuffledIndices[0];
        } else {
          return;
        }
      } else {
        if (this.currentIndex < this.queue.length - 1) {
          this.currentIndex++;
        } else if (this.repeatMode === 'all') {
          this.currentIndex = 0;
        } else {
          return;
        }
      }
      this.startPlayback();
    },

    prev() {
      if (this.progress > 3) {
        this.seek(0);
        return;
      }

      this.resetProgress();
      if (this.isShuffle) {
        const currentShufflePos = this.shuffledIndices.indexOf(this.currentIndex);
        if (currentShufflePos > 0) {
          this.currentIndex = this.shuffledIndices[currentShufflePos - 1];
        } else if (this.repeatMode === 'all') {
          this.currentIndex = this.shuffledIndices[this.shuffledIndices.length - 1];
        } else {
          this.seek(0);
          return;
        }
      } else {
        if (this.currentIndex > 0) {
          this.currentIndex--;
        } else if (this.repeatMode === 'all') {
          this.currentIndex = this.queue.length - 1;
        } else {
          this.seek(0);
          return;
        }
      }
      this.startPlayback();
    },

    seek(seconds: number) {
      PlaybackService.getInstance().seek(seconds);
    },

    setVolume(volume: number) {
      this.volume = Math.min(Math.max(volume, 0), 1);
      PlaybackService.getInstance().setVolume(this.volume);
    },

    stop() {
      const service = PlaybackService.getInstance();
      service.pause(); // HTMLAudioElement pause is effective stop
      this.isPlaying = false;
      this.currentIndex = -1;
      this.queue = [];
      this.resetProgress();
      this.lyrics = [];
    },

    toggleShuffle() {
      this.isShuffle = !this.isShuffle;
      if (this.isShuffle) {
        this.generateShuffledIndices();
      }
    },

    toggleRepeat() {
      const modes: ('off' | 'all' | 'one')[] = ['off', 'all', 'one'];
      const nextIndex = (modes.indexOf(this.repeatMode) + 1) % modes.length;
      this.repeatMode = modes[nextIndex];
    },

    toggleQueue() {
      this.showQueue = !this.showQueue;
    },

    addToQueue(track: Track) {
      // Avoid duplicates
      const exists = this.queue.some(t => t.ids.deezer === track.ids.deezer);
      const notificationStore = useNotificationStore();

      if (exists) {
        notificationStore.notify(`${track.title} ya está en la cola`, 'error');
        return;
      }

      this.queue.push(track);
      if (this.isShuffle) {
        // Add new index to shuffledIndices
        this.shuffledIndices.push(this.queue.length - 1);
      }

      // Show notification
      notificationStore.notify(`${track.title} añadido a la cola`, 'success');
    },

    removeFromQueue(originalIndex: number) {
      if (originalIndex === this.currentIndex) return; // Don't remove currently playing

      const track = this.queue[originalIndex];
      this.queue.splice(originalIndex, 1);

      // Fix currentIndex if needed
      if (originalIndex < this.currentIndex) {
        this.currentIndex--;
      }

      // Fix shuffledIndices
      if (this.isShuffle) {
        // Remove the index from shuffled sequence
        const shufflePos = this.shuffledIndices.indexOf(originalIndex);
        if (shufflePos !== -1) {
          this.shuffledIndices.splice(shufflePos, 1);
        }
        // Adjust all indices greater than the removed one
        this.shuffledIndices = this.shuffledIndices.map(idx => idx > originalIndex ? idx - 1 : idx);
      }

      const notificationStore = useNotificationStore();
      notificationStore.notify(`${track.title} eliminado de la cola`, 'info');
    },

    moveUp(originalIndex: number) {
      if (this.isShuffle) return; // Reordering in shuffle mode is complex, disable for now
      if (originalIndex <= 0) return;

      const targetIndex = originalIndex - 1;
      // Don't swap with current track
      if (originalIndex === this.currentIndex || targetIndex === this.currentIndex) return;

      const track = this.queue[originalIndex];
      this.queue.splice(originalIndex, 1);
      this.queue.splice(targetIndex, 0, track);
    },

    moveDown(originalIndex: number) {
      if (this.isShuffle) return;
      if (originalIndex >= this.queue.length - 1) return;

      const targetIndex = originalIndex + 1;
      if (originalIndex === this.currentIndex || targetIndex === this.currentIndex) return;

      const track = this.queue[originalIndex];
      this.queue.splice(originalIndex, 1);
      this.queue.splice(targetIndex, 0, track);
    },

    resetProgress() {
      this.progress = 0;
      this.duration = 0;
      this.isBuffering = false;
    },

    onTrackEnd() {
      if (this.repeatMode === 'one') {
        this.resetProgress();
        PlaybackService.getInstance().resetTrackId();
        this.startPlayback();
      } else {
        this.next();
      }
    },

    async fetchRadio(trackId: string) {
      try {
        const relatedTracks = await SearchService.getTrackRadio(trackId);

        // Race condition check: Only update if the track we're playing is still the one
        // we requested the radio for.
        if (this.currentTrack?.ids.deezer !== trackId) return;

        const newTracks = relatedTracks.filter(rt => !this.queue.some(q => q.ids.deezer === rt.ids.deezer));
        this.queue.push(...newTracks);
        if (this.isShuffle) {
          this.generateShuffledIndices();
        }
      } catch (e) {
        // Silent error
      }
    },

    generateShuffledIndices() {
      const indices = Array.from({ length: this.queue.length }, (_, i) => i);
      for (let i = indices.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [indices[i], indices[j]] = [indices[j], indices[i]];
      }
      this.shuffledIndices = indices;

    }
  }
});
