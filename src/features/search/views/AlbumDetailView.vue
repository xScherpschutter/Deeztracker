<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { SearchService } from '../services/searchService';
import { usePlaybackStore } from '../../playback/stores/usePlaybackStore';
import { useDownloadStore } from '../../library/stores/useDownloadStore';
import type { Album, Track } from '../models/search';
import { useI18n } from 'vue-i18n';
import { getImageUrl } from '../utils/image';
import LoadingSpinner from '../components/LoadingSpinner.vue';
import TrackList from '../../../components/TrackList.vue';
import AddToPlaylistModal from '../../library/components/AddToPlaylistModal.vue';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const playbackStore = usePlaybackStore();
const downloadStore = useDownloadStore();
const album = ref<Album | null>(null);
const isLoading = ref(true);

const isPlaylistModalOpen = ref(false);
const selectedTrack = ref<Track | null>(null);

const tracksWithAlbum = computed(() => {
  if (!album.value) return [];
  return album.value.tracks.map(t => ({
    ...t,
    album: {
      ...album.value,
    }
  })) as unknown as Track[];
});

const openPlaylistModal = (track: any) => {
  const trackWithAlbum = {
    ...track,
    album: {
      ...album.value,
    }
  } as Track;
  selectedTrack.value = trackWithAlbum;
  isPlaylistModalOpen.value = true;
};

const playTrack = (track: any) => {
  if (!album.value) return;
  
  const tracksWithAlbum = album.value.tracks.map(t => ({
    ...t,
    album: {
      ...album.value,
    }
  })) as unknown as Track[];
  
  const currentTrackWithAlbum = tracksWithAlbum.find(t => t.ids.deezer === track.ids.deezer);
  if (currentTrackWithAlbum) {
    playbackStore.playTrack(currentTrackWithAlbum, { type: 'album', items: tracksWithAlbum });
  }
};

const playAlbum = () => {
  if (album.value && album.value.tracks.length > 0) {
    playTrack(album.value.tracks[0]);
  }
};

const addAlbumToQueue = () => {
  if (!album.value) return;
  const tracksWithAlbum = album.value.tracks.map(t => ({
    ...t,
    album: {
      ...album.value,
    }
  })) as unknown as Track[];
  playbackStore.addTracksToQueue(tracksWithAlbum);
};

const downloadAlbum = () => {
  if (album.value?.ids.deezer) {
    downloadStore.downloadAlbum(album.value.ids.deezer);
  }
};

onMounted(async () => {
  const id = route.params.id as string;
  try {
    album.value = await SearchService.getAlbum(id);
  } catch (e) {
    console.error('Failed to load album:', e);
  } finally {
    isLoading.value = false;
  }
});
</script>

<template>
  <div class="h-full flex flex-col bg-background">
    <LoadingSpinner v-if="isLoading" size="lg" />

    <div v-else-if="album" class="flex-1 overflow-y-auto custom-scrollbar">
      <!-- Hero Header -->
      <div class="relative h-80 flex items-end p-8 gap-8 overflow-hidden">
        <!-- Background Blur -->
        <div 
          class="absolute inset-0 bg-cover bg-center opacity-20 blur-3xl scale-110"
          :style="{ backgroundImage: `url(${getImageUrl(album.images)})` }"
        ></div>
        <div class="absolute inset-0 bg-gradient-to-t from-background via-background/40 to-transparent"></div>

        <img 
          :src="getImageUrl(album.images)" 
          class="w-52 h-52 shadow-2xl rounded-lg z-10 relative object-cover"
        />
        
        <div class="flex-1 z-10 relative mb-2">
          <span class="text-xs font-bold uppercase tracking-widest text-primary mb-2 block">{{ t('search.album_label') }}</span>
          <h1 class="text-5xl font-black mb-4 tracking-tighter">{{ album.title }}</h1>
          <div class="flex items-center gap-2 text-sm font-medium">
            <span class="hover:underline cursor-pointer" @click="router.push(`/artist/${album.artists[0].ids.deezer}`)">
              {{ album.artists.map(a => a.name).join(', ') }}
            </span>
            <span class="text-textGray">•</span>
            <span class="text-textGray">{{ album.release_date.year }}</span>
            <span class="text-textGray">•</span>
            <span class="text-textGray">{{ t('search.track_count', album.total_tracks) }}</span>
          </div>
        </div>
      </div>

      <!-- Controls Row -->
      <div class="p-8 flex items-center gap-6">
        <button 
          @click="playAlbum"
          class="w-14 h-14 bg-primary rounded-full flex items-center justify-center shadow-lg hover:scale-105 active:scale-95 transition-all group"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-7 h-7 text-black fill-current ml-1" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
        </button>

        <button 
          @click="addAlbumToQueue"
          class="w-12 h-12 bg-white/5 hover:bg-white/10 text-white rounded-full flex items-center justify-center border border-white/10 transition-all hover:scale-105 active:scale-95"
          :title="t('playback.add_to_queue')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
        </button>

        <button 
          @click="downloadAlbum"
          class="flex items-center gap-2 px-6 py-3 bg-white/5 hover:bg-white/10 rounded-full border border-white/10 transition-all font-bold text-sm disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white/5"
          :disabled="!!downloadStore.batchProgress"
        >
          <template v-if="downloadStore.batchProgress?.track_id === String(album.ids.deezer)">
            <div class="w-4 h-4 border-2 border-primary/20 border-t-primary rounded-full animate-spin"></div>
            <span>{{ downloadStore.batchProgress.current }} / {{ downloadStore.batchProgress.total }}</span>
          </template>
          <template v-else>
            <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            <span>{{ t('playback.download_all') }}</span>
          </template>
        </button>
      </div>

      <!-- Tracks Table -->
      <div class="px-8 pb-12">
        <TrackList 
          :tracks="tracksWithAlbum"
          :show-album="false"
          :show-add-to-playlist="true"
          @play="playTrack"
          @add-to-playlist="openPlaylistModal"
        />
      </div>
    </div>
    
    <AddToPlaylistModal :is-open="isPlaylistModalOpen" :track="selectedTrack" @close="isPlaylistModalOpen = false" />
  </div>
</template>
