<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { SearchService } from '../services/searchService';
import { usePlaybackStore } from '../../playback/stores/usePlaybackStore';
import type { Playlist, Track } from '../models/search';
import { useI18n } from 'vue-i18n';
import { formatDuration } from '../utils/time';
import { getImageUrl } from '../utils/image';
import LoadingSpinner from '../components/LoadingSpinner.vue';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const playbackStore = usePlaybackStore();
const playlist = ref<Playlist | null>(null);
const isLoading = ref(true);

const playTrack = (track: Track) => {
  if (!playlist.value) return;
  playbackStore.playTrack(track, { type: 'playlist', items: playlist.value.tracks });
};

const playPlaylist = () => {
  if (playlist.value && playlist.value.tracks.length > 0) {
    playTrack(playlist.value.tracks[0]);
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
            <span class="text-textGray">{{ playlist.nb_tracks }} {{ t('search.track_count', playlist.nb_tracks) }}</span>
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
              <td class="py-3 text-sm text-textGray text-right tabular-nums pr-4">
                {{ formatDuration(track.duration_ms) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
