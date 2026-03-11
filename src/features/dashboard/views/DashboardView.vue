<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { SearchService } from '../../search/services/searchService';
import { usePlaybackStore } from '../../playback/stores/usePlaybackStore';
import type { Track, Album, Artist, Playlist } from '../../search/models/search';
import { getImageUrl } from '../../search/utils/image';
import LoadingSpinner from '../../search/components/LoadingSpinner.vue';

const { t } = useI18n();
const router = useRouter();
const playbackStore = usePlaybackStore();

const charts = ref<{
  tracks: Track[];
  albums: Album[];
  artists: Artist[];
  playlists: Playlist[];
} | null>(null);
const isLoading = ref(true);

const playTrack = (track: Track) => {
  playbackStore.playTrack(track, { type: 'top', items: charts.value?.tracks || [] });
};

onMounted(async () => {
  try {
    charts.value = await SearchService.getCharts();
  } catch (e) {
    console.error('Failed to load charts:', e);
  } finally {
    isLoading.value = false;
  }
});
</script>

<template>
  <div class="h-full bg-background overflow-y-auto custom-scrollbar p-8">
    <div v-if="isLoading" class="flex items-center justify-center h-full">
      <LoadingSpinner size="lg" />
    </div>

    <div v-else-if="charts" class="space-y-12">
      <!-- Welcome Hero -->
      <section class="mb-12">
        <h1 class="text-4xl font-black mb-2 tracking-tight">{{ t("dashboard.welcome") }}</h1>
      </section>

      <!-- Top Albums -->
      <section>
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-2xl font-bold tracking-tight">{{ t("search.categories.albums") }}</h2>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
          <div 
            v-for="album in charts.albums.slice(0, 6)" 
            :key="album.ids.deezer"
            @click="router.push(`/album/${album.ids.deezer}`)"
            class="group bg-surface/30 p-4 rounded-xl border border-white/5 hover:bg-surface/60 transition-all cursor-pointer"
          >
            <div class="aspect-square mb-4 shadow-xl relative overflow-hidden rounded-lg">
              <img :src="getImageUrl(album.images)" class="w-full h-full object-cover transform group-hover:scale-110 transition-transform duration-500" />
              <div class="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <div class="w-12 h-12 bg-primary rounded-full flex items-center justify-center shadow-lg transform translate-y-4 group-hover:translate-y-0 transition-transform">
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-black fill-current" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                </div>
              </div>
            </div>
            <h3 class="font-bold text-sm truncate mb-1">{{ album.title }}</h3>
            <p class="text-xs text-textGray truncate">{{ album.artists[0]?.name }}</p>
          </div>
        </div>
      </section>

      <!-- Featured Row: Top Tracks & Playlists -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-12">
        <!-- Top Tracks -->
        <div class="lg:col-span-2">
          <h2 class="text-2xl font-bold mb-6 tracking-tight">{{ t("search.popular_songs") }}</h2>
          <div class="bg-surface/20 rounded-2xl border border-white/5 p-4">
            <div 
              v-for="(track, index) in charts.tracks.slice(0, 5)" 
              :key="track.ids.deezer"
              @click="playTrack(track)"
              class="group flex items-center gap-4 p-3 rounded-xl hover:bg-white/5 transition-colors cursor-pointer"
            >
              <span class="w-6 text-center text-textGray text-sm font-mono">{{ index + 1 }}</span>
              <img :src="getImageUrl(track.album.images)" class="w-12 h-12 object-cover rounded shadow-lg" />
              <div class="flex-1 min-w-0">
                <h3 class="font-bold text-sm truncate group-hover:text-primary transition-colors" :class="{ 'text-primary': playbackStore.currentTrack?.ids.deezer === track.ids.deezer }">
                  {{ track.title }}
                </h3>
                <p class="text-xs text-textGray truncate">{{ track.artists[0]?.name }}</p>
              </div>
              <div class="opacity-0 group-hover:opacity-100 transition-opacity">
                <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-textGray" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        <!-- Top Playlists -->
        <div>
          <h2 class="text-2xl font-bold mb-6 tracking-tight">{{ t("search.categories.playlists") }}</h2>
          <div class="space-y-4">
            <div 
              v-for="playlist in charts.playlists.slice(0, 4)" 
              :key="playlist.ids.deezer"
              @click="router.push(`/playlist/${playlist.ids.deezer}`)"
              class="flex items-center gap-4 p-3 bg-surface/30 rounded-xl border border-white/5 hover:bg-surface/50 transition-all cursor-pointer group"
            >
              <img :src="getImageUrl(playlist.images)" class="w-16 h-16 object-cover rounded-lg shadow-lg" />
              <div class="flex-1 min-w-0">
                <h3 class="font-bold text-sm truncate group-hover:text-primary transition-colors">{{ playlist.title }}</h3>
                <p class="text-[10px] text-textGray uppercase tracking-wider font-bold mt-1">{{ playlist.nb_tracks }} {{ t("search.categories.tracks") }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Top Artists -->
      <section class="pb-12">
        <h2 class="text-2xl font-bold mb-6 tracking-tight">{{ t("search.categories.artists") }}</h2>
        <div class="flex gap-8 overflow-x-auto pb-4 custom-scrollbar">
          <div 
            v-for="artist in charts.artists.slice(0, 8)" 
            :key="artist.ids.deezer"
            @click="router.push(`/artist/${artist.ids.deezer}`)"
            class="flex-shrink-0 flex flex-col items-center group cursor-pointer"
          >
            <div class="w-32 h-32 rounded-full overflow-hidden mb-3 shadow-xl border-2 border-transparent group-hover:border-primary transition-all">
              <img :src="getImageUrl(artist.images)" class="w-full h-full object-cover transform group-hover:scale-110 transition-transform duration-500" />
            </div>
            <h3 class="font-bold text-sm text-center group-hover:text-primary transition-colors w-32 truncate">{{ artist.name }}</h3>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>
