<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const _props = defineProps<{
  isOpen: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  isDestructive?: boolean;
}>();

const emit = defineEmits(['confirm', 'cancel']);
const { t } = useI18n();

</script>

<template>
  <Transition
    enter-active-class="transition duration-200 ease-out"
    enter-from-class="opacity-0 scale-95"
    enter-to-class="opacity-100 scale-100"
    leave-active-class="transition duration-150 ease-in"
    leave-from-class="opacity-100 scale-100"
    leave-to-class="opacity-0 scale-95"
  >
    <div v-if="isOpen" class="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" @click.self="emit('cancel')">
      <div class="bg-surface w-full max-w-sm rounded-2xl shadow-2xl overflow-hidden border border-white/10 flex flex-col">
        <!-- Header -->
        <div class="px-6 py-4 border-b border-white/5 bg-white/5 flex items-center gap-3">
          <svg v-if="isDestructive" xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-red-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          <h3 class="text-lg font-bold">{{ title }}</h3>
        </div>

        <!-- Body -->
        <div class="p-6">
          <p class="text-textGray text-sm">{{ message }}</p>
        </div>

        <!-- Footer -->
        <div class="px-6 py-4 border-t border-white/5 bg-white/5 flex justify-end gap-3">
          <button 
            @click="emit('cancel')"
            class="px-4 py-2 text-sm font-bold text-textGray hover:text-white transition-colors"
          >
            {{ cancelText || t('settings.close') }}
          </button>
          <button 
            @click="emit('confirm')"
            class="px-4 py-2 text-sm font-bold text-white rounded-lg transition-transform hover:scale-105"
            :class="isDestructive ? 'bg-red-500 hover:bg-red-600' : 'bg-primary text-black hover:bg-primary/90'"
          >
            {{ confirmText || 'Confirm' }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>
