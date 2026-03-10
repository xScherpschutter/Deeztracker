<script setup lang="ts">
interface Props {
  size?: 'sm' | 'md' | 'lg';
}

withDefaults(defineProps<Props>(), {
  size: 'md'
});

const sizeClasses = {
  sm: 'w-8 h-8 border-2',
  md: 'w-12 h-12 border-4',
  lg: 'w-16 h-16 border-4'
};
</script>

<template>
  <div class="flex-1 flex items-center justify-center min-h-[200px]">
    <div 
      class="border-primary/20 border-t-primary rounded-full animate-spin"
      :class="sizeClasses[size]"
    ></div>
  </div>
</template>
