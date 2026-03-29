<script setup lang="ts">
import { usePlaybackStore } from '../stores/usePlaybackStore';
import { useLibraryStore } from '../../library/stores/useLibraryStore';
import { computed, ref, watch, onMounted, nextTick } from 'vue';

const store = usePlaybackStore();
const libraryStore = useLibraryStore();
const lyricsList = ref<HTMLElement | null>(null);
const isDragging = ref(false);
const localProgress = ref(0);

const onSeekInput = (e: Event) => {
  isDragging.value = true;
  localProgress.value = Number((e.target as HTMLInputElement).value) || 0;
};

const onSeekChange = (e: Event) => {
  const value = Number((e.target as HTMLInputElement).value) || 0;
  store.seek(value);
  isDragging.value = false;
};

const currentTrack = computed(() => store.currentTrack);
const lyrics = computed(() => store.lyrics);
const currentIndex = computed(() => store.currentLineIndex);

const scrollToActiveLine = (index: number, smooth: boolean = true) => {
  if (index >= 0 && lyricsList.value) {
    const lines = lyricsList.value.querySelectorAll('.lyric-line');
    const activeLine = lines[index] as HTMLElement;
    
    if (activeLine) {
      const containerHeight = lyricsList.value.clientHeight;
      const lineOffset = activeLine.offsetTop;
      const lineHeight = activeLine.clientHeight;
      
      // Center the line perfectly in the viewport
      const scrollTo = lineOffset - (containerHeight / 2) + (lineHeight / 2);
      
      lyricsList.value.scrollTo({
        top: scrollTo,
        behavior: smooth ? 'smooth' : 'auto'
      });
    }
  }
};

// Auto-scroll lyrics to the active line when it changes
watch(currentIndex, (newIndex) => {
  scrollToActiveLine(newIndex, true);
});

// Scroll to the active line immediately when the component opens
onMounted(async () => {
  if (lyrics.value.length > 0) {
    // Wait for the DOM to render the lyric lines
    await nextTick();
    scrollToActiveLine(currentIndex.value, false);
  }
});

// Also watch for when lyrics finish loading while the player is already open
watch(lyrics, async (newLyrics) => {
  if (newLyrics.length > 0) {
    await nextTick();
    scrollToActiveLine(currentIndex.value, false);
  }
});

const formatTime = (seconds: number) => {
  const min = Math.floor(seconds / 60);
  const sec = Math.floor(seconds % 60);
  return `${min}:${sec.toString().padStart(2, '0')}`;
};

const seekTo = (timeMs: number) => {
  if (timeMs === Number.MAX_SAFE_INTEGER) return;
  store.seek(timeMs / 1000);
};
</script>

