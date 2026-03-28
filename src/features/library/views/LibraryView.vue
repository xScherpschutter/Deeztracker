<script setup lang="ts">
import { ref, computed } from 'vue';
import { useLibraryStore } from '../stores/useLibraryStore';
import { useDownloadStore } from '../stores/useDownloadStore';
import { usePlaybackStore } from '../../playback/stores/usePlaybackStore';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { formatDuration } from '../../search/utils/time';
import { getImageUrl } from '../../search/utils/image';
import { getRelativeTime } from '../../../utils/date';
import { handleDragStart } from '../../../utils/drag';
import type { Track } from '../../search/models/search';
import ConfirmModal from '../../../components/ConfirmModal.vue';
import PlaylistCover from '../components/PlaylistCover.vue';

const libraryStore = useLibraryStore();
const downloadStore = useDownloadStore();
const playbackStore = usePlaybackStore();
const router = useRouter();
const { t } = useI18n();

const activeTab = ref<'favorites' | 'playlists' | 'downloads'>('favorites');
const isCreatingPlaylist = ref(false);
const newPlaylistName = ref('');
const newPlaylistDesc = ref('');

const showDeleteModal = ref(false);
const playlistToDelete = ref<number | null>(null);

// Search and Sort State
const searchQuery = ref('');
const sortBy = ref<'added_at' | 'title' | 'artist' | 'duration'>('added_at');
const sortOrder = ref<'asc' | 'desc'>('desc');

const filteredFavorites = computed(() => {
  let items = [...libraryStore.favorites];

  // Filter
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase();
    items = items.filter(t => 
      t.title.toLowerCase().includes(q) || 
      t.artists.some(a => a.name.toLowerCase().includes(q))
    );
  }

  // Sort
  items.sort((a, b) => {
    let comparison = 0;
    switch (sortBy.value) {
      case 'added_at':
        const timeA = a.added_at ? new Date(a.added_at).getTime() : 0;
        const timeB = b.added_at ? new Date(b.added_at).getTime() : 0;
        comparison = timeA - timeB;
        break;
      case 'title':
        comparison = a.title.localeCompare(b.title);
        break;
      case 'artist':
        comparison = (a.artists[0]?.name || '').localeCompare(b.artists[0]?.name || '');
        break;
      case 'duration':
        comparison = (a.duration_ms || 0) - (b.duration_ms || 0);
        break;
    }
    return sortOrder.value === 'asc' ? comparison : -comparison;
  });

  return items;
});

const filteredDownloads = computed(() => {
  let items = [...downloadStore.downloadedTracks];

  // Filter
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase();
    items = items.filter(t => 
      t.title.toLowerCase().includes(q) || 
      t.artists.some(a => a.name.toLowerCase().includes(q))
    );
  }

  // Sort
  items.sort((a, b) => {
    let comparison = 0;
    switch (sortBy.value) {
      case 'added_at':
        const timeA = a.added_at ? new Date(a.added_at).getTime() : 0;
        const timeB = b.added_at ? new Date(b.added_at).getTime() : 0;
        comparison = timeA - timeB;
        break;
      case 'title':
        comparison = a.title.localeCompare(b.title);
        break;
      case 'artist':
        comparison = (a.artists[0]?.name || '').localeCompare(b.artists[0]?.name || '');
        break;
      case 'duration':
        comparison = (a.duration_ms || 0) - (b.duration_ms || 0);
        break;
    }
    return sortOrder.value === 'asc' ? comparison : -comparison;
  });

  return items;
});

const playFavorite = (track: Track) => {
  playbackStore.playTrack(track, { type: 'playlist', items: filteredFavorites.value });
};

const playDownloaded = (track: Track) => {
  playbackStore.playTrack(track, { type: 'playlist', items: filteredDownloads.value });
};

const playAllFavorites = () => {
  if (filteredFavorites.value.length > 0) {
    playFavorite(filteredFavorites.value[0]);
  }
};

