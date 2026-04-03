<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useSearchStore } from '../stores/useSearchStore';
import { usePlaybackStore } from '../../playback/stores/usePlaybackStore';
import type { SearchType, Track } from '../models/search';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { getImageUrl } from '../utils/image';
import LoadingSpinner from '../components/LoadingSpinner.vue';
import TrackList from '../../../components/TrackList.vue';
import AddToPlaylistModal from '../../library/components/AddToPlaylistModal.vue';

const { t } = useI18n();
const searchStore = useSearchStore();
const playbackStore = usePlaybackStore();
const router = useRouter();
const scrollContainer = ref<HTMLElement | null>(null);

const isPlaylistModalOpen = ref(false);
const selectedTrack = ref<Track | null>(null);

const openPlaylistModal = (track: Track) => {
  selectedTrack.value = track;
  isPlaylistModalOpen.value = true;
};

const hasNoResults = computed(() => 
  !searchStore.isLoading && searchStore.query.length > 1 && 
  Object.values(searchStore.results).every(r => r.length === 0)
);

const categories = computed<{ label: string; value: SearchType }[]>(() => [
  { label: t('search.categories.all'), value: 'all' },
  { label: t('search.categories.tracks'), value: 'tracks' },
  { label: t('search.categories.albums'), value: 'albums' },
  { label: t('search.categories.artists'), value: 'artists' },
  { label: t('search.categories.playlists'), value: 'playlists' }
]);

const setType = (type: SearchType) => {
  searchStore.activeType = type;
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = 0;
  }
};

// Infinite scroll logic
const handleScroll = () => {
  if (!scrollContainer.value || searchStore.activeType === 'all') return;
  
  const { scrollTop, scrollHeight, clientHeight } = scrollContainer.value;
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
  <div class="h-full flex flex-col overflow-hidden bg-background text-white">
    <!-- Header: Search Input & Filters (Fixed with padding) -->
    <div class="p-8 pb-4 space-y-6 flex-shrink-0">
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

    <!-- Results Area (Scrollable) -->
    <div ref="scrollContainer" class="flex-1 overflow-y-auto px-8 pb-12 custom-scrollbar">
      <!-- Loading State -->
      <LoadingSpinner v-if="searchStore.isLoading" size="lg" />

      <!-- Empty State -->
      <div v-else-if="!searchStore.query" class="flex flex-col items-center justify-center h-full opacity-40">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-16 h-16 mb-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
        <p class="text-lg">{{ t('search.empty_state') }}</p>
      </div>

      <!-- No Results -->
      <div v-else-if="hasNoResults" class="flex flex-col items-center justify-center h-full opacity-60 px-4 text-center">
        <p class="text-xl font-medium">{{ t('search.no_results', { query: searchStore.query }) }}</p>
        <p class="text-sm text-textGray mt-2">{{ t('search.no_results_help') }}</p>
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
            
            <TrackList 
              :tracks="searchStore.results.tracks"
              :show-header="searchStore.activeType === 'tracks'"
              :show-add-to-playlist="true"
              @play="(t) => playbackStore.playTrack(t)"
              @add-to-playlist="openPlaylistModal"
            />
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
                @click="router.push(`/album/${album.ids.deezer}`)"
                class="group bg-surface/30 p-4 rounded-xl border border-white/5 hover:bg-surface/60 transition-all hover:translate-y-[-4px] cursor-pointer grid-item-optimized"
              >
                <div class="aspect-square mb-4 shadow-2xl relative">
                  <img :src="getImageUrl(album.images)" class="w-full h-full object-cover rounded-lg" />
                  <div class="absolute bottom-2 right-2 w-10 h-10 bg-primary rounded-full shadow-lg flex items-center justify-center opacity-0 translate-y-2 group-hover:opacity-100 group-hover:translate-y-0 transition-all">
                    <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-black fill-current" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                  </div>
                </div>
                <h3 class="font-bold text-sm truncate mb-1">{{ album.title }}</h3>
                <p class="text-xs text-textGray truncate">{{ album.artists.map(a => a.name).join(', ') }}</p>
                <p class="text-[10px] text-textGray/60 mt-2 uppercase tracking-tighter">{{ album.album_type }}</p>
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
                @click="router.push(`/artist/${artist.ids.deezer}`)"
                class="group flex flex-col items-center text-center p-4 rounded-xl hover:bg-surface/40 transition-all cursor-pointer grid-item-optimized"
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
                @click="router.push(`/playlist/${playlist.ids.deezer}`)"
                class="group bg-surface/30 p-4 rounded-xl border border-white/5 hover:bg-surface/60 transition-all cursor-pointer grid-item-optimized"
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


      </div>
    </div>
    
    <AddToPlaylistModal :is-open="isPlaylistModalOpen" :track="selectedTrack" @close="isPlaylistModalOpen = false" />
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

.list-item-optimized {
  content-visibility: auto;
  contain-intrinsic-size: 0 64px;
}

.grid-item-optimized {
  content-visibility: auto;
  contain-intrinsic-size: 200px 300px;
}
</style>
