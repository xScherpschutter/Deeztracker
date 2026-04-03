<script setup lang="ts">
import { ref } from 'vue';
import { useDownloadStore } from '../stores/useDownloadStore';
import { useI18n } from 'vue-i18n';
import FavoritesTab from '../components/FavoritesTab.vue';
import PlaylistsTab from '../components/PlaylistsTab.vue';
import DownloadsTab from '../components/DownloadsTab.vue';

const downloadStore = useDownloadStore();
const { t } = useI18n();

const activeTab = ref<'favorites' | 'playlists' | 'downloads'>('favorites');

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
      <FavoritesTab v-if="activeTab === 'favorites'" />
      <PlaylistsTab v-else-if="activeTab === 'playlists'" />
      <DownloadsTab v-else-if="activeTab === 'downloads'" />
    </div>
  </div>
</template>

<style scoped>
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
