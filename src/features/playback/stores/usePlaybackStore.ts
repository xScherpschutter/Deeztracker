import { defineStore } from 'pinia';
import type { Track } from '../../search/models/search';
import { PlaybackService } from '../services/playbackService';
import { SearchService } from '../../search/services/searchService';
import { invoke } from '@tauri-apps/api/core';
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
    }
  },

  actions: {
    async playTrack(track: Track, context?: { type: 'album' | 'playlist' | 'radio' | 'top', items: Track[] }) {
      // If the same track is already active, just resume if paused
      if (this.currentTrack?.ids.deezer === track.ids.deezer) {
        if (!this.isPlaying) {
          PlaybackService.getInstance().seek(0);
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
      this.duration = track.duration_ms / 1000;
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
          // Only trust browser duration if it's a browser valid number and finite
          if (browserDuration && isFinite(browserDuration) && browserDuration > 0) {
            this.duration = browserDuration;
          }
        },
        () => { this.isBuffering = false; },
      );
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

    next() {
      this.resetProgress();
      if (this.repeatMode === 'one') {
        this.seek(0);
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
        }
      } else {
        if (this.currentIndex > 0) {
          this.currentIndex--;
        } else if (this.repeatMode === 'all') {
          this.currentIndex = this.queue.length - 1;
        }
      }
      this.startPlayback();
    },

    seek(seconds: number) {
      if (this.isBuffering) return;
      PlaybackService.getInstance().seek(seconds);
      this.progress = seconds;
    },

    setVolume(volume: number) {
      this.volume = volume;
      PlaybackService.getInstance().setVolume(volume);
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

    resetProgress() {
      this.progress = 0;
      this.duration = 0;
    },

    onTrackEnd() {
      if (this.repeatMode === 'one') {
        this.startPlayback();
      } else {
        this.next();
      }
    },

    async fetchRadio(trackId: string) {
      console.log('Fetching radio for track:', trackId);
      try {
        const relatedTracks = await SearchService.getTrackRadio(trackId);
        console.log('Received related tracks:', relatedTracks.length);

        // Filter out tracks already in queue
        const newTracks = relatedTracks.filter(rt => !this.queue.some(q => q.ids.deezer === rt.ids.deezer));
        this.queue.push(...newTracks);
        console.log('New queue length:', this.queue.length);

        if (this.isShuffle) {
          this.generateShuffledIndices();
        }
      } catch (e) {
        // Silent error: Radio endpoint might be restricted or non-existent
        console.warn('Radio fetch failed, skipping auto-queue', e);
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
