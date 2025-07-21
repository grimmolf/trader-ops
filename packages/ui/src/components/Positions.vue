<template>
  <div class="positions">
    <div class="positions-header">
      <h3>Positions</h3>
    </div>
    <div class="positions-list">
      <div v-for="position in positions" :key="position.symbol" class="position-item">
        <div class="position-info">
          <span class="symbol">{{ position.symbol }}</span>
          <span class="side" :class="position.side">{{ position.side.toUpperCase() }}</span>
          <span class="quantity">{{ Math.abs(position.quantity) }}</span>
        </div>
        <div class="position-pnl">
          <span class="avg-price">${{ position.averagePrice.toFixed(2) }}</span>
          <span 
            class="unrealized-pnl"
            :class="{ positive: position.unrealizedPnL > 0, negative: position.unrealizedPnL < 0 }"
          >
            ${{ position.unrealizedPnL.toFixed(2) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Position } from '../stores'

defineProps<{
  positions: Position[]
}>()
</script>

<style scoped>
.positions {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.positions-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-primary);
}

.positions-header h3 {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
}

.positions-list {
  flex: 1;
  overflow-y: auto;
}

.position-item {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-secondary);
}

.position-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.position-pnl {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
}

.side.long {
  color: var(--accent-green);
}

.side.short {
  color: var(--accent-red);
}

.unrealized-pnl.positive {
  color: var(--accent-green);
}

.unrealized-pnl.negative {
  color: var(--accent-red);
}

.avg-price {
  color: var(--text-secondary);
}
</style>