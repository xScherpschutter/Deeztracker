<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { usePlaybackStore } from '../features/playback/stores/usePlaybackStore';
import { useDownloadStore } from '../features/library/stores/useDownloadStore';
import { useLibraryStore } from '../features/library/stores/useLibraryStore';
import type { Track } from '../features/search/models/search';
import { formatDuration } from '../features/search/utils/time';
import { getImageUrl } from '../features/search/utils/image';
import { getRelativeTime } from '../utils/date';
import AddToPlaylistModal from '../features/library/components/AddToPlaylistModal.vue';

const props = withDefaults(defineProps<{
  tracks: Track[];
  showAlbum?: boolean;
  showAddedAt?: boolean;
  showIndex?: boolean;
  playbackContext?: any;
  showRemove?: boolean;
  showHeader?: boolean;
  showAddToPlaylist?: boolean;
  showDownloadAction?: boolean;
}>(), {
  showAlbum: true,
  showAddedAt: false,
  showIndex: true,
  showRemove: false,
  showHeader: true,
  showAddToPlaylist: false,
  showDownloadAction: true
});

const emit = defineEmits<{
  (e: 'play', track: Track): void;
  (e: 'remove', track: Track): void;
  (e: 'toggleSort', key: string): void;
  (e: 'addToPlaylist', track: Track): void;
  (e: 'select', tracks: Track[]): void;
}>();

const { t } = useI18n();
const router = useRouter();
const playbackStore = usePlaybackStore();
const downloadStore = useDownloadStore();
const libraryStore = useLibraryStore();

// Selection State
const selectedIds = ref<Set<string>>(new Set());
const selectedTracks = computed(() => props.tracks.filter(t => selectedIds.value.has(t.ids.deezer!)));

// Long Press Logic
let longPressTimer: number | null = null;
let isLongPress = false;

const startLongPress = (trackId: string) => {
  isLongPress = false;
  if (longPressTimer) clearTimeout(longPressTimer);
  
  longPressTimer = window.setTimeout(() => {
    isLongPress = true;
    if (!selectedIds.value.has(trackId)) {
      toggleSelect(trackId);
    }
  }, 500);
};

const cancelLongPress = () => {
  if (longPressTimer) {
    clearTimeout(longPressTimer);
    longPressTimer = null;
  }
};

const isAllSelected = computed(() => {
  return props.tracks.length > 0 && props.tracks.every(t => selectedIds.value.has(t.ids.deezer!));
});

const isSomeSelected = computed(() => {
  return selectedIds.value.size > 0 && !isAllSelected.value;
});

const toggleSelectAll = () => {
  const newSet = new Set(selectedIds.value);
  if (isAllSelected.value) {
    newSet.clear();
  } else {
    props.tracks.forEach(t => newSet.add(t.ids.deezer!));
  }
  selectedIds.value = newSet;
};

const toggleSelect = (trackId: string) => {
  const newSet = new Set(selectedIds.value);
  if (newSet.has(trackId)) {
    newSet.delete(trackId);
  } else {
    newSet.add(trackId);
  }
  selectedIds.value = newSet;
};

const clearSelection = () => {
  selectedIds.value = new Set();
};

const handleRowClick = (track: Track) => {
  if (isLongPress) {
    isLongPress = false;
    return;
  }

  if (selectedIds.value.size > 0) {
    toggleSelect(track.ids.deezer!);
  }
};

// Batch Actions
const addSelectedToQueue = () => {
  playbackStore.addTracksToQueue(selectedTracks.value);
  clearSelection();
};

const downloadSelected = () => {
  selectedTracks.value.forEach(t => {
    if (t.ids.deezer) downloadStore.downloadTrack(t.ids.deezer);
  });
  clearSelection();
};

const isPlaylistModalOpen = ref(false);
const openBatchPlaylistModal = () => {
  isPlaylistModalOpen.value = true;
};

watch(selectedTracks, (newTracks) => {
  emit('select', newTracks);
});

const playTrack = (track: Track) => {
  emit('play', track);
};

const handleRemove = (track: Track) => {
  emit('remove', track);
};
</script>

