<script setup lang="ts">
import { ref, computed } from 'vue';
import { useDownloadStore } from '../stores/useDownloadStore';
import { usePlaybackStore } from '../../playback/stores/usePlaybackStore';
import { useI18n } from 'vue-i18n';
import type { Track } from '../../search/models/search';
import { getImageUrl } from '../../search/utils/image';
import TrackList from '../../../components/TrackList.vue';

const downloadStore = useDownloadStore();
const playbackStore = usePlaybackStore();
const { t } = useI18n();

const subTab = ref<'tracks' | 'albums' | 'artists'>('tracks');
const searchQuery = ref('');
const sortBy = ref<'added_at' | 'title' | 'artist' | 'duration'>('added_at');
const sortOrder = ref<'asc' | 'desc'>('desc');

// Drill-down state
const selectedAlbumId = ref<string | null>(null);
const selectedArtistId = ref<string | null>(null);

// --- Data Derivation ---

const downloadedTracks = computed(() => downloadStore.downloadedTracks);

const downloadedAlbums = computed(() => {
  const albumsMap = new Map<string, any>();
  downloadedTracks.value.forEach(track => {
    if (!track.album.ids.deezer) return;
    if (!albumsMap.has(track.album.ids.deezer)) {
      albumsMap.set(track.album.ids.deezer, {
        ...track.album,
        tracks_count: 1,
        added_at: track.added_at
      });
    } else {
      albumsMap.get(track.album.ids.deezer).tracks_count++;
    }
  });
  return Array.from(albumsMap.values());
});

const downloadedArtists = computed(() => {
  const artistsMap = new Map<string, any>();
  downloadedTracks.value.forEach(track => {
    track.artists.forEach(artist => {
      if (!artist.ids.deezer) return;
      if (!artistsMap.has(artist.ids.deezer)) {
        artistsMap.set(artist.ids.deezer, {
          ...artist,
          images: track.album.images,
          tracks_count: 1,
          added_at: track.added_at
        });
      } else {
        artistsMap.get(artist.ids.deezer).tracks_count++;
      }
    });
  });
  return Array.from(artistsMap.values());
});

// --- Filtering & Sorting ---

const filteredTracks = computed(() => {
  let items = [...downloadedTracks.value];
  
  if (selectedAlbumId.value) {
    items = items.filter(t => t.album.ids.deezer === selectedAlbumId.value);
  } else if (selectedArtistId.value) {
    items = items.filter(t => t.artists.some(a => a.ids.deezer === selectedArtistId.value));
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase();
    items = items.filter(t => 
      t.title.toLowerCase().includes(q) || 
      t.artists.some(a => a.name.toLowerCase().includes(q))
    );
  }

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

const filteredAlbums = computed(() => {
  let items = [...downloadedAlbums.value];
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase();
    items = items.filter(a => a.title.toLowerCase().includes(q));
  }
  return items;
});

const filteredArtists = computed(() => {
  let items = [...downloadedArtists.value];
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase();
    items = items.filter(a => a.name.toLowerCase().includes(q));
  }
  return items;
});

// --- Info for Drill-down View ---
const selectedAlbum = computed(() => downloadedAlbums.value.find(a => a.ids.deezer === selectedAlbumId.value));
const selectedArtist = computed(() => downloadedArtists.value.find(a => a.ids.deezer === selectedArtistId.value));

// --- Actions ---

const playDownloaded = (track: Track) => {
  playbackStore.playTrack(track, { type: 'playlist', items: filteredTracks.value });
};

const playAllDownloads = () => {
  if (filteredTracks.value.length > 0) {
    playDownloaded(filteredTracks.value[0]);
  }
};

const toggleSort = (key: string) => {
  const sortKey = key as any;
  if (sortBy.value === sortKey) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortBy.value = sortKey;
    sortOrder.value = 'desc';
  }
};

const selectAlbum = (id: string) => {
  selectedAlbumId.value = id;
  searchQuery.value = '';
};

const selectArtist = (id: string) => {
  selectedArtistId.value = id;
  searchQuery.value = '';
};

const goBack = () => {
  selectedAlbumId.value = null;
  selectedArtistId.value = null;
};

const setSubTab = (tab: 'tracks' | 'albums' | 'artists') => {
  subTab.value = tab;
  goBack();
};
</script>

