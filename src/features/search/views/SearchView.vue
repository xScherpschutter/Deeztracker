<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useSearchStore } from '../stores/useSearchStore';
import type { SearchType } from '../models/search';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const searchStore = useSearchStore();
const scrollContainer = ref<HTMLElement | null>(null);

const categories = computed<{ label: string; value: SearchType }[]>(() => [
  { label: t('search.categories.all'), value: 'all' },
  { label: t('search.categories.tracks'), value: 'tracks' },
  { label: t('search.categories.albums'), value: 'albums' },
  { label: t('search.categories.artists'), value: 'artists' },
  { label: t('search.categories.playlists'), value: 'playlists' }
]);

const setType = (type: SearchType) => {
  searchStore.activeType = type;
  // Scroll to top when changing category
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = 0;
  }
};

const formatDuration = (ms: number) => {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
};

const getImageUrl = (images: any[], fallback: string = '') => {
  if (!images || images.length === 0) return fallback;
  return images[Math.min(1, images.length - 1)].url;
};

// Infinite scroll logic
const handleScroll = () => {
  if (!scrollContainer.value || searchStore.activeType === 'all') return;
  
  const { scrollTop, scrollHeight, clientHeight } = scrollContainer.value;
  // If we are 200px from the bottom, load more
  if (scrollTop + clientHeight >= scrollHeight - 200) {
    searchStore.loadMore();
  }
};

onMounted(() => {
  if (scrollContainer.value) {
    scrollContainer.value.addEventListener('scroll', handleScroll);
  }
});

onUnmounted(() => {
  if (scrollContainer.value) {
    scrollContainer.value.removeEventListener('scroll', handleScroll);
  }
});
</script>

