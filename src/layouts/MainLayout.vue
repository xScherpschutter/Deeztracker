<script setup lang="ts">
import PlayerBar from '../features/playback/components/PlayerBar.vue';
import QueueDrawer from '../features/playback/components/QueueDrawer.vue';
</script>

<template>
  <div class="flex flex-col h-screen overflow-hidden pt-10 bg-background text-white">
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
