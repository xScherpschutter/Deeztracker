import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import type { Track } from '../../search/models/search';
import { getImageUrl } from '../../search/utils/image';

export class PlaybackService {
  private static instance: PlaybackService;
  private _currentTrackId: string | null = null;
  private isSeeking = false;
  private _volume = 0.8;

  private onProgressCallback: ((progress: number, duration: number) => void) | null = null;
  private onEndCallback: (() => void) | null = null;
  private onPlayCallback: (() => void) | null = null;
  private onPauseCallback: (() => void) | null = null;

  private currentDuration = 0;

  private lastProgressUpdate = 0;

  private constructor() {
    this.setupNativeListeners();
  }

  static getInstance(): PlaybackService {
    if (!PlaybackService.instance) {
      PlaybackService.instance = new PlaybackService();
    }
    return PlaybackService.instance;
  }

  private async setupNativeListeners() {
    // @ts-ignore: Keeping the reference alive
    await listen<number>('playback_progress_native', (event) => {
      if (this.isSeeking) return;

      const now = Date.now();
      if (now - this.lastProgressUpdate < 150) return;
      this.lastProgressUpdate = now;

      const progress = event.payload;
      if (this.onProgressCallback && this.currentDuration > 0) {
        this.onProgressCallback(progress, this.currentDuration);
      }

      // Periodically sync progress with the OS (MPRIS/SMTC)
      // Every ~1 second to not flood the bridge
      if (Math.floor(progress) % 2 === 0 && Math.abs(progress - Math.floor(progress)) < 0.2) {
        this.updatePlaybackState(true, progress);
      }
    });

    // @ts-ignore: Keeping the reference alive
    await listen<void>('playback_ended_native', () => {
      if (this.onEndCallback) {
        this.onEndCallback();
      }
    });
  }

  async preload(track: Track) {
    if (!track.ids.deezer) return;
    try {
      await invoke('audio_preload_native', { trackId: track.ids.deezer });
    } catch (e) {
      console.error('Preload error:', e);
    }
  }

  // Re-connect callbacks without triggering a new play
  reconnect(
    track: Track,
    onEnd: () => void,
    onPlay: () => void,
    onPause: () => void,
    onProgress: (progress: number, duration: number) => void,
  ) {
    this._currentTrackId = track.ids.deezer || null;
    this.currentDuration = (track.duration_ms || 200000) / 1000.0;
    this.onEndCallback = onEnd;
    this.onProgressCallback = onProgress;
    this.onPlayCallback = onPlay;
    this.onPauseCallback = onPause;
  }

  async play(
    track: Track,
    onEnd: () => void,
    onPlay: () => void,
    onPause: () => void,
    onProgress: (progress: number, duration: number) => void,
    onReady?: () => void,
    onBuffering?: (isBuffering: boolean) => void,
  ) {
    this.onEndCallback = onEnd;
    this.onProgressCallback = onProgress;
    this.onPlayCallback = onPlay;
    this.onPauseCallback = onPause;

    onBuffering?.(true);

    if (this._currentTrackId === track.ids.deezer) {
      try {
        await invoke('audio_resume_native');
        onReady?.();
        onBuffering?.(false);
        this.onPlayCallback?.();
        this.updatePlaybackState(true);
      } catch (e) {
        console.error('Failed to resume:', e);
        onReady?.();
        onBuffering?.(false);
      }
      return;
    }

    this._currentTrackId = track.ids.deezer || null;
    let trackDuration = track.duration_ms;
    if (!trackDuration || trackDuration < 1000) {
      trackDuration = track.duration_ms ? track.duration_ms : 200000;
    }
    this.currentDuration = trackDuration / 1000.0;


    try {
      if (track.ids.deezer) {
        await invoke('audio_play_native', {
          trackId: track.ids.deezer,
          startPercent: 0.0,
          startSec: 0.0
        });

        await this.setVolume(this._volume);
      }
      onReady?.();
      onBuffering?.(false);
      this.onPlayCallback?.();
      this.updateMediaMetadata(track);
      this.updatePlaybackState(true, 0);
    } catch (e) {
      console.error('Native playback error:', e);
      onReady?.();
      onBuffering?.(false);
    }
  }

  async pause() {
    try {
      await invoke('audio_pause_native');
      this.onPauseCallback?.();
      this.updatePlaybackState(false);
    } catch (e) {
      console.error(e);
    }
  }

  async resume() {
    try {
      await invoke('audio_resume_native');
      this.onPlayCallback?.();
      this.updatePlaybackState(true);
    } catch (e) {
      console.error(e);
    }
  }

  async stop() {
    try {
      this._currentTrackId = null;
      await invoke('audio_stop_native');
      this.onPauseCallback?.();
      this.updatePlaybackState(false);
    } catch (e) {
      console.error(e);
    }
  }

  async seek(seconds: number) {
    if (!this._currentTrackId) return;
    this.isSeeking = true;

    try {
      const durationToUse = this.currentDuration > 0 ? this.currentDuration : 1.0;
      let percent = seconds / durationToUse;

      const safeSec = isNaN(seconds) ? 0.0 : Number(seconds);
      const safePercent = isNaN(percent) ? 0.0 : Number(percent);



      await invoke('audio_play_native', {
        trackId: this._currentTrackId,
        startPercent: safePercent,
        startSec: safeSec
      });
      this.updatePlaybackState(true, seconds);
    } catch (e) {
      console.error('Seek error:', e);
    } finally {
      this.isSeeking = false;
    }
  }

  async setVolume(volume: number) {
    this._volume = Math.max(0, Math.min(1, volume));
    try {
      await invoke('audio_set_volume_native', { volume: this._volume });
    } catch (e) { console.error(e) }
  }

  private async updateMediaMetadata(track: Track) {
    try {
      const coverUrl = getImageUrl(track.album?.images, '');
      await invoke('update_media_metadata', {
        title: track.title,
        artist: track.artists.map((a) => a.name).join(', '),
        album: track.album?.title || '',
        coverUrl: coverUrl ? coverUrl : null,
        durationMs: track.duration_ms,
      });

      if ('mediaSession' in navigator) {
        navigator.mediaSession.metadata = new MediaMetadata({
          title: track.title,
          artist: track.artists.map((a) => a.name).join(', '),
          album: track.album?.title || '',
          artwork: coverUrl ? [{ src: coverUrl, sizes: '512x512', type: 'image/jpeg' }] : []
        });

        navigator.mediaSession.setActionHandler('play', () => { window.dispatchEvent(new Event('media-play')); });
        navigator.mediaSession.setActionHandler('pause', () => { window.dispatchEvent(new Event('media-pause')); });
        navigator.mediaSession.setActionHandler('previoustrack', () => { window.dispatchEvent(new Event('media-prev')); });
        navigator.mediaSession.setActionHandler('nexttrack', () => { window.dispatchEvent(new Event('media-next')); });
      }
    } catch (e) {
      console.error(e);
    }
  }

  private async updatePlaybackState(playing: boolean, positionSeconds?: number) {
    try {
      await invoke('update_playback_state', {
        playing,
        positionMs: positionSeconds ? Math.floor(positionSeconds * 1000) : undefined,
      });
    } catch (e) { }
  }
}
