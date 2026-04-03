<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { SearchService } from '../services/searchService';
import { usePlaybackStore } from '../../playback/stores/usePlaybackStore';
import { useDownloadStore } from '../../library/stores/useDownloadStore';
import type { Playlist, Track } from '../models/search';
import { useI18n } from 'vue-i18n';
import { getImageUrl } from '../utils/image';
import LoadingSpinner from '../components/LoadingSpinner.vue';
import TrackList from '../../../components/TrackList.vue';
import AddToPlaylistModal from '../../library/components/AddToPlaylistModal.vue';

const { t } = useI18n();
const route = useRoute();
const playbackStore = usePlaybackStore();
const downloadStore = useDownloadStore();
const playlist = ref<Playlist | null>(null);
const isLoading = ref(true);

const isPlaylistModalOpen = ref(false);
const selectedTrack = ref<Track | null>(null);

const openPlaylistModal = (track: Track) => {
  selectedTrack.value = track;
  isPlaylistModalOpen.value = true;
};

const formatLongDuration = (ms: number) => {
  const totalSeconds = Math.floor(ms / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  
  if (hours > 0) {
    return `${hours} h ${minutes} min`;
  }
  return `${minutes} min`;
};

const playTrack = (track: Track) => {
  if (!playlist.value) return;
  playbackStore.playTrack(track, { type: 'playlist', items: playlist.value.tracks });
};

const playPlaylist = () => {
  if (playlist.value && playlist.value.tracks.length > 0) {
    playTrack(playlist.value.tracks[0]);
  }
};

const downloadPlaylist = () => {
  if (playlist.value?.ids.deezer) {
    downloadStore.downloadPlaylist(playlist.value.ids.deezer);
  }
};

onMounted(async () => {
  const id = route.params.id as string;
  try {
    playlist.value = await SearchService.getPlaylist(id);
  } catch (e) {
    console.error('Failed to load playlist:', e);
  } finally {
    isLoading.value = false;
  }
});
</script>

<template>
  <div class="h-full flex flex-col bg-background">
    <LoadingSpinner v-if="isLoading" size="lg" />

    <div v-else-if="playlist" class="flex-1 overflow-y-auto custom-scrollbar">
      <!-- Hero Header -->
      <div class="relative h-80 flex items-end p-8 gap-8 overflow-hidden">
        <!-- Background Blur -->
        <div 
          class="absolute inset-0 bg-cover bg-center opacity-20 blur-3xl scale-110"
          :style="{ backgroundImage: `url(${getImageUrl(playlist.images)})` }"
        ></div>
        <div class="absolute inset-0 bg-gradient-to-t from-background via-background/40 to-transparent"></div>

        <img 
          :src="getImageUrl(playlist.images)" 
          class="w-52 h-52 shadow-2xl rounded-lg z-10 relative object-cover"
        />
        
        <div class="flex-1 z-10 relative mb-2">
          <span class="text-xs font-bold uppercase tracking-widest text-primary mb-2 block">{{ t('search.categories.playlists') }}</span>
          <h1 class="text-5xl font-black mb-4 tracking-tighter">{{ playlist.title }}</h1>
          <div class="flex items-center gap-2 text-sm font-medium">
            <span class="text-white">{{ playlist.user?.name || t('search.unknown_user') }}</span>
            <span class="text-textGray">•</span>
            <span class="text-textGray">{{ t('search.track_count', playlist.nb_tracks) }}</span>
            <span v-if="playlist.duration_ms" class="text-textGray">•</span>
            <span v-if="playlist.duration_ms" class="text-textGray">{{ formatLongDuration(playlist.duration_ms) }}</span>
          </div>
        </div>
      </div>

      <!-- Controls Row -->
      <div class="p-8 flex items-center gap-6">
        <button 
          @click="playPlaylist"
          class="w-14 h-14 bg-primary rounded-full flex items-center justify-center shadow-lg hover:scale-105 active:scale-95 transition-all group"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-7 h-7 text-black fill-current ml-1" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
        </button>

        <button 
          @click="downloadPlaylist"
          class="flex items-center gap-2 px-6 py-3 bg-white/5 hover:bg-white/10 rounded-full border border-white/10 transition-all font-bold text-sm disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white/5"
          :disabled="!!downloadStore.batchProgress"
        >
          <template v-if="downloadStore.batchProgress?.track_id === String(playlist.ids.deezer)">
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
          v-if="playlist.tracks"
          :tracks="playlist.tracks"
          :show-add-to-playlist="true"
          @play="playTrack"
          @add-to-playlist="openPlaylistModal"
        />
      </div>
    </div>

    <AddToPlaylistModal :is-open="isPlaylistModalOpen" :track="selectedTrack" @close="isPlaylistModalOpen = false" />
  </div>
</template>
