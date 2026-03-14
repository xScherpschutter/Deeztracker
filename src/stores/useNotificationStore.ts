import { defineStore } from 'pinia';

export const useNotificationStore = defineStore('notification', {
  state: () => ({
    message: '',
    type: 'success' as 'success' | 'error' | 'info',
    show: false,
    timeoutId: null as any
  }),
  actions: {
    notify(message: string, type: 'success' | 'error' | 'info' = 'success', duration = 3000) {
      // Clear previous timeout if exists to avoid early hiding
      if (this.timeoutId) clearTimeout(this.timeoutId);
      
      this.message = message;
      this.type = type;
      this.show = true;
      
      this.timeoutId = setTimeout(() => {
        this.show = false;
        this.timeoutId = null;
      }, duration);
    }
  }
});
