<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '../features/auth/stores/useAuthStore';
import { useI18n } from 'vue-i18n';

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
      <h2 class="text-xl font-bold text-primary mb-8 flex items-center gap-2">
        <div class="w-2 h-6 bg-primary rounded-full"></div>
        Deeztracker
      </h2>
      
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
      <footer class="h-24 bg-surface border-t border-white/5 px-8 flex items-center justify-between flex-shrink-0 z-20">
        <div class="flex items-center gap-4 w-1/3">
          <div class="w-14 h-14 bg-background rounded-lg"></div>
          <div class="space-y-2">
            <div class="h-4 bg-white/5 rounded w-32"></div>
            <div class="h-3 bg-white/5 rounded w-24"></div>
          </div>
        </div>
        <div class="flex flex-col items-center gap-3 w-1/3">
           <div class="flex items-center gap-6">
             <div class="w-4 h-4 bg-white/10 rounded-full"></div>
             <div class="w-10 h-10 bg-primary/20 rounded-full"></div>
             <div class="w-4 h-4 bg-white/10 rounded-full"></div>
           </div>
           <div class="w-full h-1 bg-white/5 rounded-full relative">
             <div class="absolute inset-y-0 left-0 w-1/3 bg-primary rounded-full"></div>
           </div>
        </div>
        <div class="w-1/3 flex justify-end">
          <div class="w-32 h-1 bg-white/5 rounded-full"></div>
        </div>
      </footer>
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
