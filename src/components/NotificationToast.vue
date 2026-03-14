<script setup lang="ts">
import { useNotificationStore } from '../stores/useNotificationStore';
import { storeToRefs } from 'pinia';

const notificationStore = useNotificationStore();
const { show, message, type } = storeToRefs(notificationStore);
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="translate-y-12 opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="translate-y-0 opacity-100"
      leave-to-class="translate-y-12 opacity-0"
    >
      <div 
        v-if="show" 
        class="fixed bottom-28 left-1/2 -translate-x-1/2 z-[100] px-6 py-3 rounded-full font-bold shadow-2xl flex items-center gap-3 min-w-[200px] justify-center transition-colors duration-300"
        :class="{
          'bg-primary text-black': type === 'success',
          'bg-red-500 text-white': type === 'error',
          'bg-surface text-white border border-white/10': type === 'info'
        }"
      >
        <!-- Success Icon -->
        <svg v-if="type === 'success'" xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
        
        <!-- Error Icon -->
        <svg v-else-if="type === 'error'" xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
        
        <!-- Info Icon -->
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>

        <span class="text-sm truncate">{{ message }}</span>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.shadow-2xl {
  box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.5);
}

.bg-primary {
  box-shadow: 0 10px 30px -10px rgba(0, 170, 255, 0.4);
}

.bg-red-500 {
  box-shadow: 0 10px 30px -10px rgba(239, 68, 68, 0.4);
}
</style>