<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useLibraryStore } from '../stores/useLibraryStore'; 
import { usePlaybackStore } from '../../playback/stores/usePlaybackStore';
import type { Track } from '../../search/models/search';
import { useI18n } from 'vue-i18n';
import { formatDuration } from '../../search/utils/time';  
import { getImageUrl } from '../../search/utils/image';
import { getRelativeTime } from '../../../utils/date';
import LoadingSpinner from '../../search/components/LoadingSpinner.vue';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const libraryStore = useLibraryStore();
const playbackStore = usePlaybackStore();

const playlistId = Number(route.params.id);
const tracks = ref<Track[]>([]);
const isLoading = ref(true);

const playlist = computed(() => libraryStore.playlists.find(p => p.id === playlistId));

const loadTracks = async () => {
  isLoading.value = true;
  tracks.value = await libraryStore.getPlaylistTracks(playlistId);
  isLoading.value = false;
};

onMounted(() => {
  loadTracks();
});

const playTrack = (track: Track) => {
  playbackStore.playTrack(track, { type: 'playlist', items: tracks.value });
};

const playAll = () => {
  if (tracks.value.length > 0) {
    playTrack(tracks.value[0]);
  }
};

const removeFromPlaylist = async (trackId: string) => {
  await libraryStore.removeTrackFromPlaylist(playlistId, trackId);
  tracks.value = tracks.value.filter(t => t.ids.deezer !== trackId);
};
</script>

<template>
  <div class="h-full flex flex-col bg-background">
    <LoadingSpinner v-if="isLoading" size="lg" />

    <div v-else-if="playlist" class="flex-1 flex flex-col overflow-y-auto custom-scrollbar">
      <!-- Hero Header -->
      <div class="relative h-80 flex items-end p-8 gap-8 overflow-hidden bg-surface/30 flex-shrink-0">
        <div class="w-52 h-52 shadow-2xl rounded-lg z-10 relative bg-white/5 flex items-center justify-center flex-shrink-0">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-24 h-24 text-white/20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15V6"/><path d="M18.5 18a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z"/><path d="M12 12H3"/><path d="M16 6H3"/><path d="M12 18H3"/></svg>
        </div>
        
        <div class="flex-1 z-10 relative mb-2">
          <span class="text-xs font-bold uppercase tracking-widest text-primary mb-2 block">Playlist</span>
          <h1 class="text-5xl font-black mb-4 tracking-tighter">{{ playlist.name }}</h1>
          <p v-if="playlist.description" class="text-sm text-textGray mb-4">{{ playlist.description }}</p>
          <div class="flex items-center gap-2 text-sm font-medium">
            <span class="text-textGray">{{ t('search.track_count', tracks.length) }}</span>
          </div>
        </div>
      </div>

      <!-- Controls Row -->
      <div class="p-8 flex items-center gap-6 flex-shrink-0">
        <button 
          @click="playAll"
          class="w-14 h-14 bg-primary rounded-full flex items-center justify-center shadow-lg hover:scale-105 active:scale-95 transition-all group"
          :class="{ 'opacity-50 cursor-not-allowed': tracks.length === 0 }"
          :disabled="tracks.length === 0"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-7 h-7 text-black fill-current ml-1" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
        </button>
      </div>

      <!-- Tracks Table -->
      <div class="px-8 pb-12 flex-1 flex flex-col">
        <div v-if="tracks.length === 0" class="flex-1 flex flex-col items-center justify-center text-center text-textGray">
          <p>Esta playlist está vacía. Añade canciones desde la búsqueda.</p>
        </div>
        
        <table v-else class="w-full text-left border-collapse">
          <thead>
            <tr class="text-textGray text-xs uppercase tracking-widest border-b border-white/5">
              <th class="py-3 font-medium w-12 text-center">#</th>
              <th class="py-3 font-medium">{{ t('search.track_title') }}</th>
              <th class="py-3 font-medium hidden md:table-cell">{{ t('library.added_at') }}</th>
              <th class="py-3 font-medium w-32 text-right pr-4">
                <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 ml-auto" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="(track, index) in tracks" 
              :key="track.ids.deezer"
              @click="playTrack(track)"
              class="group hover:bg-white/5 transition-colors cursor-pointer rounded-md"
              :class="{ 'bg-white/5 text-primary': playbackStore.currentTrack?.ids.deezer === track.ids.deezer }"
            >
              <td class="py-3 text-sm text-textGray text-center tabular-nums group-hover:text-white" :class="{ 'text-primary': playbackStore.currentTrack?.ids.deezer === track.ids.deezer }">
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
                {{ track.added_at ? getRelativeTime(track.added_at, t) : '-' }}
              </td>
              <td class="py-3 pr-4">
                <div class="flex items-center justify-end gap-3">
                  <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button 
                      @click.stop="libraryStore.toggleFavorite(track)" 
                      class="p-1.5 hover:bg-white/10 rounded-full transition-colors"
                      :class="libraryStore.isTrackFavorite(track.ids.deezer) ? 'text-primary' : 'text-textGray hover:text-white'"
                    >
                      <svg v-if="libraryStore.isTrackFavorite(track.ids.deezer)" xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 fill-current" viewBox="0 0 24 24"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>
                      <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>
                    </button>
                    <!-- Remove from Playlist Button -->
                    <button 
                      @click.stop="removeFromPlaylist(track.ids.deezer!)" 
                      class="p-1.5 hover:bg-red-500/20 text-textGray hover:text-red-500 rounded-full transition-colors"
                      :title="t('library.remove_from_playlist')"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
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
  </div>
</template>
