import { defineStore } from 'pinia';
import { ref, watch } from 'vue';
import { SearchService } from '../services/searchService';
import type { Track, Album, Artist, Playlist, SearchType } from '../models/search';

export const useSearchStore = defineStore('search', () => {
  const query = ref('');
  const activeType = ref<SearchType>('all');
  const isLoading = ref(false);
  const isLoadingMore = ref(false);
  const isInitialized = ref(false);
  const authError = ref<string | null>(null);

  const results = ref({
    tracks: [] as Track[],
    albums: [] as Album[],
    artists: [] as Artist[],
    playlists: [] as Playlist[]
  });

  const pagination = ref({
    tracks: { index: 0, hasMore: true },
    albums: { index: 0, hasMore: true },
    artists: { index: 0, hasMore: true },
    playlists: { index: 0, hasMore: true }
  });

  const LIMIT = 40;

  async function performSearch() {
    if (!query.value.trim()) {
      clearResults();
      return;
    }

    // Limpiamos resultados previos inmediatamente para evitar "flashes" de datos viejos
    clearResults();
    
    isLoading.value = true;
    authError.value = null;

    try {
      if (activeType.value === 'all') {
        const res = await SearchService.searchAll(query.value, 10);
        results.value = res;
      } else {
        const type = activeType.value;
        let newResults: any[] = [];

        switch (type) {
          case 'tracks':
            newResults = await SearchService.searchTracks(query.value, LIMIT, 0);
            results.value.tracks = newResults;
            break;
          case 'albums':
            newResults = await SearchService.searchAlbums(query.value, LIMIT, 0);
            results.value.albums = newResults;
            break;
          case 'artists':
            newResults = await SearchService.searchArtists(query.value, LIMIT, 0);
            results.value.artists = newResults;
            break;
          case 'playlists':
            newResults = await SearchService.searchPlaylists(query.value, LIMIT, 0);
            results.value.playlists = newResults;
            break;
        }

        pagination.value[type].index = newResults.length;
        pagination.value[type].hasMore = newResults.length === LIMIT;
      }
    } catch (e) {
      console.error('Search error:', e);
    } finally {
      isLoading.value = false;
    }
  }

  async function loadMore() {
    const type = activeType.value;
    if (type === 'all' || isLoadingMore.value || !pagination.value[type].hasMore) return;

    isLoadingMore.value = true;
    const currentIndex = pagination.value[type].index;

    try {
      let newResults: any[] = [];
      switch (type) {
        case 'tracks':
          newResults = await SearchService.searchTracks(query.value, LIMIT, currentIndex);
          results.value.tracks.push(...newResults);
          break;
        case 'albums':
          newResults = await SearchService.searchAlbums(query.value, LIMIT, currentIndex);
          results.value.albums.push(...newResults);
          break;
        case 'artists':
          newResults = await SearchService.searchArtists(query.value, LIMIT, currentIndex);
          results.value.artists.push(...newResults);
          break;
        case 'playlists':
          newResults = await SearchService.searchPlaylists(query.value, LIMIT, currentIndex);
          results.value.playlists.push(...newResults);
          break;
      }

      pagination.value[type].index += newResults.length;
      pagination.value[type].hasMore = newResults.length === LIMIT;
    } catch (e) {
      console.error('Load more error:', e);
    } finally {
      isLoadingMore.value = false;
    }
  }

  function clearResults() {
    results.value = {
      tracks: [],
      albums: [],
      artists: [],
      playlists: []
    };
    pagination.value = {
      tracks: { index: 0, hasMore: true },
      albums: { index: 0, hasMore: true },
      artists: { index: 0, hasMore: true },
      playlists: { index: 0, hasMore: true }
    };
  }

  let debounceTimeout: number | undefined;
  watch([query, activeType], () => {
    clearTimeout(debounceTimeout);
    debounceTimeout = window.setTimeout(() => {
      performSearch();
    }, 400);
  });

  return {
    query,
    activeType,
    results,
    isLoading,
    isLoadingMore,
    isInitialized,
    authError,
    performSearch,
    loadMore,
    clearResults
  };
});
