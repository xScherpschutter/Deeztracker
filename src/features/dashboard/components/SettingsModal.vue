<script setup lang="ts">
import { useSettingsStore } from '../stores/useSettingsStore';
import { useAuthStore } from '../../auth/stores/useAuthStore';
import { useI18n } from 'vue-i18n';
import { computed, ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';

const props = defineProps<{
  isOpen: boolean
}>();

const emit = defineEmits(['close']);

const settingsStore = useSettingsStore();
const authStore = useAuthStore();
const router = useRouter();
const { t, locale } = useI18n();

// Custom dropdown state
const qualityDropdownOpen = ref(false);
const languageDropdownOpen = ref(false);

const qualityOptions = computed(() => [
  { value: 'MP3_128', label: t('settings.audio.quality_low') },
  { value: 'MP3_320', label: t('settings.audio.quality_medium') },
  { value: 'FLAC', label: t('settings.audio.quality_high') },
]);

const languageOptions = computed(() => [
  { value: 'es', label: t('settings.appearance.languages.es') },
  { value: 'en', label: t('settings.appearance.languages.en') },
]);

const selectedQualityLabel = computed(() => {
  const option = qualityOptions.value.find(o => o.value === settingsStore.audioQuality);
  return option?.label ?? settingsStore.audioQuality;
});

const selectedLanguageLabel = computed(() => {
  const option = languageOptions.value.find(o => o.value === settingsStore.language);
  return option?.label ?? settingsStore.language;
});

const selectQuality = (value: string) => {
  settingsStore.setAudioQuality(value);
  qualityDropdownOpen.value = false;
};

const selectLanguage = (value: string) => {
  settingsStore.setLanguage(value);
  locale.value = value;
  languageDropdownOpen.value = false;
};

const toggleQualityDropdown = () => {
  qualityDropdownOpen.value = !qualityDropdownOpen.value;
  languageDropdownOpen.value = false;
};

const toggleLanguageDropdown = () => {
  languageDropdownOpen.value = !languageDropdownOpen.value;
  qualityDropdownOpen.value = false;
};

// Close dropdowns on outside click
const handleClickOutside = (e: MouseEvent) => {
  const target = e.target as HTMLElement;
  if (!target.closest('.custom-select')) {
    qualityDropdownOpen.value = false;
    languageDropdownOpen.value = false;
  }
};

onMounted(() => document.addEventListener('click', handleClickOutside));
onUnmounted(() => document.removeEventListener('click', handleClickOutside));

const arlToken = computed(() => {
  const fullArl = localStorage.getItem('deeztracker_arl') || '';
  if (fullArl.length <= 10) return fullArl;
  return `${fullArl.substring(0, 6)}...${fullArl.substring(fullArl.length - 4)}`;
});

const handleLogout = () => {
  authStore.logout();
  emit('close');
  router.push('/login');
};
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
    <div v-if="isOpen" class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" @click.self="emit('close')">
      <div class="bg-surface w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden border border-white/10 flex flex-col max-h-[85vh]">
        <!-- Header -->
        <div class="px-6 py-4 border-b border-white/5 flex items-center justify-between bg-white/5">
          <h2 class="text-xl font-bold flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-primary"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.1a2 2 0 0 1-1-1.72v-.51a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
            {{ t('settings.title') }}
          </h2>
          <button @click="emit('close')" class="p-2 hover:bg-white/10 rounded-full transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
          </button>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-y-auto p-6 space-y-8">
          
          <!-- Audio Section -->
          <section>
            <h3 class="text-xs font-bold text-textGray uppercase tracking-wider mb-4">{{ t('settings.audio.title') }}</h3>
            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <div>
                  <div class="font-medium">{{ t('settings.audio.quality') }}</div>
                  <div class="text-xs text-textGray">{{ t('settings.audio.quality_help') }}</div>
                </div>
                <!-- Custom Select: Audio Quality -->
                <div class="custom-select relative">
                  <button 
                    @click="toggleQualityDropdown"
                    class="bg-background border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary cursor-pointer text-white flex items-center gap-2 min-w-[160px] justify-between"
                  >
                    <span>{{ selectedQualityLabel }}</span>
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="transition-transform" :class="{ 'rotate-180': qualityDropdownOpen }"><path d="m6 9 6 6 6-6"/></svg>
                  </button>
                  <Transition
                    enter-active-class="transition duration-150 ease-out"
                    enter-from-class="opacity-0 -translate-y-1"
                    enter-to-class="opacity-100 translate-y-0"
                    leave-active-class="transition duration-100 ease-in"
                    leave-from-class="opacity-100 translate-y-0"
                    leave-to-class="opacity-0 -translate-y-1"
                  >
                    <div v-if="qualityDropdownOpen" class="absolute right-0 mt-1 w-full bg-white rounded-lg shadow-xl z-10 overflow-hidden border border-gray-200">
                      <button
                        v-for="option in qualityOptions"
                        :key="option.value"
                        @click="selectQuality(option.value)"
                        class="w-full text-left px-3 py-2 text-sm text-black hover:bg-primary/10 hover:text-primary transition-colors"
                        :class="{ 'bg-primary/10 text-primary font-semibold': settingsStore.audioQuality === option.value }"
                      >
                        {{ option.label }}
                      </button>
                    </div>
                  </Transition>
                </div>
              </div>
            </div>
          </section>

          <!-- Appearance Section -->
          <section>
            <h3 class="text-xs font-bold text-textGray uppercase tracking-wider mb-4">{{ t('settings.appearance.title') }}</h3>
            <div class="flex items-center justify-between">
              <div class="font-medium">{{ t('settings.appearance.language') }}</div>
              <!-- Custom Select: Language -->
              <div class="custom-select relative">
                <button 
                  @click="toggleLanguageDropdown"
                  class="bg-background border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary cursor-pointer text-white flex items-center gap-2 min-w-[160px] justify-between"
                >
                  <span>{{ selectedLanguageLabel }}</span>
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="transition-transform" :class="{ 'rotate-180': languageDropdownOpen }"><path d="m6 9 6 6 6-6"/></svg>
                </button>
                <Transition
                  enter-active-class="transition duration-150 ease-out"
                  enter-from-class="opacity-0 -translate-y-1"
                  enter-to-class="opacity-100 translate-y-0"
                  leave-active-class="transition duration-100 ease-in"
                  leave-from-class="opacity-100 translate-y-0"
                  leave-to-class="opacity-0 -translate-y-1"
                >
                  <div v-if="languageDropdownOpen" class="absolute right-0 mt-1 w-full bg-white rounded-lg shadow-xl z-10 overflow-hidden border border-gray-200">
                    <button
                      v-for="option in languageOptions"
                      :key="option.value"
                      @click="selectLanguage(option.value)"
                      class="w-full text-left px-3 py-2 text-sm text-black hover:bg-primary/10 hover:text-primary transition-colors"
                      :class="{ 'bg-primary/10 text-primary font-semibold': settingsStore.language === option.value }"
                    >
                      {{ option.label }}
                    </button>
                  </div>
                </Transition>
              </div>
            </div>
          </section>

          <!-- Account Section -->
          <section>
            <h3 class="text-xs font-bold text-textGray uppercase tracking-wider mb-4">{{ t('settings.account.title') }}</h3>
            <div class="bg-white/5 rounded-xl p-4 space-y-4">
              <div class="flex items-center justify-between">
                <span class="text-sm text-textGray">{{ t('settings.account.status') }}</span>
                <span 
                  class="text-xs font-bold px-2 py-1 rounded-full"
                  :class="authStore.isPremium ? 'bg-primary/20 text-primary' : 'bg-white/10 text-white/60'"
                >
                  {{ authStore.isPremium ? t('settings.account.premium') : t('settings.account.free') }}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm text-textGray">{{ t('settings.account.arl_token') }}</span>
                <span class="text-xs font-mono text-white/40">{{ arlToken }}</span>
              </div>
              <button 
                @click="handleLogout"
                class="w-full py-2 bg-red-500/10 hover:bg-red-500/20 text-red-500 rounded-lg text-sm font-bold transition-colors mt-2"
              >
                {{ t('settings.account.logout') }}
              </button>
            </div>
          </section>

          <!-- About Section -->
          <section class="pt-2">
            <div class="flex items-center justify-between text-xs text-textGray">
              <span>Deeztracker</span>
              <span>{{ t('settings.about.version') }} 0.1.0</span>
            </div>
          </section>

        </div>

        <!-- Footer -->
        <div class="px-6 py-4 bg-white/5 border-t border-white/5 flex justify-end">
          <button 
            @click="emit('close')"
            class="px-6 py-2 bg-white text-black rounded-full font-bold text-sm hover:scale-105 transition-transform"
          >
            {{ t('settings.close') }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
/* Custom scrollbar for the modal content */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>
