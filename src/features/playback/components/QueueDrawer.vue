<script setup lang="ts">
import { computed } from 'vue';
import { usePlaybackStore } from '../stores/usePlaybackStore';
import { storeToRefs } from 'pinia';
import { useI18n } from 'vue-i18n';
import type { Track } from '../../search/models/search';

const { t } = useI18n();
const playbackStore = usePlaybackStore();
const { queue, currentIndex, isShuffle, shuffledIndices, showQueue } = storeToRefs(playbackStore);

const currentTrack = computed(() => playbackStore.currentTrack);

// Helper to get the correct display order based on shuffle
const displayQueue = computed(() => {
  let orderedQueue = [];
  if (!isShuffle.value || shuffledIndices.value.length === 0) {
    orderedQueue = queue.value.map((track, index) => ({ track, originalIndex: index }));
    // Find where we are in the linear queue
    const currentPos = currentIndex.value;
    return orderedQueue.slice(currentPos + 1);
  } else {
    orderedQueue = shuffledIndices.value.map((originalIndex) => ({
      track: queue.value[originalIndex],
      originalIndex
    }));
    // Find where we are in the shuffled sequence
    const currentPos = shuffledIndices.value.indexOf(currentIndex.value);
    return orderedQueue.slice(currentPos + 1);
  }
});

// Tracks that have already been played in the current session/context
const historyQueue = computed(() => {
  if (!isShuffle.value || shuffledIndices.value.length === 0) {
    const currentPos = currentIndex.value;
    return queue.value
      .slice(0, currentPos)
      .map((track, index) => ({ track, originalIndex: index }));
  } else {
    const currentPos = shuffledIndices.value.indexOf(currentIndex.value);
    return shuffledIndices.value
      .slice(0, currentPos)
      .map((originalIndex) => ({
        track: queue.value[originalIndex],
        originalIndex
      }));
  }
});

const playFromQueue = (originalIndex: number) => {
  playbackStore.currentIndex = originalIndex;
  playbackStore.startPlayback();
};

const clearQueue = () => {
  // Keep only current track if playing
  if (currentIndex.value !== -1) {
    const current = queue.value[currentIndex.value];
    playbackStore.queue = [current];
    playbackStore.currentIndex = 0;
    if (isShuffle.value) {
      playbackStore.shuffledIndices = [0];
    }
  } else {
    playbackStore.stop();
  }
};

const closeDrawer = () => {
  playbackStore.showQueue = false;
};
</script>

<template>
  <Transition
    enter-active-class="transition duration-300 ease-out"
    enter-from-class="translate-x-full"
    enter-to-class="translate-x-0"
    leave-active-class="transition duration-200 ease-in"
    leave-from-class="translate-x-0"
    leave-to-class="translate-x-full"
  >
    <div v-if="showQueue" class="fixed right-0 top-10 bottom-24 w-80 bg-surface/95 backdrop-blur-md border-l border-white/5 z-40 flex flex-col shadow-2xl">
      <!-- Header -->
      <div class="p-6 flex items-center justify-between border-b border-white/5">
        <h2 class="text-lg font-bold">{{ t('playback.queue_title') }}</h2>
        <div class="flex items-center gap-2">
          <button 
            @click="clearQueue" 
            class="text-xs text-textGray hover:text-white transition-colors p-1"
            :title="t('playback.clear_queue')"
          >
            {{ t('playback.clear_queue') }}
          </button>
          <button @click="closeDrawer" class="p-1 hover:bg-white/10 rounded-full transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
          </button>
        </div>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto custom-scrollbar p-4">
        <!-- Previously Played -->
        <div v-if="historyQueue.length > 0" class="mb-6 opacity-50 hover:opacity-100 transition-opacity">
          <div class="text-xs font-bold text-textGray uppercase tracking-wider mb-3 px-2">{{ t('playback.history') }}</div>
          <div class="space-y-1">
            <div 
              v-for="(item, index) in historyQueue" :key="'hist-'+index"
              @click="playFromQueue(item.originalIndex)"
              class="flex items-center gap-3 p-2 hover:bg-white/5 rounded-lg cursor-pointer group"
            >
              <div class="w-10 h-10 flex-shrink-0 grayscale group-hover:grayscale-0 transition-all">
                <img :src="item.track.album.images[0]?.url" class="w-full h-full rounded object-cover" alt="Cover">
              </div>
              <div class="min-w-0 flex-1">
                <div class="text-sm font-medium truncate">{{ item.track.title }}</div>
                <div class="text-xs text-textGray truncate">{{ item.track.artists[0]?.name }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Now Playing -->
        <div v-if="currentTrack" class="mb-6">
          <div class="text-xs font-bold text-textGray uppercase tracking-wider mb-3 px-2">{{ t('playback.now_playing') }}</div>
          <div class="flex items-center gap-3 p-2 bg-white/5 rounded-lg border border-primary/20 shadow-lg shadow-primary/5">
            <img :src="currentTrack.album.images[0]?.url" class="w-12 h-12 rounded object-cover shadow-lg" alt="Cover">
            <div class="min-w-0 flex-1">
              <div class="text-sm font-bold text-primary truncate">{{ currentTrack.title }}</div>
              <div class="text-xs text-textGray truncate">{{ currentTrack.artists.map(a => a.name).join(', ') }}</div>
            </div>
            <div class="flex gap-1 pr-2">
              <span class="w-1 h-3 bg-primary animate-bounce-slow-1"></span>
              <span class="w-1 h-3 bg-primary animate-bounce-slow-2"></span>
              <span class="w-1 h-3 bg-primary animate-bounce-slow-3"></span>
            </div>
          </div>
        </div>

        <!-- Next Up -->
        <div>
          <div class="text-xs font-bold text-textGray uppercase tracking-wider mb-3 px-2">{{ t('playback.next_up') }}</div>
          <div class="space-y-1">
            <template v-for="(item, index) in displayQueue" :key="'next-'+index">
              <div 
                @click="playFromQueue(item.originalIndex)"
                class="flex items-center gap-3 p-2 hover:bg-white/5 rounded-lg cursor-pointer group transition-all"
              >
                <div class="relative w-10 h-10 flex-shrink-0">
                  <img :src="item.track.album.images[0]?.url" class="w-full h-full rounded object-cover group-hover:opacity-60 transition-opacity" alt="Cover">
                  <div class="absolute inset-0 items-center justify-center hidden group-hover:flex">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" class="text-white"><path d="m5 3 14 9-14 9V3z"/></svg>
                  </div>
                </div>
                <div class="min-w-0 flex-1">
                  <div class="text-sm font-medium truncate group-hover:text-primary transition-colors">{{ item.track.title }}</div>
                  <div class="text-xs text-textGray truncate">{{ item.track.artists[0]?.name }}</div>
                </div>
              </div>
            </template>
            
            <div v-if="displayQueue.length === 0" class="text-center py-10">
              <p class="text-sm text-textGray">{{ t('playback.empty_queue') }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>
  
  <!-- Backdrop for small screens or to close by clicking outside -->
  <div v-if="showQueue" @click="closeDrawer" class="fixed inset-0 bg-black/20 z-30 lg:hidden"></div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}

@keyframes bounce-slow {
  0%, 100% { height: 4px; }
  50% { height: 12px; }
}

.animate-bounce-slow-1 { animation: bounce-slow 1s ease-in-out infinite; }
.animate-bounce-slow-2 { animation: bounce-slow 1.2s ease-in-out infinite; animation-delay: 0.2s; }
.animate-bounce-slow-3 { animation: bounce-slow 0.8s ease-in-out infinite; animation-delay: 0.4s; }
</style>