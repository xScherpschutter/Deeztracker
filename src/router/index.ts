import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../features/auth/stores/useAuthStore';
import MainLayout from '../layouts/MainLayout.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: MainLayout,
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => Promise.resolve({ template: '<div class="p-8 h-full overflow-y-auto"><h1 class="text-3xl font-bold mb-8">{{ $t("dashboard.welcome") }}</h1><div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6"><div v-for="i in 10" :key="i" class="aspect-square bg-surface rounded-xl border border-white/5 animate-pulse"></div></div></div>' })
        },
        {
          path: 'search',
          name: 'search',
          component: () => import('../features/search/views/SearchView.vue')
        },
        {
          path: 'album/:id',
          name: 'album-detail',
          component: () => import('../features/search/views/AlbumDetailView.vue')
        },
        {
          path: 'artist/:id',
          name: 'artist-detail',
          component: () => import('../features/search/views/ArtistDetailView.vue')
        },
        {
          path: 'playlist/:id',
          name: 'playlist-detail',
          component: () => import('../features/search/views/PlaylistDetailView.vue')
        }
      ]
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../features/auth/views/LoginView.vue')
    }
  ]
});

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore();
  
  if (!authStore.isInitialized) {
    await authStore.init();
  }

  if (to.name !== 'login' && !authStore.isAuthenticated) {
    next({ name: 'login' });
  } else if (to.name === 'login' && authStore.isAuthenticated) {
    next({ name: 'dashboard' });
  } else {
    next();
  }
});

export default router;
