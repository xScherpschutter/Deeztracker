<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { SearchService } from '../services/searchService';
import { usePlaybackStore } from '../../playback/stores/usePlaybackStore';
import { useLibraryStore } from '../../library/stores/useLibraryStore';
import { handleDragStart } from "../../../utils/drag";
import type { Album, Track } from '../models/search';
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
const album = ref<Album | null>(null);
const isLoading = ref(true);

const isPlaylistModalOpen = ref(false);
const selectedTrack = ref<Track | null>(null);

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
      </div>

      <!-- Tracks Table -->
      <div class="px-8 pb-12">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="text-textGray text-xs uppercase tracking-widest border-b border-white/5">
              <th class="py-3 font-medium w-12 text-center">#</th>
              <th class="py-3 font-medium">{{ t('search.track_title') }}</th>
              <th class="py-3 font-medium w-20 text-right pr-4">
                <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 ml-auto" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="(track, index) in album.tracks" 
              :key="track.ids.deezer"
              @click="playTrack(track)"
              draggable="true"
              @dragstart="handleDragStart($event, { ...track, album })"
              class="group hover:bg-white/5 transition-colors cursor-pointer rounded-md"
              :class="{ 'bg-white/5 text-primary': playbackStore.currentTrack?.ids.deezer === track.ids.deezer }"
            >
              <td class="py-3 text-sm text-textGray text-center tabular-nums group-hover:text-white" :class="{ 'text-primary': playbackStore.currentTrack?.ids.deezer === track.ids.deezer }">
                {{ index + 1 }}
              </td>
              <td class="py-3">
                <div class="flex flex-col">
                  <span class="text-sm font-medium group-hover:text-primary transition-colors flex items-center gap-2" :class="{ 'text-primary': playbackStore.currentTrack?.ids.deezer === track.ids.deezer }">
                    {{ track.title }}
                    <span v-if="track.explicit" class="text-[10px] bg-white/10 text-textGray px-1 rounded uppercase font-bold">E</span>
                  </span>
                  <span class="text-xs text-textGray">{{ track.artists.map(a => a.name).join(', ') }}</span>
                </div>
              </td>
              <td class="py-3 pr-4">
                <div class="flex items-center justify-end gap-3">
                  <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button 
                      @click.stop="playbackStore.addToQueue({ ...track, album: { ...album } } as unknown as Track)" 
                      class="p-1.5 hover:bg-white/10 text-textGray hover:text-white rounded-full transition-colors"
                      :title="t('playback.add_to_queue')"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12h18"/><path d="M3 6h18"/><path d="M3 18h18"/><path d="m13 18 2 2 4-4"/></svg>
                    </button>
                    <button 
                      @click.stop="libraryStore.toggleFavorite({ ...track, album: { ...album } } as unknown as Track)" 
                      class="p-1 hover:bg-white/10 rounded-full transition-colors"
                      :class="libraryStore.isTrackFavorite(track.ids.deezer) ? 'text-primary' : 'text-textGray hover:text-white'"
                    >
                      <svg v-if="libraryStore.isTrackFavorite(track.ids.deezer)" xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 fill-current" viewBox="0 0 24 24"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>
                      <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>
                    </button>
                    <button @click.stop="openPlaylistModal(track)" class="p-1 hover:bg-white/10 text-textGray hover:text-white rounded-full transition-colors">
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
