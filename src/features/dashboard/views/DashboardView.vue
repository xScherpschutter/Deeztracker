<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
</script>

<template>
  <div class="p-8 h-full overflow-y-auto">
    <h1 class="text-3xl font-bold mb-8">{{ t("dashboard.welcome") }}</h1>
    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
      <div v-for="i in 10" :key="i" class="aspect-square bg-surface rounded-xl border border-white/5 animate-pulse"></div>
    </div>
  </div>
</template>
