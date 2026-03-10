<script setup lang="ts">
import { useAuthStore } from './features/auth/stores/useAuthStore';
import AppBar from './components/AppBar.vue';

const authStore = useAuthStore();
</script>

<template>
  <div v-if="!authStore.isInitialized" class="min-h-screen bg-background flex items-center justify-center">
     <div class="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
  </div>
  <div v-else class="min-h-screen bg-background text-white">
    <AppBar />
    <router-view />
  </div>
</template>

<style>
/* Estilos globales suaves */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.1);
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
