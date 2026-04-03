<script setup lang="ts">
import { computed, ref, watch, onMounted, nextTick } from 'vue';
import { usePlaybackStore } from '../stores/usePlaybackStore';
import { useSettingsStore } from '../../dashboard/stores/useSettingsStore';

const store = usePlaybackStore();
const settingsStore = useSettingsStore();
const lyricsList = ref<HTMLElement | null>(null);

const lyrics = computed(() => store.lyrics);
const currentIndex = computed(() => store.currentLineIndex);
const lyricsMode = computed(() => settingsStore.lyricsMode);

const scrollToActiveLine = (index: number, smooth: boolean = true) => {
  if (lyricsMode.value === 'current') return; // No scrolling in current mode
  
  if (index >= 0 && lyricsList.value) {
    const lines = lyricsList.value.querySelectorAll('.lyric-line');
    const activeLine = lines[index] as HTMLElement;
    
    if (activeLine) {
      const containerHeight = lyricsList.value.clientHeight;
      const lineOffset = activeLine.offsetTop;
      const lineHeight = activeLine.clientHeight;
      
      const scrollTo = lineOffset - (containerHeight / 2) + (lineHeight / 2);
      
      lyricsList.value.scrollTo({
        top: scrollTo,
        behavior: smooth ? 'smooth' : 'auto'
      });
    }
  }
};

watch(currentIndex, (newIndex) => {
  scrollToActiveLine(newIndex, true);
});

onMounted(async () => {
  if (lyrics.value.length > 0) {
    await nextTick();
    scrollToActiveLine(currentIndex.value, false);
  }
});

watch(lyrics, async (newLyrics) => {
  if (newLyrics.length > 0) {
    await nextTick();
    scrollToActiveLine(currentIndex.value, false);
  }
});

watch(lyricsMode, async () => {
  await nextTick();
  scrollToActiveLine(currentIndex.value, false);
});

const seekTo = (timeMs: number) => {
  if (timeMs === Number.MAX_SAFE_INTEGER) return;
  store.seek(timeMs / 1000);
};
</script>

<template>
  <div class="lyrics-container w-full h-full flex flex-col items-center justify-center relative overflow-hidden">
    <!-- Loading State -->
    <div v-if="store.isLoadingLyrics" class="flex flex-col items-center gap-3">
      <div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-white/40"></div>
      <p class="text-white/40 text-sm">{{ $t('player.searching_lyrics') }}</p>
    </div>

    <!-- No Lyrics -->
    <div v-else-if="lyrics.length === 0" class="text-white/25 text-lg italic text-center px-8">
      {{ $t('player.lyrics_not_available') }}
    </div>

    <!-- Lyrics Content -->
    <div v-else class="w-full h-full relative">
      
      <!-- Normal / Fade Modes -->
      <div v-if="lyricsMode !== 'current'" 
           ref="lyricsList" 
           class="w-full h-full overflow-y-auto scrollbar-hide py-[45vh] px-4 space-y-4 select-none"
      >
        <div v-for="(line, index) in lyrics" 
             :key="index"
             class="lyric-line py-4 px-6 rounded-2xl cursor-pointer hover:bg-white/5 text-center transition-all duration-[800ms] cubic-bezier(0.23, 1, 0.32, 1)"
             :class="{
               'active text-white scale-110 opacity-100 blur-none font-bold': index === currentIndex,
               'text-white/20 opacity-30 font-semibold scale-95 blur-[2px]': index !== currentIndex && (lyricsMode === 'normal' || index > currentIndex),
               'opacity-0 pointer-events-none scale-[1.4] translate-y-[-100px] translate-x-[80px] blur-[40px] rotate-3 skew-x-12': lyricsMode === 'fade' && index < currentIndex,
               'translate-y-4': index > currentIndex && lyricsMode === 'normal',
               '-translate-y-4': index < currentIndex && lyricsMode === 'normal'
             }"
             @click="seekTo(line.timeMs)">
          <p class="text-2xl md:text-3xl lg:text-4xl xl:text-5xl leading-tight"
             :class="{ 'drop-shadow-[0_0_20px_rgba(255,255,255,0.3)]': index === currentIndex }">
            {{ line.text }}
          </p>
        </div>
      </div>

      <!-- Current Only Mode -->
      <div v-else class="w-full h-full flex items-center justify-center px-8 select-none">
        <Transition name="lyric-fade" mode="out-in">
          <div :key="currentIndex" class="text-center">
            <p v-if="currentIndex >= 0" 
               class="text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-bold leading-tight drop-shadow-[0_0_30px_rgba(255,255,255,0.4)]"
            >
              {{ lyrics[currentIndex].text }}
            </p>
            <p v-else class="text-white/20 italic">...</p>
          </div>
        </Transition>
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
  scroll-margin: 45vh;
  will-change: transform, opacity, filter;
}

/* Current Only Animation */
.lyric-fade-enter-active {
  transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
}
.lyric-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 1, 1);
}

.lyric-fade-enter-from {
  opacity: 0;
  transform: scale(0.9) translateY(20px);
}
.lyric-fade-leave-to {
  opacity: 0;
  transform: scale(1.05) translateY(-20px);
}

/* Optimize for performance */
.lyric-line {
  backface-visibility: hidden;
  transform: translateZ(0);
}
</style>
