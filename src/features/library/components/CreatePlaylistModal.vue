<script setup lang="ts">
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useLibraryStore } from '../stores/useLibraryStore';

defineProps<{
  isOpen: boolean;
}>();

const emit = defineEmits(['close', 'created']);

const { t } = useI18n();
const libraryStore = useLibraryStore();

const name = ref('');
const description = ref('');
const isSubmitting = ref(false);

const handleCreate = async () => {
  if (!name.value.trim() || isSubmitting.value) return;
  
  isSubmitting.value = true;
  try {
    const newPlaylist = await libraryStore.createPlaylist(name.value, description.value);
    name.value = '';
    description.value = '';
    emit('created', newPlaylist);
    emit('close');
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div v-if="isOpen" class="fixed inset-0 z-[120] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm" @click.self="emit('close')">
        <div class="bg-surface border border-white/10 w-full max-w-md rounded-2xl shadow-2xl overflow-hidden">
          <div class="p-8 space-y-6">
            <h2 class="text-2xl font-bold">{{ t('library.create_playlist') }}</h2>
            
            <div class="space-y-4">
              <div class="space-y-2">
                <label class="text-xs font-bold text-textGray uppercase tracking-widest">{{ t('library.new_playlist_name') }}</label>
                <input 
                  v-model="name"
                  type="text" 
                  class="w-full bg-background border border-white/10 rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-primary transition-colors"
                  @keyup.enter="handleCreate"
                  :placeholder="t('library.new_playlist_name')"
                  autofocus
                />
              </div>
              
              <div class="space-y-2">
                <label class="text-xs font-bold text-textGray uppercase tracking-widest">{{ t('library.new_playlist_desc') }}</label>
                <textarea 
                  v-model="description"
                  rows="3"
                  class="w-full bg-background border border-white/10 rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-primary transition-colors resize-none"
                  :placeholder="t('library.new_playlist_desc')"
                ></textarea>
              </div>
            </div>

            <div class="flex justify-end gap-3 pt-2">
              <button @click="emit('close')" class="px-6 py-2.5 text-sm font-bold text-textGray hover:text-white transition-colors">
                {{ t('settings.close') }}
              </button>
              <button 
                @click="handleCreate" 
                class="px-8 py-2.5 bg-primary text-black rounded-full text-sm font-bold hover:scale-105 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed" 
                :disabled="!name.trim() || isSubmitting"
              >
                {{ t('library.create_playlist') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