<template>
  <div class="flex-1 flex flex-col space-y-6">
    <div v-if="downloadStore.downloadedTracks.length === 0" class="flex-1 flex flex-col items-center justify-center opacity-50">
      <svg xmlns="http://www.w3.org/2000/svg" class="w-16 h-16 mb-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
      <p>{{ t('library.downloads_empty', 'No tienes canciones descargadas.') }}</p>
    </div>
    
    <div v-else class="flex flex-col flex-1">
      <!-- Sub-tabs (Hidden during drill-down) -->
      <div v-if="!selectedAlbumId && !selectedArtistId" class="flex items-center gap-2 bg-white/5 p-1 rounded-xl w-fit mb-8">
        <button 
          v-for="tab in (['tracks', 'albums', 'artists'] as const)"
          :key="tab"
          @click="setSubTab(tab)"
          class="px-6 py-2 rounded-lg text-sm font-bold transition-all"
          :class="subTab === tab ? 'bg-primary text-black shadow-lg' : 'text-textGray hover:text-white'"
        >
          {{ t(`search.categories.${tab}`) }}
        </button>
      </div>

      <!-- Drill-down Header -->
      <div v-else class="flex items-center gap-4 mb-8 bg-white/5 p-4 rounded-2xl border border-white/5">
        <button 
          @click="goBack"
          class="p-3 hover:bg-white/10 rounded-full transition-colors text-textGray hover:text-white"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <div class="flex items-center gap-4 flex-1">
          <img 
            :src="getImageUrl(selectedAlbum ? selectedAlbum.images : (selectedArtist ? selectedArtist.images : []))" 
            class="w-16 h-16 rounded-lg object-cover shadow-2xl border border-white/10"
            :class="{ 'rounded-full': selectedArtistId }"
          />
          <div>
            <h2 class="text-2xl font-bold text-white">{{ selectedAlbum ? selectedAlbum.title : selectedArtist?.name }}</h2>
            <p class="text-sm text-textGray">{{ t('search.track_count', filteredTracks.length) }}</p>
          </div>
        </div>
      </div>

      <!-- Tools: Always visible if items exist, unless in Albums/Artists grid -->
      <div v-if="subTab === 'tracks' || selectedAlbumId || selectedArtistId" class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
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

      <!-- Search for Albums/Artists Grid -->
      <div v-else class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div class="relative group max-w-md w-full md:w-80">
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

      <!-- Tab Content -->
      <div class="flex-1 min-h-0">
        <!-- Tracks View (also used for Drill-down) -->
        <div v-if="subTab === 'tracks' || selectedAlbumId || selectedArtistId">
          <TrackList 
            :tracks="filteredTracks"
            :show-added-at="true"
            :show-download-action="false"
            @play="playDownloaded"
            @toggle-sort="toggleSort"
          />
        </div>

        <!-- Albums View -->
        <div v-else-if="subTab === 'albums'" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
          <div 
            v-for="album in filteredAlbums" 
            :key="album.ids.deezer"
            @click="selectAlbum(album.ids.deezer)"
            class="group bg-surface/30 p-4 rounded-xl border border-white/5 hover:bg-surface/60 transition-all hover:translate-y-[-4px] cursor-pointer"
          >
            <div class="aspect-square mb-4 shadow-2xl relative overflow-hidden rounded-lg">
              <img :src="getImageUrl(album.images)" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" />
              <div class="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <div class="w-12 h-12 bg-primary rounded-full flex items-center justify-center shadow-lg transform translate-y-4 group-hover:translate-y-0 transition-transform">
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-black fill-current ml-1" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                </div>
              </div>
            </div>
            <h3 class="font-bold text-sm truncate mb-1 text-white">{{ album.title }}</h3>
            <p class="text-xs text-textGray truncate">{{ t('search.track_count', album.tracks_count) }}</p>
          </div>
        </div>

        <!-- Artists View -->
        <div v-else-if="subTab === 'artists'" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
          <div 
            v-for="artist in filteredArtists" 
            :key="artist.ids.deezer"
            @click="selectArtist(artist.ids.deezer)"
            class="group bg-surface/30 p-4 rounded-xl border border-white/5 hover:bg-surface/60 transition-all hover:translate-y-[-4px] cursor-pointer text-center"
          >
            <div class="aspect-square mb-4 shadow-2xl relative overflow-hidden rounded-full border-4 border-white/5 mx-auto w-3/4">
              <img :src="getImageUrl(artist.images)" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" />
            </div>
            <h3 class="font-bold text-sm truncate mb-1 text-white">{{ artist.name }}</h3>
            <p class="text-xs text-textGray truncate">{{ t('search.track_count', artist.tracks_count) }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
