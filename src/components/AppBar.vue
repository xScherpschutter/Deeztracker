<script setup lang="ts">
import { getCurrentWindow } from '@tauri-apps/api/window';
import { useAuthStore } from '../features/auth/stores/useAuthStore';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { ref } from 'vue';
import SettingsModal from '../features/dashboard/components/SettingsModal.vue';

const { t } = useI18n();
const appWindow = getCurrentWindow();
const authStore = useAuthStore();
const router = useRouter();
const isSettingsOpen = ref(false);

const minimize = () => appWindow.minimize();
const toggleMaximize = () => appWindow.toggleMaximize();
const close = () => appWindow.close();

const goBack = () => router.back();
const goForward = () => router.forward();
</script>

<template>
  <nav class="app-bar bg-background border-b border-white/5 fixed top-0 left-0 right-0 z-[100] flex items-center justify-between select-none h-10">
    <!-- Región de arrastre absoluta -->
    <div data-tauri-drag-region class="absolute inset-0 z-[-1] cursor-default"></div>

    <!-- Left Side: Logo & Navigation (Solo si está autenticado) -->
    <div class="flex items-center gap-4 px-4 h-full">
      <div v-if="authStore.isAuthenticated" class="flex items-center gap-2 pointer-events-none">
        <div class="w-5 h-5 bg-primary rounded flex items-center justify-center">
           <span class="text-[10px] font-bold text-black">D</span>
        </div>
        <span class="text-xs font-semibold tracking-wider text-textGray uppercase">Deeztracker</span>
      </div>

      <div v-if="authStore.isAuthenticated" class="flex items-center gap-1 ml-4">
        <button 
          @click="goBack"
          class="no-drag w-7 h-7 flex items-center justify-center rounded-full bg-black/20 text-textGray hover:text-white hover:bg-black/40 transition-all"
          :title="t('app_bar.back')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
        </button>
        <button 
          @click="goForward"
          class="no-drag w-7 h-7 flex items-center justify-center rounded-full bg-black/20 text-textGray hover:text-white hover:bg-black/40 transition-all"
          :title="t('app_bar.forward')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
      </div>
    </div>

    <!-- Right Side: Settings & Window Controls -->
    <div class="flex items-center h-full">
      <!-- Settings Icon (Solo si está autenticado) -->
      <button 
        v-if="authStore.isAuthenticated"
        @click="isSettingsOpen = true"
        class="no-drag w-10 h-full flex items-center justify-center hover:bg-white/5 text-textGray hover:text-white transition-colors border-r border-white/5"
        :title="t('app_bar.settings')"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.1a2 2 0 0 1-1-1.72v-.51a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
      </button>

      <!-- Window Controls (Siempre visibles) -->
      <div class="flex items-center h-full">
        <button 
          @click="minimize"
          class="no-drag w-10 h-full flex items-center justify-center hover:bg-white/5 text-textGray transition-colors"
          :title="t('app_bar.minimize')"
          :aria-label="t('app_bar.minimize')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/></svg>
        </button>
        <button 
          @click="toggleMaximize"
          class="no-drag w-10 h-full flex items-center justify-center hover:bg-white/5 text-textGray transition-colors"
          :title="t('app_bar.maximize')"
          :aria-label="t('app_bar.maximize')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="14" height="14" x="5" y="5" rx="1"/></svg>
        </button>
        <button 
          @click="close"
          class="no-drag w-10 h-full flex items-center justify-center hover:bg-red-500/80 hover:text-white text-textGray transition-colors"
          :title="t('app_bar.close')"
          :aria-label="t('app_bar.close')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
    </div>
    
    <!-- Settings Modal -->
    <SettingsModal :is-open="isSettingsOpen" @close="isSettingsOpen = false" />
  </nav>
</template>

<style scoped>
.app-bar {
  -webkit-app-region: drag;
}

.no-drag {
  -webkit-app-region: no-drag;
}

button {
  cursor: pointer;
}
</style>
