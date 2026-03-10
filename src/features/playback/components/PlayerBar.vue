<script setup lang="ts">
import { usePlaybackStore } from '../stores/usePlaybackStore';
import { formatDuration } from '../../search/utils/time';

const playbackStore = usePlaybackStore();

const onSeek = (e: Event) => {
  const value = (e.target as HTMLInputElement).value;
  playbackStore.seek(parseFloat(value));
};

const onVolumeChange = (e: Event) => {
  const value = (e.target as HTMLInputElement).value;
  playbackStore.setVolume(parseFloat(value));
};
</script>

<template>
  <footer class="h-24 bg-surface border-t border-white/5 px-8 flex items-center justify-between flex-shrink-0 z-20">
    <!-- Track Info -->
    <div class="flex items-center gap-4 w-1/3 min-w-0">
      <div v-if="playbackStore.currentTrack" class="w-14 h-14 bg-background rounded-lg overflow-hidden flex-shrink-0">
        <img :src="playbackStore.currentTrack.album.images[0]?.url" alt="Cover" class="w-full h-full object-cover">
      </div>
      <div v-else class="w-14 h-14 bg-white/5 rounded-lg flex-shrink-0"></div>
      
      <div class="min-w-0">
        <template v-if="playbackStore.currentTrack">
          <div class="text-sm font-bold truncate hover:underline cursor-pointer">
            {{ playbackStore.currentTrack.title }}
          </div>
          <div class="text-xs text-textGray truncate">
            {{ playbackStore.currentTrack.artists.map(a => a.name).join(', ') }}
          </div>
        </template>
        <template v-else>
          <div class="h-4 bg-white/5 rounded w-32 mb-2"></div>
          <div class="h-3 bg-white/5 rounded w-24"></div>
        </template>
      </div>
    </div>

    <!-- Controls -->
    <div class="flex flex-col items-center gap-2 w-1/3">
      <div class="flex items-center gap-6">
        <!-- Shuffle -->
        <button 
          @click="playbackStore.toggleShuffle"
          class="transition-colors"
          :class="playbackStore.isShuffle ? 'text-primary' : 'text-textGray hover:text-white'"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 18h1.4c1.3 0 2.5-.6 3.3-1.7l6.1-8.6c.7-1.1 2-1.7 3.3-1.7H22"/><path d="m18 2 4 4-4 4"/><path d="M2 6h1.9c1.2 0 2.3.6 3 1.5l3.8 5c.3.4.7.7 1.1 1l.5.3c.6.4 1.3.7 2 .7h7.7"/><path d="m18 14 4 4-4 4"/></svg>
        </button>

        <!-- Previous -->
        <button @click="playbackStore.prev" class="text-textGray hover:text-white transition-colors">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m19 20-10-8 10-8v16z"/><path d="M5 19V5"/></svg>
        </button>

        <!-- Play/Pause -->
        <button 
          @click="playbackStore.togglePlay" 
          class="w-10 h-10 bg-white text-black rounded-full flex items-center justify-center hover:scale-105 transition-transform"
        >
          <svg v-if="!playbackStore.isPlaying" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="m5 3 14 9-14 9V3z"/></svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
        </button>

        <!-- Next -->
        <button @click="playbackStore.next" class="text-textGray hover:text-white transition-colors">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m5 4 10 8-10 8V4z"/><path d="M19 5v14"/></svg>
        </button>

        <!-- Repeat -->
        <button 
          @click="playbackStore.toggleRepeat"
          class="transition-colors relative"
          :class="playbackStore.repeatMode !== 'off' ? 'text-primary' : 'text-textGray hover:text-white'"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m17 2 4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><path d="m7 22-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
          <span v-if="playbackStore.repeatMode === 'one'" class="absolute -top-1 -right-1 text-[8px] font-bold bg-primary text-black w-3 h-3 rounded-full flex items-center justify-center">1</span>
        </button>
      </div>

      <!-- Progress Bar -->
      <div class="w-full flex items-center gap-2 group">
        <span class="text-[10px] text-textGray w-8 text-right font-mono">{{ formatDuration(playbackStore.progress * 1000) }}</span>
        <input 
          type="range" 
          :value="playbackStore.progress" 
          :max="playbackStore.duration || 0" 
          step="0.1"
          @input="onSeek"
          class="flex-1 h-1 bg-white/10 rounded-full appearance-none cursor-pointer accent-primary group-hover:h-1.5 transition-all"
          :style="{
            background: `linear-gradient(to right, #00AAFF ${ (playbackStore.progress / (playbackStore.duration || 1)) * 100 }%, rgba(255, 255, 255, 0.1) 0)`
          }"
        >
        <span class="text-[10px] text-textGray w-8 font-mono">{{ formatDuration(playbackStore.duration * 1000) }}</span>
      </div>
    </div>

    <!-- Volume & Others -->
    <div class="w-1/3 flex justify-end items-center gap-4">
      <div class="flex items-center gap-2 w-32 group/vol">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-textGray"><path d="M11 5 6 9H2v6h4l5 4V5z"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
        <input 
          type="range" 
          min="0" 
          max="1" 
          step="0.01" 
          :value="playbackStore.volume" 
          @input="onVolumeChange"
          class="flex-1 h-1 bg-white/10 rounded-full appearance-none cursor-pointer accent-white hover:h-1.5 transition-all"
          :style="{
            background: `linear-gradient(to right, white ${ playbackStore.volume * 100 }%, rgba(255, 255, 255, 0.1) 0)`
          }"
        >
      </div>
    </div>
  </footer>
</template>

<style scoped>
input[type='range']::-webkit-slider-thumb {
  appearance: none;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: white;
  transition: all 0.1s ease;
}

.group:hover input[type='range']::-webkit-slider-thumb,
input[type='range']:active::-webkit-slider-thumb {
  width: 12px;
  height: 12px;
}
</style>
