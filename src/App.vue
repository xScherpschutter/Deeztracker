<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useAuthStore } from './features/auth/stores/useAuthStore';
import LoginView from './features/auth/views/LoginView.vue';
import AppBar from './components/AppBar.vue';
import SearchView from './features/search/views/SearchView.vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const authStore = useAuthStore();
const currentView = ref<'home' | 'search'>('home');
const isInitializing = ref(true);

onMounted(async () => {
  await authStore.init();
  isInitializing.value = false;
});
</script>

<template>
  <main class="min-h-screen bg-background font-sans selection:bg-primary/30 selection:text-white pt-10">
    <AppBar />

    <!-- Pantalla de Carga Inicial -->
    <div v-if="isInitializing" class="h-[calc(100vh-2.5rem)] flex items-center justify-center">
       <div class="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
    </div>

    <!-- Pantalla de Login -->
    <LoginView v-else-if="!authStore.isAuthenticated" />

    <!-- Aplicación Principal (Dashboard) -->
    <div v-else class="flex h-[calc(100vh-2.5rem)] overflow-hidden">
      <!-- Sidebar -->
      <aside class="w-64 bg-surface border-r border-white/5 p-6 flex flex-col">
        <h2 class="text-xl font-bold text-primary mb-8 flex items-center gap-2">
          <div class="w-2 h-6 bg-primary rounded-full"></div>
          Deeztracker
        </h2>
        
        <nav class="flex-1 space-y-2">
          <button 
            @click="currentView = 'home'"
            class="w-full flex items-center gap-4 px-4 py-3 rounded-xl transition-all font-medium text-sm group"
            :class="currentView === 'home' ? 'bg-primary/10 text-primary' : 'text-textGray hover:text-white hover:bg-white/5'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
            {{ t('nav.home') }}
          </button>
          <button 
            @click="currentView = 'search'"
            class="w-full flex items-center gap-4 px-4 py-3 rounded-xl transition-all font-medium text-sm group"
            :class="currentView === 'search' ? 'bg-primary/10 text-primary' : 'text-textGray hover:text-white hover:bg-white/5'"
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

      <!-- Main Content -->
      <section class="flex-1 flex flex-col overflow-hidden relative">
        <!-- Vistas dinámicas -->
        <main v-if="currentView === 'search'" class="flex-1 overflow-hidden">
          <SearchView />
        </main>

        <template v-else-if="currentView === 'home'">
          <header class="h-16 flex items-center px-8 border-b border-white/5">
            <div class="h-4 bg-white/5 rounded w-32"></div>
          </header>
          
          <main class="flex-1 overflow-y-auto p-8">
            <h1 class="text-3xl font-bold mb-8">{{ t('dashboard.welcome') }}</h1>
            <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
              <div v-for="i in 10" :key="i" class="aspect-square bg-surface rounded-xl border border-white/5 animate-pulse"></div>
            </div>
          </main>
        </template>

        <!-- Player Bar placeholder -->
        <footer class="h-24 bg-surface border-t border-white/5 px-8 flex items-center justify-between">
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
      </section>
    </div>
  </main>
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
</style>
