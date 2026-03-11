<script setup lang="ts">
import { ref } from 'vue';
import { useAuthStore } from '../stores/useAuthStore';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

const { t } = useI18n();
const authStore = useAuthStore();
const router = useRouter();
const arlToken = ref('');

async function handleLogin() {
  await authStore.login(arlToken.value);
  if (authStore.isAuthenticated) {
    router.push('/dashboard');
  }
}
</script>

<template>
  <div class="h-[calc(100vh-2.5rem)] flex items-center justify-center bg-background text-textWhite p-6 mt-10">
    <div class="max-w-md w-full bg-surface p-8 rounded-2xl shadow-xl border border-white/5">
      <div class="text-center mb-10 flex flex-col items-center">
        <img src="/icon.png" alt="Logo" class="w-16 h-16 object-contain mb-4" />
        <h1 class="text-3xl font-bold text-primary tracking-tight mb-2">Deeztracker</h1>
        <p class="text-textGray">{{ t('auth.login') }}</p>
      </div>

      <div class="space-y-6">
        <div>
          <label class="block text-sm font-medium text-textGray mb-2 px-1">
            {{ t('auth.arl_label') }}
          </label>
          <input 
            v-model="arlToken"
            type="password"
            :placeholder="t('auth.arl_placeholder')"
            class="w-full bg-background border border-white/10 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all placeholder:text-white/20"
            @keyup.enter="handleLogin"
          />
        </div>

        <p v-if="authStore.authError" class="text-red-400 text-sm text-center bg-red-400/10 py-2 rounded-lg">
          {{ t(authStore.authError) }}
        </p>

        <button 
          @click="handleLogin"
          :disabled="authStore.isAuthenticating"
          class="w-full bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-4 rounded-xl transition-all shadow-lg shadow-primary/20 active:scale-[0.98]"
        >
          <span v-if="!authStore.isAuthenticating">{{ t('auth.authenticate') }}</span>
          <span v-else class="flex items-center justify-center gap-2">
            <svg class="animate-spin h-5 w-5 text-white" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ t('auth.logging_in') }}
          </span>
        </button>
      </div>

      <p class="mt-8 text-xs text-center text-textGray leading-relaxed opacity-50 px-4">
        {{ t('auth.arl_help') }}
      </p>
    </div>
  </div>
</template>
