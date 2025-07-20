<template>
  <div class="news-feed">
    <div class="news-header">
      <h3>Market News</h3>
      <span class="symbol-filter">{{ symbol }}</span>
    </div>
    <div class="news-content">
      <div v-for="item in newsItems" :key="item.id" class="news-item">
        <div class="news-meta">
          <span class="time">{{ formatTime(item.timestamp) }}</span>
          <span class="source">{{ item.source }}</span>
        </div>
        <div class="news-headline">{{ item.headline }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  symbol: string
}>()

// Mock news data
const newsItems = ref([
  {
    id: 1,
    headline: "Futures market shows strong momentum ahead of opening",
    source: "MarketWatch",
    timestamp: new Date(Date.now() - 5 * 60 * 1000)
  },
  {
    id: 2,
    headline: "Fed officials signal continued monetary policy support",
    source: "Reuters",
    timestamp: new Date(Date.now() - 15 * 60 * 1000)
  },
  {
    id: 3,
    headline: "Technology sector leads early trading gains",
    source: "Bloomberg",
    timestamp: new Date(Date.now() - 25 * 60 * 1000)
  }
])

function formatTime(date: Date): string {
  return date.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}
</script>

<style scoped>
.news-feed {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
}

.news-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-primary);
}

.news-header h3 {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
}

.symbol-filter {
  font-size: 12px;
  color: var(--accent-blue);
  font-weight: 500;
}

.news-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px;
}

.news-item {
  padding: 12px 0;
  border-bottom: 1px solid var(--border-secondary);
}

.news-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  font-size: 11px;
  color: var(--text-secondary);
}

.news-headline {
  font-size: 12px;
  line-height: 1.4;
  color: var(--text-primary);
}
</style>