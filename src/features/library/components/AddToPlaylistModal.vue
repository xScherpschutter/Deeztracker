<script setup lang="ts">
import { useLibraryStore } from '../stores/useLibraryStore';
import { useI18n } from 'vue-i18n';
import type { Track } from '../../search/models/search';
import PlaylistCover from './PlaylistCover.vue';

const props = defineProps<{
  isOpen: boolean;
  track: Track | null;
}>();

const emit = defineEmits(['close']);

const libraryStore = useLibraryStore();
const { t } = useI18n();

const addToPlaylist = async (playlistId: number) => {
  if (props.track) {
    await libraryStore.addTrackToPlaylist(playlistId, props.track);
    emit('close');
  }
};
</script>

<template>
  <Transition
    enter-active-class="transition duration-200 ease-out"
    enter-from-class="opacity-0 scale-95"
    enter-to-class="opacity-100 scale-100"
    leave-active-class="transition duration-150 ease-in"
    leave-from-class="opacity-100 scale-100"
    leave-to-class="opacity-0 scale-95"
  >
    <div v-if="isOpen" class="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" @click.self="emit('close')">
      <div class="bg-surface w-full max-w-sm rounded-2xl shadow-2xl overflow-hidden border border-white/10 flex flex-col max-h-[70vh]">
        <!-- Header -->
        <div class="px-6 py-4 border-b border-white/5 bg-white/5 flex items-center justify-between">
          <h3 class="text-lg font-bold truncate">{{ t('library.add_to_playlist') }}</h3>
          <button @click="emit('close')" class="text-textGray hover:text-white transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
          </button>
        </div>

        <!-- Track Info -->
        <div v-if="track" class="px-6 py-4 flex items-center gap-3 bg-white/5 border-b border-white/5">
          <img :src="track.album.images[0]?.url" class="w-10 h-10 rounded shadow" />
          <div class="min-w-0">
            <p class="text-sm font-bold truncate">{{ track.title }}</p>
            <p class="text-xs text-textGray truncate">{{ track.artists.map(a => a.name).join(', ') }}</p>
          </div>
        </div>

        <!-- List -->
        <div class="flex-1 overflow-y-auto p-2 custom-scrollbar">
          <div v-if="libraryStore.playlists.length === 0" class="p-8 text-center">
            <p class="text-sm text-textGray mb-4">{{ t('library.no_playlists') }}</p>
          </div>
          <button 
            v-for="playlist in libraryStore.playlists" 
            :key="playlist.id"
            @click="addToPlaylist(playlist.id)"
            class="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-white/10 transition-colors text-left"
          >
            <PlaylistCover :covers="playlist.preview_covers" class="w-10 h-10 flex-shrink-0" />
            <div class="min-w-0">
              <p class="text-sm font-medium truncate">{{ playlist.name }}</p>
            </div>
          </button>
        </div>

        <!-- Footer -->
        <div class="px-6 py-4 border-t border-white/5 bg-white/5">
          <button 
            @click="emit('close')"
            class="w-full py-2 bg-white text-black rounded-full font-bold text-sm hover:scale-105 transition-transform"
          >
            {{ t('settings.close') }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>