<template>
  <div class="relative w-full">
    <table class="w-full text-left border-collapse">
      <thead v-if="showHeader">
        <tr class="text-textGray text-xs uppercase tracking-widest border-b border-white/5">
          <th class="py-3 font-medium w-12 text-center">
            <div class="flex items-center justify-center">
              <input 
                type="checkbox" 
                :checked="isAllSelected"
                :indeterminate="isSomeSelected"
                @change="toggleSelectAll"
                class="w-4 h-4 rounded border-white/20 bg-white/5 text-primary focus:ring-primary focus:ring-offset-0 transition-all cursor-pointer appearance-none checked:bg-primary checked:border-primary relative checked:after:content-['✓'] checked:after:absolute checked:after:text-[10px] checked:after:text-black checked:after:font-bold checked:after:left-0.5 checked:after:top-[-1px] border"
              />
            </div>
          </th>
          <th v-if="showIndex" class="py-3 font-medium w-12 text-center">#</th>
          <th class="py-3 font-medium cursor-pointer hover:text-white transition-colors" @click="emit('toggleSort', 'title')">
            {{ t('search.track_title') }}
          </th>
          <th v-if="showAlbum" class="py-3 font-medium hidden md:table-cell">{{ t('search.categories.albums') }}</th>
          <th v-if="showAddedAt" class="py-3 font-medium hidden lg:table-cell cursor-pointer hover:text-white transition-colors" @click="emit('toggleSort', 'added_at')">
            {{ t('library.added_at') }}
          </th>
          <th class="py-3 font-medium w-32 text-right pr-4">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 ml-auto" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr 
          v-for="(track, index) in tracks" 
          :key="track.ids.deezer"
          class="group hover:bg-white/5 transition-colors rounded-md select-none"
          :class="{ 
            'bg-white/5 text-primary': playbackStore.currentTrack?.ids.deezer === track.ids.deezer,
            'bg-primary/10 hover:bg-primary/20': selectedIds.has(track.ids.deezer!),
            'cursor-pointer': selectedIds.size > 0
          }"
          @click="handleRowClick(track)"
          @mousedown="startLongPress(track.ids.deezer!)"
          @mouseup="cancelLongPress"
          @mouseleave="cancelLongPress"
          @contextmenu.prevent
          @touchstart="startLongPress(track.ids.deezer!)"
          @touchend="cancelLongPress"
        >
          <td class="py-3 text-center" @click.stop>
            <div class="flex items-center justify-center">
              <input 
                type="checkbox" 
                :checked="selectedIds.has(track.ids.deezer!)"
                @change="toggleSelect(track.ids.deezer!)"
                class="w-4 h-4 rounded border-white/20 bg-white/5 text-primary focus:ring-primary focus:ring-offset-0 transition-all cursor-pointer appearance-none checked:bg-primary checked:border-primary relative checked:after:content-['✓'] checked:after:absolute checked:after:text-[10px] checked:after:text-black checked:after:font-bold checked:after:left-0.5 checked:after:top-[-1px] border"
              />
            </div>
          </td>
          <td v-if="showIndex" class="py-3 text-sm text-textGray text-center tabular-nums group-hover:text-white" :class="{ 'text-primary font-bold': playbackStore.currentTrack?.ids.deezer === track.ids.deezer }">
            <span v-if="playbackStore.currentTrack?.ids.deezer === track.ids.deezer && playbackStore.isPlaying">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 mx-auto animate-pulse fill-current" viewBox="0 0 24 24"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
            </span>
            <span v-else>{{ index + 1 }}</span>
          </td>
          <td class="py-3">
            <div class="flex items-center gap-4">
              <div 
                class="relative w-10 h-10 flex-shrink-0 cursor-pointer group/cover"
                @click.stop="playTrack(track)"
              >
                <img :src="getImageUrl(track.album.images)" class="w-full h-full object-cover rounded shadow-lg group-hover/cover:opacity-70 transition-opacity" />
                <div class="absolute inset-0 bg-black/20 opacity-0 group-hover/cover:opacity-100 flex items-center justify-center rounded transition-opacity">
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 fill-current text-white" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                </div>
              </div>
              <div class="flex flex-col min-w-0">
                <span 
                  class="text-sm font-medium group-hover:text-primary transition-colors flex items-center gap-2 truncate hover:underline cursor-pointer w-fit" 
                  :class="{ 'text-primary': playbackStore.currentTrack?.ids.deezer === track.ids.deezer }"
                  @click.stop="playTrack(track)"
                >
                  {{ track.title }}
                  <span v-if="track.explicit" class="text-[10px] bg-white/10 text-textGray px-1 rounded uppercase font-bold">E</span>
                </span>
                <span class="text-xs text-textGray hover:underline cursor-pointer truncate w-fit" @click.stop="router.push(`/artist/${track.artists[0].ids.deezer}`)">
                  {{ track.artists.map(a => a.name).join(', ') }}
                </span>
              </div>
            </div>
          </td>
          <td v-if="showAlbum" class="py-3 text-sm text-textGray hidden md:table-cell">
            <span class="hover:underline truncate block max-w-[200px] cursor-pointer" @click.stop="router.push(`/album/${track.album.ids.deezer}`)">
              {{ track.album.title }}
            </span>
          </td>
          <td v-if="showAddedAt" class="py-3 text-sm text-textGray hidden lg:table-cell">
            {{ track.added_at ? getRelativeTime(track.added_at, t) : '-' }}
          </td>
          <td class="py-3 pr-4" @click.stop>
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

                <!-- Add to Playlist -->
                <button 
                  v-if="showAddToPlaylist"
                  @click.stop="emit('addToPlaylist', track)" 
                  class="p-1.5 hover:bg-white/10 text-textGray hover:text-white rounded-full transition-colors"
                  :title="t('library.add_to_playlist')"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
                </button>

                <!-- Remove Action -->
                <button 
                  v-if="showRemove"
                  @click.stop="handleRemove(track)" 
                  class="p-1.5 hover:bg-red-500/20 text-textGray hover:text-red-500 rounded-full transition-colors"
                  :title="t('library.remove')"
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

    <!-- Selection Floating Toolbar -->
    <Transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="translate-y-20 opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="translate-y-0 opacity-100"
      leave-to-class="translate-y-20 opacity-0"
    >
      <div 
        v-if="selectedIds.size > 0" 
        class="fixed bottom-32 left-1/2 -translate-x-1/2 bg-primary rounded-full px-6 py-3 shadow-2xl flex items-center gap-6 z-[100] text-black"
      >
        <span class="font-bold text-sm">{{ t('library.selected_tracks', { count: selectedIds.size }) }}</span>
        
        <div class="h-6 w-px bg-black/20"></div>
        
        <div class="flex items-center gap-2">
          <button 
            @click="addSelectedToQueue"
            class="p-2 hover:bg-black/10 rounded-full transition-colors"
            :title="t('playback.add_to_queue')"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12h18"/><path d="M3 6h18"/><path d="M3 18h18"/><path d="m13 18 2 2 4-4"/></svg>
          </button>
          
          <button 
            @click="openBatchPlaylistModal"
            class="p-2 hover:bg-black/10 rounded-full transition-colors"
            :title="t('library.add_to_playlist')"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
          </button>
          
          <button 
            v-if="showDownloadAction"
            @click="downloadSelected"
            class="p-2 hover:bg-black/10 rounded-full transition-colors"
            :title="t('playback.download')"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          </button>
        </div>
        
        <div class="h-6 w-px bg-black/20"></div>
        
        <button 
          @click="clearSelection"
          class="text-sm font-bold hover:underline"
        >
          {{ t('playback.clear_queue') }}
        </button>
      </div>
    </Transition>

    <AddToPlaylistModal 
      :is-open="isPlaylistModalOpen" 
      :tracks="selectedTracks" 
      @close="isPlaylistModalOpen = false" 
    />
  </div>
</template>

<style scoped>
input[type="checkbox"]:indeterminate {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='black' stroke-width='4'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M5 12h14' /%3E%3C/svg%3E");
  background-size: 10px;
  background-position: center;
  background-repeat: no-repeat;
  background-color: #3b82f6;
  border-color: #3b82f6;
}
</style>
