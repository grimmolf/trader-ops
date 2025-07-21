<template>
  <div class="watchlist">
    <div class="watchlist-header">
      <h3>Watchlist</h3>
    </div>
    <div class="symbol-list">
      <div
        v-for="quote in quotes"
        :key="quote.symbol"
        @click="$emit('symbol-clicked', quote.symbol)"
        class="symbol-item"
        :class="{ active: quote.symbol === activeSymbol }"
      >
        <div class="symbol-info">
          <span class="symbol">{{ quote.symbol }}</span>
          <span class="price">${{ formatPrice(quote.price) }}</span>
        </div>
        <div class="change-info">
          <span 
            class="change"
            :class="{ positive: quote.change > 0, negative: quote.change < 0 }"
          >
            {{ quote.change > 0 ? '+' : '' }}${{ formatPrice(Math.abs(quote.change)) }}
          </span>
          <span 
            class="change-percent"
            :class="{ positive: quote.changePercent > 0, negative: quote.changePercent < 0 }"
          >
            ({{ quote.changePercent > 0 ? '+' : '' }}{{ quote.changePercent.toFixed(2) }}%)
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Quote } from '../stores'

defineProps<{
  symbols: string[]
  quotes: Quote[]
  activeSymbol: string
}>()

defineEmits<{
  'symbol-clicked': [symbol: string]
  'symbol-removed': [symbol: string]
}>()

function formatPrice(price: number): string {
  return price.toFixed(2)
}
</script>

<style scoped>
.watchlist {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.watchlist-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-primary);
}

.watchlist-header h3 {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
}

.symbol-list {
  flex: 1;
  overflow-y: auto;
}

.symbol-item {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-secondary);
  cursor: pointer;
  transition: background-color 0.1s;
}

.symbol-item:hover {
  background: var(--bg-hover);
}

.symbol-item.active {
  background: var(--bg-hover);
  border-left: 3px solid var(--accent-blue);
}

.symbol-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.symbol {
  font-weight: 600;
  font-size: 13px;
}

.price {
  font-size: 13px;
  font-weight: 500;
}

.change-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
}

.change.positive,
.change-percent.positive {
  color: var(--accent-green);
}

.change.negative,
.change-percent.negative {
  color: var(--accent-red);
}
</style>