<template>
  <div class="flex flex-col h-full bg-background text-white p-8">
    <!-- Header: Search Input & Filters -->
    <div class="mb-10 space-y-6">
      <div class="relative max-w-2xl group">
        <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-textGray group-focus-within:text-primary transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
        </div>
        <input 
          v-model="searchStore.query"
          type="text"
          :placeholder="t('search.placeholder')"
          class="w-full bg-surface border border-white/5 rounded-full py-3.5 pl-12 pr-6 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:bg-surface/80 transition-all text-sm tracking-wide"
        />
      </div>

      <div class="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-hide">
        <button 
          v-for="cat in categories" 
          :key="cat.value"
          @click="setType(cat.value)"
          class="px-5 py-2 rounded-full text-sm font-medium transition-all whitespace-nowrap border border-white/5"
          :class="searchStore.activeType === cat.value 
            ? 'bg-primary text-black border-primary' 
            : 'bg-surface hover:bg-white/10 text-textGray hover:text-white'"
        >
          {{ cat.label }}
        </button>
      </div>
    </div>

    <!-- Results Area -->
    <div ref="scrollContainer" class="flex-1 overflow-y-auto pr-2 custom-scrollbar">
      <!-- Loading State -->
      <div v-if="searchStore.isLoading" class="flex items-center justify-center h-64">
        <div class="w-10 h-10 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
      </div>

      <!-- Empty State -->
      <div v-else-if="!searchStore.query" class="flex flex-col items-center justify-center h-64 opacity-40">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-16 h-16 mb-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
        <p class="text-lg">{{ t('search.empty_state') }}</p>
      </div>

      <!-- Results Content -->
      <div v-else class="space-y-12">
        
        <!-- Tracks Section -->
        <section v-if="searchStore.activeType === 'all' || searchStore.activeType === 'tracks'">
          <div v-if="searchStore.results.tracks.length > 0">
            <h2 class="text-xl font-bold mb-6 flex items-center justify-between">
              {{ t('search.categories.tracks') }}
              <button v-if="searchStore.activeType === 'all'" @click="setType('tracks')" class="text-xs text-textGray hover:text-primary uppercase tracking-widest">{{ t('search.view_all') }}</button>
            </h2>
            <div class="grid grid-cols-1 gap-1">
              <div 
                v-for="track in searchStore.results.tracks" 
                :key="track.ids.deezer"
                class="group flex items-center gap-4 p-2 rounded-lg hover:bg-white/5 transition-colors cursor-pointer"
              >
                <div class="relative w-12 h-12 flex-shrink-0">
                  <img :src="getImageUrl(track.album.images)" class="w-full h-full object-cover rounded-md shadow-lg" />
                  <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center rounded-md transition-opacity">
                    <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 fill-current text-white" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                  </div>
                </div>
                <div class="flex-1 min-w-0">
                  <h3 class="font-medium text-sm truncate group-hover:text-primary transition-colors">{{ track.title }}</h3>
                  <p class="text-xs text-textGray truncate">{{ track.artists.map(a => a.name).join(', ') }}</p>
                </div>
                <div class="hidden md:block flex-1 min-w-0 px-4">
                  <p class="text-xs text-textGray truncate">{{ track.album.title }}</p>
                </div>
                <div class="text-xs text-textGray font-mono tabular-nums pr-2">
                  {{ formatDuration(track.duration_ms) }}
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Albums Section -->
        <section v-if="searchStore.activeType === 'all' || searchStore.activeType === 'albums'">
          <div v-if="searchStore.results.albums.length > 0">
            <h2 class="text-xl font-bold mb-6 flex items-center justify-between">
              {{ t('search.categories.albums') }}
              <button v-if="searchStore.activeType === 'all'" @click="setType('albums')" class="text-xs text-textGray hover:text-primary uppercase tracking-widest">{{ t('search.view_all') }}</button>
            </h2>
            <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
              <div 
                v-for="album in searchStore.results.albums" 
                :key="album.ids.deezer"
                class="group bg-surface/30 p-4 rounded-xl border border-white/5 hover:bg-surface/60 transition-all hover:translate-y-[-4px] cursor-pointer"
              >
                <div class="aspect-square mb-4 shadow-2xl relative">
                  <img :src="getImageUrl(album.images)" class="w-full h-full object-cover rounded-lg" />
                  <div class="absolute bottom-2 right-2 w-10 h-10 bg-primary rounded-full shadow-lg flex items-center justify-center opacity-0 translate-y-2 group-hover:opacity-100 group-hover:translate-y-0 transition-all">
                    <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-black fill-current" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                  </div>
                </div>
                <h3 class="font-bold text-sm truncate mb-1">{{ album.title }}</h3>
                <p class="text-xs text-textGray truncate">{{ album.artists.map(a => a.name).join(', ') }}</p>
                <p class="text-[10px] text-textGray/60 mt-2 uppercase tracking-tighter">{{ album.album_type }} • {{ album.release_date.year }}</p>
              </div>
            </div>
          </div>
        </section>

        <!-- Artists Section -->
        <section v-if="searchStore.activeType === 'all' || searchStore.activeType === 'artists'">
          <div v-if="searchStore.results.artists.length > 0">
            <h2 class="text-xl font-bold mb-6 flex items-center justify-between">
              {{ t('search.categories.artists') }}
              <button v-if="searchStore.activeType === 'all'" @click="setType('artists')" class="text-xs text-textGray hover:text-primary uppercase tracking-widest">{{ t('search.view_all') }}</button>
            </h2>
            <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
              <div 
                v-for="artist in searchStore.results.artists" 
                :key="artist.ids.deezer"
                class="group flex flex-col items-center text-center p-4 rounded-xl hover:bg-surface/40 transition-all cursor-pointer"
              >
                <div class="w-32 h-32 md:w-40 md:h-40 mb-4 shadow-2xl relative">
                  <img :src="getImageUrl(artist.images)" class="w-full h-full object-cover rounded-full" />
                </div>
                <h3 class="font-bold text-sm truncate w-full group-hover:text-primary transition-colors">{{ artist.name }}</h3>
                <p class="text-xs text-textGray uppercase tracking-widest mt-1">{{ t('search.artist_label') }}</p>
              </div>
            </div>
          </div>
        </section>

        <!-- Playlists Section -->
        <section v-if="searchStore.activeType === 'all' || searchStore.activeType === 'playlists'">
          <div v-if="searchStore.results.playlists.length > 0">
            <h2 class="text-xl font-bold mb-6 flex items-center justify-between">
              {{ t('search.categories.playlists') }}
              <button v-if="searchStore.activeType === 'all'" @click="setType('playlists')" class="text-xs text-textGray hover:text-primary uppercase tracking-widest">{{ t('search.view_all') }}</button>
            </h2>
            <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
              <div 
                v-for="playlist in searchStore.results.playlists" 
                :key="playlist.ids.deezer"
                class="group bg-surface/30 p-4 rounded-xl border border-white/5 hover:bg-surface/60 transition-all cursor-pointer"
              >
                <div class="aspect-square mb-4 shadow-2xl relative">
                  <img :src="getImageUrl(playlist.images)" class="w-full h-full object-cover rounded-lg" />
                </div>
                <h3 class="font-bold text-sm truncate mb-1">{{ playlist.title }}</h3>
                <p class="text-xs text-textGray truncate">{{ t('search.playlist_by', { user: playlist.user?.name || t('search.unknown_user') }) }}</p>
              </div>
            </div>
          </div>
        </section>

        <!-- Loading More Spinner -->
        <div v-if="searchStore.isLoadingMore" class="flex justify-center py-8">
          <div class="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
        </div>

        <!-- No Results for Query -->
        <div v-if="Object.values(searchStore.results).every(r => r.length === 0) && !searchStore.isLoading" class="flex flex-col items-center justify-center h-64 opacity-60 px-4 text-center">
           <p class="text-xl font-medium">{{ t('search.no_results', { query: searchStore.query }) }}</p>
           <p class="text-sm text-textGray mt-2">{{ t('search.no_results_help') }}</p>
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

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.1);
}
</style>