const playAllDownloads = () => {
  if (filteredDownloads.value.length > 0) {
    playDownloaded(filteredDownloads.value[0]);
  }
};

const toggleSort = (key: typeof sortBy.value) => {
  if (sortBy.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortBy.value = key;
    sortOrder.value = 'desc';
  }
};

const handleCreatePlaylist = async () => {
  if (!newPlaylistName.value.trim()) return;
  await libraryStore.createPlaylist(newPlaylistName.value, newPlaylistDesc.value);
  newPlaylistName.value = '';
  newPlaylistDesc.value = '';
  isCreatingPlaylist.value = false;
};

const requestDeletePlaylist = (id: number) => {
  playlistToDelete.value = id;
  showDeleteModal.value = true;
};

const executeDeletePlaylist = async () => {
  if (playlistToDelete.value !== null) {
    await libraryStore.deletePlaylist(playlistToDelete.value);
    playlistToDelete.value = null;
    showDeleteModal.value = false;
  }
};

const cancelDeletePlaylist = () => {
  playlistToDelete.value = null;
  showDeleteModal.value = false;
};

const setTab = (tab: 'favorites' | 'playlists' | 'downloads') => {
  activeTab.value = tab;
  if (tab === 'downloads') {
    downloadStore.checkIntegrity();
  }
};
</script>

