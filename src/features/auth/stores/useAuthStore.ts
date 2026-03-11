import { defineStore } from 'pinia';
import { ref } from 'vue';
import { AuthService } from '../services/authService';
import { usePlaybackStore } from '../../playback/stores/usePlaybackStore';
import { useSettingsStore } from '../../dashboard/stores/useSettingsStore';
import { invoke } from '@tauri-apps/api/core';

const ARL_KEY = 'deeztracker_arl';

export const useAuthStore = defineStore('auth', () => {
  const isAuthenticated = ref(false);
  const isAuthenticating = ref(false);
  const isInitialized = ref(false);
  const isPremium = ref(false);
  const authError = ref<string | null>(null);

  const playbackStore = usePlaybackStore();

  async function login(arl: string, save: boolean = true) {
    if (!arl) return;
    isAuthenticating.value = true;
    authError.value = null;

    try {
      const success = await AuthService.login(arl);
      if (success) {
        isAuthenticated.value = true;
        
        // Sync settings with backend now that we are authenticated
        const settingsStore = useSettingsStore();
        await settingsStore.init();

        // Check premium status after successful login
        isPremium.value = await invoke<boolean>("is_premium");
        
        if (save) {
          localStorage.setItem(ARL_KEY, arl);
        }
      } else {
        authError.value = 'auth.error_failed';
        localStorage.removeItem(ARL_KEY);
      }
    } catch (e) {
      authError.value = 'auth.error_failed';
      localStorage.removeItem(ARL_KEY);
    } finally {
      isAuthenticating.value = false;
    }
  }

  function logout() {
    playbackStore.stop();
    isAuthenticated.value = false;
    isPremium.value = false;
    localStorage.removeItem(ARL_KEY);
  }

  async function init() {
    if (isInitialized.value) return;
    
    const savedArl = localStorage.getItem(ARL_KEY);
    if (savedArl) {
      await login(savedArl, false);
      
      // Refresh premium status explicitly
      try {
        isPremium.value = await invoke<boolean>("is_premium");
      } catch (e) {
        console.error("Failed to verify premium on init", e);
      }
    }
    isInitialized.value = true;
  }

  return {
    isAuthenticated,
    isAuthenticating,
    isInitialized,
    isPremium,
    authError,
    login,
    logout,
    init
  };
});
