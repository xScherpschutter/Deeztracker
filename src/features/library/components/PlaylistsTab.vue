<script setup lang="ts">
import { ref } from 'vue';
import { useLibraryStore } from '../stores/useLibraryStore';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import ConfirmModal from '../../../components/ConfirmModal.vue';
import PlaylistCover from './PlaylistCover.vue';
import CreatePlaylistModal from './CreatePlaylistModal.vue';

const libraryStore = useLibraryStore();
const router = useRouter();
const { t } = useI18n();

const isCreatingPlaylist = ref(false);
const showDeleteModal = ref(false);
const playlistToDelete = ref<number | null>(null);

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
  <div class="flex-1 flex flex-col space-y-6">
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
    <CreatePlaylistModal 
      :is-open="isCreatingPlaylist" 
      @close="isCreatingPlaylist = false" 
    />

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
