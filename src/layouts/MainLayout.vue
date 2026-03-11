<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '../features/auth/stores/useAuthStore';
import { useI18n } from 'vue-i18n';
import PlayerBar from '../features/playback/components/PlayerBar.vue';

const { t } = useI18n();
const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

const isActive = (name: string) => route.name === name || route.path.startsWith(`/${name}`);
</script>

<template>
  <div class="flex h-screen overflow-hidden pt-10 bg-background text-white">
    <!-- Sidebar -->
    <aside class="w-64 bg-surface border-r border-white/5 p-6 flex flex-col flex-shrink-0">
      <nav class="flex-1 space-y-2">
        <button 
          @click="router.push('/dashboard')"
          class="w-full flex items-center gap-4 px-4 py-3 rounded-xl transition-all font-medium text-sm group"
          :class="isActive('dashboard') ? 'bg-primary/10 text-primary' : 'text-textGray hover:text-white hover:bg-white/5'"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
          {{ t('nav.home') }}
        </button>
        <button 
          @click="router.push('/search')"
          class="w-full flex items-center gap-4 px-4 py-3 rounded-xl transition-all font-medium text-sm group"
          :class="isActive('search') ? 'bg-primary/10 text-primary' : 'text-textGray hover:text-white hover:bg-white/5'"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
          {{ t('nav.search') }}
        </button>
        
        <div class="pt-6 pb-2 px-4 text-[10px] font-bold text-textGray/40 uppercase tracking-widest">{{ t('nav.library') }}</div>
        <div class="space-y-1">
          <div class="h-10 px-4 flex items-center gap-4 text-textGray/40 text-sm italic">{{ t('nav.coming_soon') }}</div>
        </div>
      </nav>
    </aside>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden relative">
      <!-- Dynamic View Container -->
      <main class="flex-1 overflow-hidden relative">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>

      <!-- Player Bar -->
      <PlayerBar />
    </div>
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