<template>
  <div class="h-full flex flex-col bg-background text-white p-8 overflow-hidden">
    <h1 class="text-4xl font-black mb-8">{{ t('library.title') }}</h1>

    <!-- Tabs -->
    <div class="flex items-center gap-6 mb-8 border-b border-white/10">
      <button 
        @click="setTab('favorites')"
        class="pb-4 font-bold text-lg transition-colors border-b-2"
        :class="activeTab === 'favorites' ? 'text-white border-primary' : 'text-textGray border-transparent hover:text-white'"
      >
        {{ t('library.favorites') }}
      </button>
      <button 
        @click="setTab('playlists')"
        class="pb-4 font-bold text-lg transition-colors border-b-2"
        :class="activeTab === 'playlists' ? 'text-white border-primary' : 'text-textGray border-transparent hover:text-white'"
      >
        {{ t('library.playlists') }}
      </button>
      <button 
        @click="setTab('downloads')"
        class="pb-4 font-bold text-lg transition-colors border-b-2"
        :class="activeTab === 'downloads' ? 'text-white border-primary' : 'text-textGray border-transparent hover:text-white'"
      >
        {{ t('library.downloads') }}
      </button>
    </div>

    <!-- Tab Content -->
    <div class="flex-1 overflow-y-auto custom-scrollbar pr-4 flex flex-col">
      
      <!-- Favorites Tab -->
      <div v-if="activeTab === 'favorites'" class="flex-1 flex flex-col space-y-6">
        <div v-if="libraryStore.favorites.length === 0" class="flex-1 flex flex-col items-center justify-center opacity-50">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-16 h-16 mb-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>
          <p>{{ t('library.no_favorites') }}</p>
        </div>
        
        <div v-else class="flex flex-col flex-1">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
            <div class="flex items-center gap-4">
              <button 
                @click="playAllFavorites"
                class="w-12 h-12 bg-primary rounded-full flex items-center justify-center shadow-lg hover:scale-105 active:scale-95 transition-all flex-shrink-0"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-black fill-current ml-1" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
              </button>
              
              <div class="relative group max-w-md w-64 md:w-80">
                <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-textGray group-focus-within:text-primary transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                </div>
                <input 
                  v-model="searchQuery"
                  type="text" 
                  :placeholder="t('search.placeholder')"
                  class="w-full bg-white/5 border border-white/10 rounded-full py-3 pl-12 pr-6 text-sm focus:outline-none focus:border-primary/40 focus:bg-white/10 transition-all shadow-inner"
                />
              </div>
            </div>

            <div class="flex items-center gap-4 text-xs text-textGray bg-white/5 p-1 rounded-full border border-white/5">
              <button 
                @click="toggleSort('added_at')" 
                class="hover:text-white transition-all px-4 py-1.5 rounded-full"
                :class="{ 'bg-white/10 text-primary shadow-sm': sortBy === 'added_at' }"
              >
                {{ t('library.added_at') }}
                <span v-if="sortBy === 'added_at'" class="ml-1">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
              </button>
              <button 
                @click="toggleSort('title')" 
                class="hover:text-white transition-all px-4 py-1.5 rounded-full"
                :class="{ 'bg-white/10 text-primary shadow-sm': sortBy === 'title' }"
              >
                {{ t('search.track_title') }}
                <span v-if="sortBy === 'title'" class="ml-1">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
              </button>
            </div>
          </div>
          
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="text-textGray text-xs uppercase tracking-widest border-b border-white/5">
                <th class="py-3 font-medium w-12 text-center">#</th>
                <th class="py-3 font-medium cursor-pointer hover:text-white transition-colors" @click="toggleSort('title')">
                  {{ t('search.track_title') }}
                  <span v-if="sortBy === 'title'">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
                </th>
                <th class="py-3 font-medium hidden md:table-cell">{{ t('search.categories.albums') }}</th>
                <th class="py-3 font-medium hidden lg:table-cell cursor-pointer hover:text-white transition-colors" @click="toggleSort('added_at')">
                  {{ t('library.added_at') }}
                  <span v-if="sortBy === 'added_at'">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
                </th>
                <th class="py-3 font-medium w-20 text-right pr-4">
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 ml-auto" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="(track, index) in filteredFavorites" 
                :key="track.ids.deezer"
                @click="playFavorite(track)"
                draggable="true"
                @dragstart="handleDragStart($event, track)"
                class="group hover:bg-white/5 transition-colors cursor-pointer rounded-md list-item-optimized"
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
                    <div class="flex flex-col min-w-0">
                      <h3 class="font-medium text-sm truncate group-hover:text-primary transition-colors" :class="{ 'text-primary': playbackStore.currentTrack?.ids.deezer === track.ids.deezer }">{{ track.title }}</h3>
                      <p class="text-xs text-textGray truncate hover:underline" @click.stop="router.push(`/artist/${track.artists[0]?.ids.deezer}`)">
                        {{ track.artists.map(a => a.name).join(', ') }}
                      </p>
                    </div>
                  </div>
                </td>
                <td class="py-3 text-sm text-textGray hidden md:table-cell">
                  <span class="hover:underline truncate block max-w-[200px]" @click.stop="router.push(`/album/${track.album.ids.deezer}`)">
                    {{ track.album.title }}
                  </span>
                </td>
                <td class="py-3 text-sm text-textGray hidden lg:table-cell">
                  {{ track.added_at ? getRelativeTime(track.added_at, t) : '-' }}
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
                        class="p-1.5 hover:bg-white/10 rounded-full transition-all text-primary"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 fill-current" viewBox="0 0 24 24"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>
                      </button>
                    </div>
                    <span class="text-xs text-textGray font-mono tabular-nums w-10 text-right">{{ formatDuration(track.duration_ms) }}</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Downloads Tab -->
      <div v-else-if="activeTab === 'downloads'" class="flex-1 flex flex-col space-y-6">
        <div v-if="downloadStore.downloadedTracks.length === 0" class="flex-1 flex flex-col items-center justify-center opacity-50">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-16 h-16 mb-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          <p>No tienes canciones descargadas.</p>
        </div>
        
        <div v-else class="flex flex-col flex-1">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
            <div class="flex items-center gap-4">
              <button 
                @click="playAllDownloads"
                class="w-12 h-12 bg-primary rounded-full flex items-center justify-center shadow-lg hover:scale-105 active:scale-95 transition-all flex-shrink-0"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-black fill-current ml-1" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
              </button>
              
              <div class="relative group max-w-md w-64 md:w-80">
                <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-textGray group-focus-within:text-primary transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                </div>
                <input 
                  v-model="searchQuery"
                  type="text" 
                  :placeholder="t('search.placeholder')"
                  class="w-full bg-white/5 border border-white/10 rounded-full py-3 pl-12 pr-6 text-sm focus:outline-none focus:border-primary/40 focus:bg-white/10 transition-all shadow-inner"
                />
              </div>
            </div>

            <div class="flex items-center gap-4 text-xs text-textGray bg-white/5 p-1 rounded-full border border-white/5">
              <button 
                @click="toggleSort('added_at')" 
                class="hover:text-white transition-all px-4 py-1.5 rounded-full"
                :class="{ 'bg-white/10 text-primary shadow-sm': sortBy === 'added_at' }"
              >
                {{ t('library.added_at') }}
                <span v-if="sortBy === 'added_at'" class="ml-1">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
              </button>
              <button 
                @click="toggleSort('title')" 
                class="hover:text-white transition-all px-4 py-1.5 rounded-full"
                :class="{ 'bg-white/10 text-primary shadow-sm': sortBy === 'title' }"
              >
                {{ t('search.track_title') }}
                <span v-if="sortBy === 'title'" class="ml-1">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
              </button>
            </div>
          </div>
          
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="text-textGray text-xs uppercase tracking-widest border-b border-white/5">
                <th class="py-3 font-medium w-12 text-center">#</th>
                <th class="py-3 font-medium cursor-pointer hover:text-white transition-colors" @click="toggleSort('title')">
                  {{ t('search.track_title') }}
                  <span v-if="sortBy === 'title'">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
                </th>
                <th class="py-3 font-medium hidden md:table-cell">{{ t('search.categories.albums') }}</th>
                <th class="py-3 font-medium hidden lg:table-cell cursor-pointer hover:text-white transition-colors" @click="toggleSort('added_at')">
                  {{ t('library.added_at') }}
                  <span v-if="sortBy === 'added_at'">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
                </th>
                <th class="py-3 font-medium w-20 text-right pr-4">
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 ml-auto" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="(track, index) in filteredDownloads" 
                :key="track.ids.deezer"
                @click="playDownloaded(track)"
                draggable="true"
                @dragstart="handleDragStart($event, track)"
                class="group hover:bg-white/5 transition-colors cursor-pointer rounded-md list-item-optimized"
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
                    <div class="flex flex-col min-w-0">
                      <h3 class="font-medium text-sm truncate group-hover:text-primary transition-colors" :class="{ 'text-primary': playbackStore.currentTrack?.ids.deezer === track.ids.deezer }">{{ track.title }}</h3>
                      <p class="text-xs text-textGray truncate hover:underline" @click.stop="router.push(`/artist/${track.artists[0]?.ids.deezer}`)">
                        {{ track.artists.map(a => a.name).join(', ') }}
                      </p>
                    </div>
                  </div>
                </td>
                <td class="py-3 text-sm text-textGray hidden md:table-cell">
                  <span class="hover:underline truncate block max-w-[200px]" @click.stop="router.push(`/album/${track.album.ids.deezer}`)">
                    {{ track.album.title }}
                  </span>
                </td>
                <td class="py-3 text-sm text-textGray hidden lg:table-cell">
                  {{ track.added_at ? getRelativeTime(track.added_at, t) : '-' }}
                </td>
                <td class="py-3 pr-4">
                  <div class="flex items-center justify-end gap-3">
                    <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
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
                    </div>
                    <span class="text-xs text-textGray font-mono tabular-nums w-10 text-right">{{ formatDuration(track.duration_ms) }}</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Playlists Tab -->
      <div v-else-if="activeTab === 'playlists'" class="flex-1 flex flex-col space-y-6">
        
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-xl font-bold">{{ t('library.playlists') }}</h2>
          <button 
            @click="isCreatingPlaylist = true"
            class="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-full text-sm font-bold transition-colors flex items-center gap-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
            {{ t('library.create_playlist') }}
          </button>
        </div>

        <!-- Create Playlist Modal -->
        <Teleport to="body">
          <div v-if="isCreatingPlaylist" class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
            <div class="bg-surface border border-white/10 w-full max-w-md rounded-2xl shadow-2xl overflow-hidden scale-in">
              <div class="p-8 space-y-6">
                <h2 class="text-2xl font-bold">{{ t('library.create_playlist') }}</h2>
                
                <div class="space-y-4">
                  <div class="space-y-2">
                    <label class="text-xs font-bold text-textGray uppercase tracking-widest">{{ t('library.new_playlist_name') }}</label>
                    <input 
                      v-model="newPlaylistName"
                      type="text" 
                      class="w-full bg-background border border-white/10 rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-primary transition-colors"
                      @keyup.enter="handleCreatePlaylist"
                      autofocus
                    />
                  </div>
                  
                  <div class="space-y-2">
                    <label class="text-xs font-bold text-textGray uppercase tracking-widest">{{ t('library.new_playlist_desc') }}</label>
                    <textarea 
                      v-model="newPlaylistDesc"
                      rows="3"
                      class="w-full bg-background border border-white/10 rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-primary transition-colors resize-none"
                    ></textarea>
                  </div>
                </div>

                <div class="flex justify-end gap-3 pt-2">
                  <button @click="isCreatingPlaylist = false" class="px-6 py-2.5 text-sm font-bold text-textGray hover:text-white transition-colors">{{ t('settings.close') }}</button>
                  <button 
                    @click="handleCreatePlaylist" 
                    class="px-8 py-2.5 bg-primary text-black rounded-full text-sm font-bold hover:scale-105 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed" 
                    :disabled="!newPlaylistName.trim()"
                  >
                    {{ t('library.create_playlist') }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </Teleport>

        <div v-if="libraryStore.playlists.length === 0 && !isCreatingPlaylist" class="flex-1 flex flex-col items-center justify-center opacity-50">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-16 h-16 mb-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15V6"/><path d="M18.5 18a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z"/><path d="M12 12H3"/><path d="M16 6H3"/><path d="M12 18H3"/></svg>
          <p>{{ t('library.no_playlists') }}</p>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
          <div 
            v-for="playlist in libraryStore.playlists" 
            :key="playlist.id"
            @click="router.push(`/library/playlist/${playlist.id}`)"
            class="group bg-surface/30 p-4 rounded-xl border border-white/5 hover:bg-surface/60 transition-all hover:translate-y-[-4px] cursor-pointer relative"
          >
            <button 
              @click.stop="requestDeletePlaylist(playlist.id)"
              class="absolute top-2 right-2 p-1.5 bg-black/60 rounded-full text-textGray hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity z-10"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
            </button>
            <PlaylistCover :covers="playlist.preview_covers" class="mb-4 shadow-2xl" />
            <h3 class="font-bold text-sm truncate mb-1">{{ playlist.name }}</h3>
            <p v-if="playlist.description" class="text-xs text-textGray truncate">{{ playlist.description }}</p>
          </div>
        </div>

      </div>

    </div>

    <!-- Delete Confirmation Modal -->
    <ConfirmModal 
      :is-open="showDeleteModal"
      :title="t('library.delete_playlist_title')"
      :message="t('library.delete_playlist_confirm')"
      :confirm-text="t('library.delete_playlist_btn')"
      :cancel-text="t('settings.close')"
      :is-destructive="true"
      @confirm="executeDeletePlaylist"
      @cancel="cancelDeletePlaylist"
    />
  </div>
</template>

<style scoped>
.list-item-optimized {
  content-visibility: auto;
  contain-intrinsic-size: 0 64px;
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
</style>
