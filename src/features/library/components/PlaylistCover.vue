<script setup lang="ts">
defineProps<{
  covers: string[];
  size?: 'sm' | 'md' | 'lg' | 'xl';
}>();
</script>

<template>
  <div class="relative aspect-square bg-white/5 rounded-lg overflow-hidden shadow-2xl flex items-center justify-center group-hover:shadow-primary/20 transition-all duration-500">
    <!-- Empty State -->
    <template v-if="covers.length === 0">
      <svg xmlns="http://www.w3.org/2000/svg" 
           :class="[
             'text-white/20',
             size === 'xl' ? 'w-24 h-24' : 'w-12 h-12'
           ]" 
           viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M21 15V6"/><path d="M18.5 18a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z"/><path d="M12 12H3"/><path d="M16 6H3"/><path d="M12 18H3"/>
      </svg>
    </template>

    <!-- Mosaic (4 covers) -->
    <template v-else-if="covers.length >= 4">
      <div class="grid grid-cols-2 grid-rows-2 w-full h-full">
        <img v-for="(cover, index) in covers.slice(0, 4)" 
             :key="index" 
             :src="cover" 
             class="w-full h-full object-cover" />
      </div>
    </template>

    <!-- Single Cover (1-3 covers) -->
    <template v-else>
      <img :src="covers[0]" class="w-full h-full object-cover" />
    </template>
  </div>
</template>
