import { Howl } from 'howler';
import { invoke } from '@tauri-apps/api/core';
import type { Track } from '../../search/models/search';

export class PlaybackService {
  private static instance: PlaybackService;
  private howl: Howl | null = null;
  private currentTrackId: string | null = null;
  private baseUrl: string | null = null;

  private constructor() {}

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

  async play(track: Track, onEnd: () => void, onPlay: () => void, onPause: () => void, onProgress: (progress: number, duration: number) => void) {
    if (this.currentTrackId === track.ids.deezer && this.howl) {
      this.howl.play();
      return;
    }

    if (this.howl) {
      this.howl.stop();
      this.howl.unload();
    }

    this.currentTrackId = track.ids.deezer || null;
    const baseUrl = await this.getBaseUrl();
    const url = `${baseUrl}/stream/${track.ids.deezer}`;

    this.howl = new Howl({
      src: [url],
      format: ['mp3', 'flac'],
      html5: true, // Use native audio element now that server supports content-length
      onplay: () => {
        onPlay();
        this.updateMediaMetadata(track);
        this.startProgressTimer(onProgress);
      },
      onpause: () => {
        onPause();
        this.updatePlaybackState(false);
      },
      onend: () => {
        onEnd();
      },
      onloaderror: (id, error) => {
        console.error('Playback load error:', error);
      }
    });

    this.howl.play();
  }

  pause() {
    this.howl?.pause();
  }

  stop() {
    this.howl?.stop();
  }

  seek(seconds: number) {
    this.howl?.seek(seconds);
  }

  setVolume(volume: number) {
    this.howl?.volume(volume);
  }

  private startProgressTimer(onProgress: (progress: number, duration: number) => void) {
    const update = () => {
      if (this.howl && this.howl.playing()) {
        const seek = this.howl.seek() as number;
        const duration = this.howl.duration();
        onProgress(seek, duration);
        this.updatePlaybackState(true, seek);
        requestAnimationFrame(update);
      }
    };
    requestAnimationFrame(update);
  }

  private async updateMediaMetadata(track: Track) {
    try {
      await invoke('update_media_metadata', {
        title: track.title,
        artist: track.artists.map(a => a.name).join(', '),
        album: track.album.title,
        coverUrl: track.album.images[track.album.images.length - 1]?.url,
        durationMs: track.duration_ms
      });
    } catch (e) {
      console.error('Failed to update media metadata', e);
    }
  }

  private async updatePlaybackState(playing: boolean, positionSeconds?: number) {
    try {
      await invoke('update_playback_state', {
        playing,
        positionMs: positionSeconds ? Math.floor(positionSeconds * 1000) : undefined
      });
    } catch (e) {
      console.error('Failed to update playback state', e);
    }
  }
}
