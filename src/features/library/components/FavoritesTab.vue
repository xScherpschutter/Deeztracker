<script setup lang="ts">
import { ref, computed } from 'vue';
import { useLibraryStore } from '../stores/useLibraryStore';
import { usePlaybackStore } from '../../playback/stores/usePlaybackStore';
import { useI18n } from 'vue-i18n';
import type { Track } from '../../search/models/search';
import TrackList from '../../../components/TrackList.vue';

const libraryStore = useLibraryStore();
const playbackStore = usePlaybackStore();
const { t } = useI18n();

const searchQuery = ref('');
const sortBy = ref<'added_at' | 'title' | 'artist' | 'duration'>('added_at');
const sortOrder = ref<'asc' | 'desc'>('desc');

const filteredFavorites = computed(() => {
  let items = [...libraryStore.favorites];

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase();
    items = items.filter(t => 
      t.title.toLowerCase().includes(q) || 
      t.artists.some(a => a.name.toLowerCase().includes(q))
    );
  }

  items.sort((a, b) => {
    let comparison = 0;
    switch (sortBy.value) {
      case 'added_at':
        const timeA = a.added_at ? new Date(a.added_at).getTime() : 0;
        const timeB = b.added_at ? new Date(b.added_at).getTime() : 0;
        comparison = timeA - timeB;
        break;
      case 'title':
        comparison = a.title.localeCompare(b.title);
        break;
      case 'artist':
        comparison = (a.artists[0]?.name || '').localeCompare(b.artists[0]?.name || '');
        break;
      case 'duration':
        comparison = (a.duration_ms || 0) - (b.duration_ms || 0);
        break;
    }
    return sortOrder.value === 'asc' ? comparison : -comparison;
  });

  return items;
});

const playFavorite = (track: Track) => {
  playbackStore.playTrack(track, { type: 'playlist', items: filteredFavorites.value });
};

const playAllFavorites = () => {
  if (filteredFavorites.value.length > 0) {
    playFavorite(filteredFavorites.value[0]);
  }
};

const toggleSort = (key: string) => {
  const sortKey = key as any;
  if (sortBy.value === sortKey) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortBy.value = sortKey;
    sortOrder.value = 'desc';
  }
};
</script>

<template>
  <div class="flex-1 flex flex-col space-y-6">
    <div v-if="libraryStore.favorites.length === 0" class="flex-1 flex flex-col items-center justify-center opacity-50">
      <svg xmlns="http://www.w3.org/2000/svg" class="w-16 h-16 mb-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>
      <p>{{ t('library.no_favorites') }}</p>
    </div>
    
    <div v-else class="flex flex-col flex-1">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div class="flex items-center gap-4">
          <button 
            @click="playAllFavorites"
            class="w-12 h-12 bg-primary rounded-full flex items-center justify-center shadow-lg hover:scale-105 active:scale-95 transition-all flex-shrink-0"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-black fill-current ml-1" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          </button>
          
          <div class="relative group max-w-md w-64 md:w-80">
            <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-textGray group-focus-within:text-primary transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
            </div>
            <input 
              v-model="searchQuery"
              type="text" 
              :placeholder="t('search.placeholder')"
              class="w-full bg-white/5 border border-white/10 rounded-full py-3 pl-12 pr-6 text-sm focus:outline-none focus:border-primary/40 focus:bg-white/10 transition-all shadow-inner"
            />
          </div>
        </div>

        <div class="flex items-center gap-4 text-xs text-textGray bg-white/5 p-1 rounded-full border border-white/5">
          <button 
            @click="toggleSort('added_at')" 
            class="hover:text-white transition-all px-4 py-1.5 rounded-full"
            :class="{ 'bg-white/10 text-primary shadow-sm': sortBy === 'added_at' }"
          >
            {{ t('library.added_at') }}
            <span v-if="sortBy === 'added_at'" class="ml-1">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
          </button>
          <button 
            @click="toggleSort('title')" 
            class="hover:text-white transition-all px-4 py-1.5 rounded-full"
            :class="{ 'bg-white/10 text-primary shadow-sm': sortBy === 'title' }"
          >
            {{ t('search.track_title') }}
            <span v-if="sortBy === 'title'" class="ml-1">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
          </button>
        </div>
      </div>
      
      <TrackList 
        :tracks="filteredFavorites"
        :show-added-at="true"
        @play="playFavorite"
        @toggle-sort="toggleSort"
      />
    </div>
  </div>
</template>
