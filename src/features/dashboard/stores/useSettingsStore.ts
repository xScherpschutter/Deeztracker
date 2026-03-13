import { defineStore } from 'pinia';
import { ref } from 'vue';
import { invoke } from '@tauri-apps/api/core';

export const useSettingsStore = defineStore('settings', () => {
  const audioQuality = ref(localStorage.getItem('settings_audio_quality') || 'MP3_128');
  const language = ref(localStorage.getItem('settings_language') || 'es');

  // Use i18n if called within a component, otherwise we'll handle it in the init
  const setLanguage = (lang: string) => {
    language.value = lang;
    localStorage.setItem('settings_language', lang);
    // Note: Actual i18n.locale update should happen in the component or a global watcher
  };

  const setAudioQuality = async (quality: string) => {
    try {
      await invoke('set_audio_quality', { quality });
      audioQuality.value = quality;
      localStorage.setItem('settings_audio_quality', quality);
    } catch (error) {
      console.error('Failed to set audio quality:', error);
    }
  };

  const init = async () => {
    // Sync audio quality with backend on startup
    try {
      await invoke('set_audio_quality', { quality: audioQuality.value });
    } catch (e) {

    }
  };

  return {
    audioQuality,
    language,
    setLanguage,
    setAudioQuality,
    init
  };
});
