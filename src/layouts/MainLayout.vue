<script setup lang="ts">
import { ref, watch } from 'vue';
import { getCurrentWindow } from '@tauri-apps/api/window';
import PlayerBar from '../features/playback/components/PlayerBar.vue';
import QueueDrawer from '../features/playback/components/QueueDrawer.vue';
import NotificationToast from '../components/NotificationToast.vue';
import { usePlaybackStore } from '../features/playback/stores/usePlaybackStore';

const playbackStore = usePlaybackStore();
const isDraggingOver = ref(false);
const appWindow = getCurrentWindow();

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

const onDrop = (e: DragEvent) => {
  isDraggingOver.value = false;
  const trackData = e.dataTransfer?.getData('application/json');
  if (trackData) {
    try {
      const track = JSON.parse(trackData);
      playbackStore.addToQueue(track);
    } catch (err) {
      console.error('Failed to parse dropped track:', err);
    }
  }
};
</script>

<template>
  <div 
    class="flex flex-col h-screen overflow-hidden pt-10 bg-background text-white relative"
    @dragover.prevent="isDraggingOver = true"
    @dragleave.prevent="isDraggingOver = false"
    @drop.prevent="onDrop"
  >
    <!-- Drop Overlay Visual Hint -->
    <div 
      v-if="isDraggingOver" 
      class="absolute inset-0 z-[100] bg-primary/10 backdrop-blur-[2px] border-4 border-dashed border-primary/40 flex items-center justify-center pointer-events-none"
    >
      <div class="bg-surface p-8 rounded-2xl shadow-2xl flex flex-col items-center gap-4 border border-white/10 scale-in">
        <div class="w-16 h-16 bg-primary/20 rounded-full flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-8 h-8 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
        </div>
        <p class="text-xl font-bold text-primary">Soltar para añadir a la cola</p>
      </div>
    </div>

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
