<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { SearchService } from '../services/searchService';
import { usePlaybackStore } from '../../playback/stores/usePlaybackStore';
import { useLibraryStore } from '../../library/stores/useLibraryStore';
import { useDownloadStore } from '../../library/stores/useDownloadStore';
import type { Playlist, Track } from '../models/search';
import { useI18n } from 'vue-i18n';
import { formatDuration } from '../utils/time';
import { getImageUrl } from '../utils/image';
import LoadingSpinner from '../components/LoadingSpinner.vue';
import AddToPlaylistModal from '../../library/components/AddToPlaylistModal.vue';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const playbackStore = usePlaybackStore();
const libraryStore = useLibraryStore();
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
          class="flex items-center gap-2 px-6 py-3 bg-white/5 hover:bg-white/10 rounded-full border border-white/10 transition-all font-bold text-sm"
          :disabled="!!downloadStore.batchProgress"
        >
          <template v-if="downloadStore.batchProgress">
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
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="text-textGray text-xs uppercase tracking-widest border-b border-white/5">
              <th class="py-3 font-medium w-12 text-center">#</th>
              <th class="py-3 font-medium">{{ t('search.track_title') }}</th>
              <th class="py-3 font-medium hidden md:table-cell">{{ t('search.categories.albums') }}</th>
              <th class="py-3 font-medium w-20 text-right pr-4">
                <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 ml-auto" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="(track, index) in playlist.tracks" 
              :key="track.ids.deezer"
              @click="playTrack(track)"
              class="group hover:bg-white/5 transition-colors cursor-pointer rounded-md"
              :class="{ 'bg-white/5 text-primary': playbackStore.currentTrack?.ids.deezer === track.ids.deezer }"
            >
              <td class="py-3 text-sm text-textGray text-center tabular-nums group-hover:text-white" :class="{ 'text-primary font-bold': playbackStore.currentTrack?.ids.deezer === track.ids.deezer }">
                <span v-if="playbackStore.currentTrack?.ids.deezer === track.ids.deezer && playbackStore.isPlaying">
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 mx-auto animate-pulse fill-current" viewBox="0 0 24 24"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
                </span>
                <span v-else>{{ index + 1 }}</span>
              </td>
              <td class="py-3">
                <div class="flex items-center gap-4">
                  <img :src="getImageUrl(track.album.images)" class="w-10 h-10 object-cover rounded shadow-lg" />
                  <div class="flex flex-col">
                    <span class="text-sm font-medium group-hover:text-primary transition-colors flex items-center gap-2" :class="{ 'text-primary': playbackStore.currentTrack?.ids.deezer === track.ids.deezer }">
                      {{ track.title }}
                      <span v-if="track.explicit" class="text-[10px] bg-white/10 text-textGray px-1 rounded uppercase font-bold">E</span>
                    </span>
                    <span class="text-xs text-textGray hover:underline" @click.stop="router.push(`/artist/${track.artists[0].ids.deezer}`)">
                      {{ track.artists.map(a => a.name).join(', ') }}
                    </span>
                  </div>
                </div>
              </td>
              <td class="py-3 text-sm text-textGray hidden md:table-cell">
                <span class="hover:underline truncate block max-w-[200px]" @click.stop="router.push(`/album/${track.album.ids.deezer}`)">
                  {{ track.album.title }}
                </span>
              </td>
              <td class="py-3 pr-4">
                <div class="flex items-center justify-end gap-3">
                  <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity" :class="{ 'opacity-100': downloadStore.isDownloaded(track.ids.deezer) || downloadStore.isDownloading(track.ids.deezer) }">
                    <!-- Download Status / Action -->
                    <button 
                      v-if="!downloadStore.isDownloaded(track.ids.deezer)"
                      @click.stop="downloadStore.downloadTrack(track.ids.deezer!)" 
                      class="p-1.5 hover:bg-white/10 text-textGray hover:text-white rounded-full transition-colors"
                      :disabled="downloadStore.isDownloading(track.ids.deezer)"
                      :title="t('playback.download')"
                    >
                      <div v-if="downloadStore.isDownloading(track.ids.deezer)" class="w-4 h-4 border-2 border-primary/20 border-t-primary rounded-full animate-spin"></div>
                      <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    </button>
                    <div v-else class="p-1.5 text-primary" :title="t('playback.downloaded')">
                      <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                    </div>

                    <!-- Add to Queue -->
                    <button 
                      @click.stop="playbackStore.addToQueue(track)" 
                      class="p-1.5 hover:bg-white/10 text-textGray hover:text-white rounded-full transition-colors"
                      :title="t('playback.add_to_queue')"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12h18"/><path d="M3 6h18"/><path d="M3 18h18"/><path d="m13 18 2 2 4-4"/></svg>
                    </button>

                    <button 
                      @click.stop="libraryStore.toggleFavorite(track)" 
                      class="p-1.5 hover:bg-white/10 rounded-full transition-colors"
                      :class="libraryStore.isTrackFavorite(track.ids.deezer) ? 'text-primary' : 'text-textGray hover:text-white'"
                    >
                      <svg v-if="libraryStore.isTrackFavorite(track.ids.deezer)" xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 fill-current" viewBox="0 0 24 24"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>
                      <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>
                    </button>
                    <button @click.stop="openPlaylistModal(track)" class="p-1.5 hover:bg-white/10 text-textGray hover:text-white rounded-full transition-colors">
                      <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
                    </button>
                  </div>
                  <span class="text-sm text-textGray tabular-nums w-10 text-right">{{ formatDuration(track.duration_ms) }}</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <AddToPlaylistModal :is-open="isPlaylistModalOpen" :track="selectedTrack" @close="isPlaylistModalOpen = false" />
  </div>
</template>
