import { invoke } from '@tauri-apps/api/core';
import type { Track } from '../../search/models/search';
import { getImageUrl } from '../../search/utils/image';

export class PlaybackService {
  private static instance: PlaybackService;
  private audio: HTMLAudioElement | null = null;
  private currentTrackId: string | null = null;
  private baseUrl: string | null = null;
  private animationFrameId: number | null = null;
  private isSeeking = false;
  private lastPositionSent = -1;

  private constructor() { }

  static getInstance(): PlaybackService {
    if (!PlaybackService.instance) {
      PlaybackService.instance = new PlaybackService();
    }
    return PlaybackService.instance;
  }

  private async getBaseUrl(): Promise<string> {
    if (!this.baseUrl) {
      this.baseUrl = await invoke<string>('get_streaming_base_url');
    }
    return this.baseUrl;
  }

  async play(
    track: Track,
    onEnd: () => void,
    onPlay: () => void,
    onPause: () => void,
    onProgress: (progress: number, duration: number) => void,
    onReady?: () => void,
  ) {
    // Resume if same track
    if (this.currentTrackId === track.ids.deezer && this.audio) {
      this.safePlay(this.audio);
      return;
    }

    // Clean up previous audio
    this.cleanup();

    this.currentTrackId = track.ids.deezer || null;
    const baseUrl = await this.getBaseUrl();
    const url = `${baseUrl}/stream/${track.ids.deezer}`;

    const audio = new Audio(url);
    this.audio = audio;

    // Event listeners
    audio.addEventListener('play', () => {
      onPlay();
      this.updateMediaMetadata(track);
      this.updatePlaybackState(true, audio.currentTime);
      this.startProgressTimer(onProgress);
    });

    // canplay: browser has enough data buffered to actually play and seek
    audio.addEventListener('canplay', () => {
      onReady?.();
    }, { once: true });

    audio.addEventListener('pause', () => {
      // Ignore pause events triggered by the browser during seeking
      if (this.isSeeking) return;
      onPause();
      this.stopProgressTimer();
      this.updatePlaybackState(false, audio.currentTime);
    });

    audio.addEventListener('seeking', () => {
      this.isSeeking = true;
    });

    audio.addEventListener('seeked', () => {
      this.isSeeking = false;
      this.updatePlaybackState(!audio.paused, audio.currentTime);
      // Auto-resume playback after seek completes
      if (audio.paused && this.currentTrackId) {
        this.safePlay(audio);
      }
      this.startProgressTimer(onProgress);
    });

    audio.addEventListener('ended', () => {
      this.stopProgressTimer();
      onEnd();
    });

    audio.addEventListener('error', (e) => {
      console.error('Playback error:', e);
    });

    this.safePlay(audio);
  }

  pause() {
    this.audio?.pause();
  }

  stop() {
    this.cleanup();
  }

  seek(seconds: number) {
    if (!this.audio) return;
    this.audio.currentTime = seconds;
  }

  setVolume(volume: number) {
    if (this.audio) {
      this.audio.volume = volume;
    }
  }

  /** Play with AbortError handling (normal when play is interrupted by seek) */
  private safePlay(audio: HTMLAudioElement) {
    audio.play().catch((e) => {
      if (e.name !== 'AbortError') {
        console.error('Playback error:', e);
      }
    });
  }

  private cleanup() {
    this.stopProgressTimer();
    if (this.audio) {
      this.audio.pause();
      this.audio.removeAttribute('src');
      this.audio.load(); // Release resources
      this.audio = null;
    }
    this.lastPositionSent = -1;
  }

  private startProgressTimer(onProgress: (progress: number, duration: number) => void) {
    this.stopProgressTimer();
    const update = () => {
      if (this.audio && !this.audio.paused) {
        const currentTime = this.audio.currentTime;
        const duration = this.audio.duration || 0;
        onProgress(currentTime, isFinite(duration) ? duration : 0);
        this.animationFrameId = requestAnimationFrame(update);
      }
    };
    this.animationFrameId = requestAnimationFrame(update);
  }

  private stopProgressTimer() {
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
  }

  private async updateMediaMetadata(track: Track) {
    try {
      const coverUrl = getImageUrl(track.album?.images, '');
      
      // 1. Update OS via Souvlaki (Rust)
      await invoke('update_media_metadata', {
        title: track.title,
        artist: track.artists.map((a) => a.name).join(', '),
        album: track.album?.title || '',
        coverUrl: coverUrl ? coverUrl : null,
        durationMs: track.duration_ms,
      });

      // 2. Update Browser's Media Session (prevents Webview from hijacking OS media keys silently)
      if ('mediaSession' in navigator) {
        navigator.mediaSession.metadata = new MediaMetadata({
          title: track.title,
          artist: track.artists.map((a) => a.name).join(', '),
          album: track.album?.title || '',
          artwork: coverUrl ? [{ src: coverUrl, sizes: '512x512', type: 'image/jpeg' }] : []
        });

        // Delegate browser media actions back to Tauri (or Pinia)
        // We dispatch standard custom events so the store can pick them up if needed,
        // but the store is already listening to Tauri events. To ensure they work 
        // regardless of who catches the key (Webview vs Souvlaki), we emit window events.
        navigator.mediaSession.setActionHandler('play', () => { window.dispatchEvent(new Event('media-play')); });
        navigator.mediaSession.setActionHandler('pause', () => { window.dispatchEvent(new Event('media-pause')); });
        navigator.mediaSession.setActionHandler('previoustrack', () => { window.dispatchEvent(new Event('media-prev')); });
        navigator.mediaSession.setActionHandler('nexttrack', () => { window.dispatchEvent(new Event('media-next')); });
      }

    } catch (e) {
      console.error('Failed to update media metadata', e);
    }
  }

  private async updatePlaybackState(playing: boolean, positionSeconds?: number) {
    try {
      await invoke('update_playback_state', {
        playing,
        positionMs: positionSeconds ? Math.floor(positionSeconds * 1000) : undefined,
      });
    } catch (e) {
      console.error('Failed to update playback state', e);
    }
  }
}