<template>
  <div v-if="currentTrack" class="fixed inset-0 z-50 bg-black/95 text-white flex flex-col">
    <!-- Close Button -->
    <div class="flex justify-end pt-12 pr-6 flex-shrink-0">
      <button @click="$emit('close')" class="p-2.5 hover:bg-white/10 rounded-full transition-colors">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
    </div>

    <!-- Main Content: Two Columns -->
    <div class="flex-1 flex flex-col md:flex-row items-center justify-center gap-12 lg:gap-32 xl:gap-64 px-8 pb-8 overflow-hidden min-h-0">
      
      <!-- Left Column: Cover + Info + Controls (all centered) -->
      <div class="flex-1 flex flex-col items-center justify-center max-w-md">
        <!-- Album Cover -->
        <div class="w-56 h-56 md:w-64 md:h-64 lg:w-80 lg:h-80 shadow-2xl rounded-xl overflow-hidden flex-shrink-0 relative">
          <img :src="currentTrack.album.images[0]?.url" 
               class="w-full h-full object-cover" />
          <div v-if="store.isBuffering" class="absolute inset-0 flex items-center justify-center bg-black/40">
            <div class="animate-spin rounded-full h-14 w-14 border-t-2 border-b-2 border-white"></div>
          </div>
        </div>

        <!-- Track Info -->
        <div class="mt-8 w-full px-4 flex flex-col items-center">
          <div class="w-full relative max-w-md group">
            <div class="text-center px-12">
              <h1 class="text-3xl font-bold truncate">{{ currentTrack.title }}</h1>
              <p class="text-lg text-white/60 mt-1 truncate">{{ currentTrack.artists.map(a => a.name).join(', ') }}</p>
            </div>
            <button 
              @click.stop="libraryStore.toggleFavorite(currentTrack)" 
              class="absolute right-0 top-1/2 -translate-y-1/2 p-2.5 hover:bg-white/10 rounded-full transition-colors shrink-0"
              :class="libraryStore.isTrackFavorite(currentTrack.ids.deezer) ? 'text-primary' : 'text-white/40 hover:text-white'"
            >
              <svg v-if="libraryStore.isTrackFavorite(currentTrack.ids.deezer)" xmlns="http://www.w3.org/2000/svg" class="w-7 h-7 fill-current" viewBox="0 0 24 24"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>
            </button>
          </div>
          <p class="text-sm text-white/30 mt-2 truncate text-center">{{ currentTrack.album.title }}</p>
        </div>

        <!-- Progress Bar -->
        <div class="w-full mt-8 flex items-center gap-3">
          <span class="text-[11px] text-white/50 font-mono w-9 text-right">{{ formatTime(isDragging ? localProgress : store.progress) }}</span>
          <input type="range" 
                 :value="isDragging ? localProgress : store.progress" 
                 :max="store.duration || 0"
                 step="0.1"
                 :disabled="store.isBuffering"
                 @input="onSeekInput"
                 @change="onSeekChange"
                 @mousedown="isDragging = true"
                 @touchstart="isDragging = true"
                 class="flex-1 accent-white h-1 rounded-lg"
                 :class="store.isBuffering ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'" />
          <span class="text-[11px] text-white/50 font-mono w-9">{{ formatTime(store.duration) }}</span>
        </div>

        <!-- Playback Controls -->
        <div class="w-full flex justify-between items-center mt-8 px-2">
          <!-- Shuffle -->
          <button 
            @click="store.toggleShuffle"
            class="p-2 transition-colors"
            :class="store.isShuffle ? 'text-white' : 'text-white/30 hover:text-white/50'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 18h1.4c1.3 0 2.5-.6 3.3-1.7l6.1-8.6c.7-1.1 2-1.7 3.3-1.7H22"/><path d="m18 2 4 4-4 4"/><path d="M2 6h1.9c1.2 0 2.3.6 3 1.5l3.8 5c.3.4.7.7 1.1 1l.5.3c.6.4 1.3.7 2 .7h7.7"/><path d="m18 14 4 4-4 4"/></svg>
          </button>

          <!-- Previous -->
          <button @click="store.prev" class="p-2 hover:text-white/80 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="currentColor" viewBox="0 0 24 24"><path d="M6 6h2v12H6zm3.5 6 8.5 6V6z"/></svg>
          </button>

          <!-- Play/Pause -->
          <button @click="store.togglePlay" class="p-5 bg-white text-black rounded-full hover:scale-105 transition-transform shadow-xl">
            <svg v-if="!store.isPlaying" xmlns="http://www.w3.org/2000/svg" class="h-10 w-10" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-10 w-10" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
          </button>

          <!-- Next -->
          <button @click="store.next" class="p-2 hover:text-white/80 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="currentColor" viewBox="0 0 24 24"><path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/></svg>
          </button>

          <!-- Repeat -->
          <button 
            @click="store.toggleRepeat"
            class="p-2 transition-colors relative"
            :class="store.repeatMode !== 'off' ? 'text-white' : 'text-white/30 hover:text-white/50'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m17 2 4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><path d="m7 22-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
            <span v-if="store.repeatMode === 'one'" class="absolute -top-1 -right-1 text-[10px] font-bold bg-white text-black w-3.5 h-3.5 rounded-full flex items-center justify-center">1</span>
          </button>
        </div>

      </div>

      <!-- Right Column: Lyrics (centered) -->
      <div class="flex-1 flex flex-col items-center justify-center relative min-h-0 h-full overflow-hidden max-w-2xl">
        <!-- Loading State -->
        <div v-if="store.isLoadingLyrics" class="flex flex-col items-center gap-3">
          <div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-white/40"></div>
          <p class="text-white/40 text-sm">{{ $t('player.searching_lyrics') }}</p>
        </div>

        <!-- No Lyrics -->
        <div v-else-if="lyrics.length === 0" class="text-white/25 text-lg italic text-center px-8">
          {{ $t('player.lyrics_not_available') }}
        </div>

        <!-- Lyrics List -->
        <div v-else ref="lyricsList" class="w-full h-full overflow-y-auto scrollbar-hide py-[40vh] px-4 space-y-2 select-none">
          <div v-for="(line, index) in lyrics" 
               :key="index"
               class="lyric-line py-4 px-6 rounded-2xl cursor-pointer hover:bg-white/5 text-center group/line"
               :class="{
                 'text-white scale-110 opacity-100 blur-none font-bold': index === currentIndex,
                 'text-white/30 opacity-40 font-semibold scale-95': index !== currentIndex,
                 'translate-y-4': index > currentIndex,
                 '-translate-y-4': index < currentIndex
               }"
               @click="seekTo(line.timeMs)">
            <p class="text-2xl md:text-3xl lg:text-4xl xl:text-5xl leading-relaxed"
               :class="{ 'drop-shadow-[0_0_20px_rgba(255,255,255,0.3)]': index === currentIndex }">
              {{ line.text }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.lyric-line {
  scroll-margin: 35vh;
  transition: transform 0.3s ease-out, opacity 0.3s ease-out, filter 0.3s ease-out;
  will-change: transform, opacity, filter;
  transform: translateZ(0);
}

.lyric-line p {
  transition: filter 0.3s ease-out, transform 0.3s ease-out;
}

input[type='range']::-webkit-slider-thumb {
  appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: white;
}
</style>