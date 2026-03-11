<script setup lang="ts">
import { ref } from 'vue';
import { useLibraryStore } from '../stores/useLibraryStore';
import { usePlaybackStore } from '../../playback/stores/usePlaybackStore';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { formatDuration } from '../../search/utils/time';
import { getImageUrl } from '../../search/utils/image';
import { getRelativeTime } from '../../../utils/date';
import type { Track } from '../../search/models/search';
import ConfirmModal from '../../../components/ConfirmModal.vue';

const libraryStore = useLibraryStore();
const playbackStore = usePlaybackStore();
const router = useRouter();
const { t } = useI18n();

const activeTab = ref<'favorites' | 'playlists'>('favorites');
const isCreatingPlaylist = ref(false);
const newPlaylistName = ref('');
const newPlaylistDesc = ref('');

const showDeleteModal = ref(false);
const playlistToDelete = ref<number | null>(null);

const playFavorite = (track: Track) => {
  playbackStore.playTrack(track, { type: 'playlist', items: libraryStore.favorites });
};

const playAllFavorites = () => {
  if (libraryStore.favorites.length > 0) {
    playFavorite(libraryStore.favorites[0]);
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
</script>

<template>
  <div class="h-full flex flex-col bg-background text-white p-8 overflow-hidden">
    <h1 class="text-4xl font-black mb-8">{{ t('library.title') }}</h1>

    <!-- Tabs -->
    <div class="flex items-center gap-6 mb-8 border-b border-white/10">
      <button 
        @click="activeTab = 'favorites'"
        class="pb-4 font-bold text-lg transition-colors border-b-2"
        :class="activeTab === 'favorites' ? 'text-white border-primary' : 'text-textGray border-transparent hover:text-white'"
      >
        {{ t('library.favorites') }}
      </button>
      <button 
        @click="activeTab = 'playlists'"
        class="pb-4 font-bold text-lg transition-colors border-b-2"
        :class="activeTab === 'playlists' ? 'text-white border-primary' : 'text-textGray border-transparent hover:text-white'"
      >
        {{ t('library.playlists') }}
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
        
        <div v-else>
          <button 
            @click="playAllFavorites"
            class="mb-6 w-12 h-12 bg-primary rounded-full flex items-center justify-center shadow-lg hover:scale-105 active:scale-95 transition-all"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-black fill-current ml-1" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          </button>
          
          <div class="grid grid-cols-1 gap-1">
            <div 
              v-for="(track, index) in libraryStore.favorites" 
              :key="track.ids.deezer"
              @click="playFavorite(track)"
              class="group flex items-center gap-4 p-2 rounded-lg hover:bg-white/5 transition-colors cursor-pointer"
              :class="{ 'bg-white/5 text-primary': playbackStore.currentTrack?.ids.deezer === track.ids.deezer }"
            >
              <span class="w-6 text-center text-textGray text-sm tabular-nums group-hover:text-white" :class="{ 'text-primary font-bold': playbackStore.currentTrack?.ids.deezer === track.ids.deezer }">
                {{ index + 1 }}
              </span>
              <img :src="getImageUrl(track.album.images)" class="w-10 h-10 object-cover rounded shadow-lg" />
              <div class="flex-1 min-w-0">
                <h3 class="font-medium text-sm truncate group-hover:text-primary transition-colors" :class="{ 'text-primary': playbackStore.currentTrack?.ids.deezer === track.ids.deezer }">{{ track.title }}</h3>
                <p class="text-xs text-textGray truncate hover:underline" @click.stop="router.push(`/artist/${track.artists[0]?.ids.deezer}`)">
                  {{ track.artists.map(a => a.name).join(', ') }}
                </p>
              </div>
              <div class="hidden md:block flex-1 min-w-0 px-4 hover:underline" @click.stop="router.push(`/album/${track.album.ids.deezer}`)">
                <p class="text-xs text-textGray truncate">{{ track.album.title }}</p>
              </div>
              <div class="hidden lg:block flex-1 min-w-0 px-4">
                <p class="text-xs text-textGray truncate">{{ track.added_at ? getRelativeTime(track.added_at, t) : '-' }}</p>
              </div>
              <div class="flex items-center justify-end gap-3 pr-2">
                <button 
                  @click.stop="libraryStore.toggleFavorite(track)" 
                  class="opacity-0 group-hover:opacity-100 p-1 hover:bg-white/10 rounded-full transition-all text-primary"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 fill-current" viewBox="0 0 24 24"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>
                </button>
                <span class="text-xs text-textGray font-mono tabular-nums w-10 text-right">{{ formatDuration(track.duration_ms) }}</span>
              </div>
            </div>
          </div>
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

        <!-- Create Playlist Inline Form -->
        <div v-if="isCreatingPlaylist" class="bg-surface/50 p-6 rounded-xl border border-white/10 mb-8 space-y-4">
          <input 
            v-model="newPlaylistName"
            type="text" 
            :placeholder="t('library.new_playlist_name')"
            class="w-full bg-background border border-white/10 rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-primary transition-colors"
            @keyup.enter="handleCreatePlaylist"
            autofocus
          />
          <input 
            v-model="newPlaylistDesc"
            type="text" 
            :placeholder="t('library.new_playlist_desc')"
            class="w-full bg-background border border-white/10 rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-primary transition-colors"
            @keyup.enter="handleCreatePlaylist"
          />
          <div class="flex justify-end gap-3 pt-2">
            <button @click="isCreatingPlaylist = false" class="px-4 py-2 text-sm text-textGray hover:text-white transition-colors">{{ t('settings.close') }}</button>
            <button @click="handleCreatePlaylist" class="px-4 py-2 bg-primary text-black rounded-lg text-sm font-bold hover:scale-105 transition-transform" :disabled="!newPlaylistName.trim()">{{ t('library.create_playlist') }}</button>
          </div>
        </div>

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
            <div class="aspect-square mb-4 shadow-2xl bg-white/5 rounded-lg flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-12 h-12 text-white/20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15V6"/><path d="M18.5 18a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z"/><path d="M12 12H3"/><path d="M16 6H3"/><path d="M12 18H3"/></svg>
            </div>
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
