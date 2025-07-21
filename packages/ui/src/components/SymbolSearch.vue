<template>
  <div class="symbol-search">
    <input
      v-model="searchQuery"
      @input="onSearch"
      @keyup.enter="selectSymbol"
      placeholder="Search symbols..."
      class="search-input"
    />
    <div v-if="showResults && searchResults.length" class="search-results">
      <div
        v-for="symbol in searchResults"
        :key="symbol"
        @click="selectSymbol(symbol)"
        class="search-result"
      >
        {{ symbol }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const emit = defineEmits<{
  'symbol-selected': [symbol: string]
}>()

const searchQuery = ref('')
const showResults = ref(false)

const searchResults = computed(() => {
  if (!searchQuery.value || searchQuery.value.length < 2) return []
  
  // Mock search results - in real implementation, this would call the backend
  const symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'MNQ1!', 'ES1!', 'NQ1!']
  return symbols.filter(symbol => 
    symbol.toLowerCase().includes(searchQuery.value.toLowerCase())
  ).slice(0, 5)
})

function onSearch() {
  showResults.value = searchQuery.value.length >= 2
}

function selectSymbol(symbol?: string) {
  const selectedSymbol = symbol || searchQuery.value.toUpperCase()
  emit('symbol-selected', selectedSymbol)
  searchQuery.value = ''
  showResults.value = false
}
</script>

<style scoped>
.symbol-search {
  position: relative;
}

.search-input {
  width: 200px;
  padding: 6px 12px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-primary);
  border-radius: 4px;
  color: var(--text-primary);
  font-size: 13px;
}

.search-input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 1000;
}

.search-result {
  padding: 8px 12px;
  cursor: pointer;
  font-size: 13px;
}

.search-result:hover {
  background: var(--bg-hover);
}
</style>