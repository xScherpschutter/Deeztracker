<script setup lang="ts">
import { watch } from 'vue';
import { getCurrentWindow } from '@tauri-apps/api/window';
import { invoke } from '@tauri-apps/api/core';
import { useI18n } from 'vue-i18n';
import PlayerBar from '../features/playback/components/PlayerBar.vue';
import QueueDrawer from '../features/playback/components/QueueDrawer.vue';
import NotificationToast from '../components/NotificationToast.vue';
import { usePlaybackStore } from '../features/playback/stores/usePlaybackStore';

const playbackStore = usePlaybackStore();
const appWindow = getCurrentWindow();
const { t, locale } = useI18n();

// Update Native Window Title (Taskbar) based on current track
watch(() => playbackStore.currentTrack, async (track) => {
  const title = track 
    ? `${track.title} - ${track.artists[0]?.name}` 
    : 'Deeztracker';
  
  // Update both DOM and Native Window
  document.title = title;
  try {
    await appWindow.setTitle(title);
  } catch (err) {
    console.error('Failed to set native window title:', err);
  }
}, { immediate: true });

// Sync Tray Menu Labels with current language
watch(locale, async () => {
  try {
    await invoke('update_tray_menu', {
      toggle: t('tray.toggle'),
      next: t('tray.next'),
      prev: t('tray.prev'),
      show: t('tray.show'),
      quit: t('tray.quit')
    });
  } catch (err) {
    console.error('Failed to update tray menu language:', err);
  }
}, { immediate: true });
</script>

<template>
  <div class="flex flex-col h-screen overflow-hidden pt-10 bg-background text-white relative">
    <!-- Main Content Area -->
    <main class="flex-1 overflow-hidden relative">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
      
      <!-- Queue Drawer -->
      <QueueDrawer />
    </main>

    <!-- Player Bar -->
    <PlayerBar />

    <!-- Notifications -->
    <NotificationToast />
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
