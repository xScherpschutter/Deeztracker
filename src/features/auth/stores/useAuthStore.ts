import { defineStore } from 'pinia';
import { ref } from 'vue';
import { AuthService } from '../services/authService';
import { usePlaybackStore } from '../../playback/stores/usePlaybackStore';

const ARL_KEY = 'deeztracker_arl';

export const useAuthStore = defineStore('auth', () => {
  const isAuthenticated = ref(false);
  const isAuthenticating = ref(false);
  const isInitialized = ref(false);
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
    localStorage.removeItem(ARL_KEY);
  }

  async function init() {
    if (isInitialized.value) return;
    
    const savedArl = localStorage.getItem(ARL_KEY);
    if (savedArl) {
      await login(savedArl, false);
    }
    isInitialized.value = true;
  }

  return {
    isAuthenticated,
    isAuthenticating,
    isInitialized,
    authError,
    login,
    logout,
    init
  };
});
