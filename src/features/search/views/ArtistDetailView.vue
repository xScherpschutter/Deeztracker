<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { SearchService } from '../services/searchService';
import type { Artist, Track, Album } from '../models/search';
import { useI18n } from 'vue-i18n';
import { formatDuration } from '../utils/time';
import { getImageUrl } from '../utils/image';
import LoadingSpinner from '../components/LoadingSpinner.vue';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const artist = ref<Artist | null>(null);
const topTracks = ref<Track[]>([]);
const albums = ref<Album[]>([]);
const isLoading = ref(true);

onMounted(async () => {
  const id = route.params.id as string;
  try {
    const [artistData, tracksData, albumsData] = await Promise.all([
      SearchService.getArtist(id),
      SearchService.getArtistTopTracks(id, 5),
      SearchService.getArtistAlbums(id, 12)
    ]);
    artist.value = artistData;
    topTracks.value = tracksData;
    albums.value = albumsData;
  } catch (e) {
    console.error('Failed to load artist details:', e);
  } finally {
    isLoading.value = false;
  }
});
</script>

<template>
  <div class="h-full flex flex-col bg-background">
    <LoadingSpinner v-if="isLoading" size="lg" />

    <div v-else-if="artist" class="flex-1 overflow-y-auto custom-scrollbar relative">
      <!-- Hero Header -->
      <div class="relative h-96 flex items-end p-8 gap-8 overflow-hidden">
        <!-- Background Blur -->
        <div 
          class="absolute inset-0 bg-cover bg-center opacity-30 blur-3xl scale-110"
          :style="{ backgroundImage: `url(${getImageUrl(artist.images)})` }"
        ></div>
        <div class="absolute inset-0 bg-gradient-to-t from-background via-background/40 to-transparent"></div>

        <div class="w-64 h-64 shadow-2xl rounded-full z-10 relative overflow-hidden border-4 border-white/5 flex-shrink-0">
          <img 
            :src="getImageUrl(artist.images)" 
            class="w-full h-full object-cover"
          />
        </div>
        
        <div class="flex-1 z-10 relative mb-6">
          <div class="flex items-center gap-2 mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-primary fill-current" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/></svg>
            <span class="text-sm font-bold uppercase tracking-widest text-white">{{ t('search.artist_label') }}</span>
          </div>
          <h1 class="text-7xl font-black mb-6 tracking-tighter">{{ artist.name }}</h1>
          <div class="flex items-center gap-4 text-sm font-medium">
            <span class="text-white">{{ artist.nb_fan?.toLocaleString() }} {{ t('search.fans') }}</span>
            <span class="text-textGray">•</span>
            <span class="text-white">{{ artist.nb_album }} {{ t('search.categories.albums') }}</span>
          </div>
        </div>
      </div>

      <!-- Content -->
      <div class="p-8 space-y-12 pb-12">
        <!-- Top Tracks -->
        <section>
          <h2 class="text-2xl font-bold mb-6">{{ t('search.popular_songs') }}</h2>
          <div class="grid grid-cols-1 gap-1">
            <div 
              v-for="(track, index) in topTracks" 
              :key="track.ids.deezer"
              class="group flex items-center gap-4 p-2 rounded-lg hover:bg-white/5 transition-colors cursor-pointer"
            >
              <span class="w-6 text-center text-textGray text-sm tabular-nums group-hover:text-white">{{ index + 1 }}</span>
              <img :src="getImageUrl(track.album.images)" class="w-10 h-10 object-cover rounded shadow-lg" />
              <div class="flex-1 min-w-0">
                <h3 class="font-medium text-sm truncate group-hover:text-primary transition-colors">{{ track.title }}</h3>
                <p v-if="track.explicit" class="text-[10px] bg-white/10 text-textGray px-1 rounded uppercase font-bold w-fit mt-0.5">E</p>
              </div>
              <span class="text-xs text-textGray tabular-nums">{{ formatDuration(track.duration_ms) }}</span>
            </div>
          </div>
        </section>

        <!-- Albums Grid -->
        <section>
          <h2 class="text-2xl font-bold mb-6">{{ t('search.categories.albums') }}</h2>
          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
            <div 
              v-for="album in albums" 
              :key="album.ids.deezer"
              @click="router.push(`/album/${album.ids.deezer}`)"
              class="group bg-surface/30 p-4 rounded-xl border border-white/5 hover:bg-surface/60 transition-all hover:translate-y-[-4px] cursor-pointer"
            >
              <div class="aspect-square mb-4 shadow-2xl relative">
                <img :src="getImageUrl(album.images)" class="w-full h-full object-cover rounded-lg" />
                <div class="absolute bottom-2 right-2 w-10 h-10 bg-primary rounded-full shadow-lg flex items-center justify-center opacity-0 translate-y-2 group-hover:opacity-100 group-hover:translate-y-0 transition-all">
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-black fill-current" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                </div>
              </div>
              <h3 class="font-bold text-sm truncate mb-1">{{ album.title }}</h3>
              <p class="text-xs text-textGray truncate">{{ album.release_date.year }}</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>
