<template>
  <div class="order-history">
    <div class="orders-header">
      <h3>Recent Orders</h3>
    </div>
    <div class="orders-list">
      <div v-for="order in orders.slice(0, 10)" :key="order.id" class="order-item">
        <div class="order-info">
          <span class="symbol">{{ order.symbol }}</span>
          <span class="side" :class="order.side">{{ order.side.toUpperCase() }}</span>
          <span class="quantity">{{ order.quantity }}</span>
        </div>
        <div class="order-details">
          <span class="price">${{ order.price.toFixed(2) }}</span>
          <span class="status" :class="order.status">{{ order.status.toUpperCase() }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Order } from '../src/stores/trading'

defineProps<{
  orders: Order[]
}>()
</script>

<style scoped>
.order-history {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.orders-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-primary);
}

.orders-header h3 {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
}

.orders-list {
  flex: 1;
  overflow-y: auto;
}

.order-item {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-secondary);
}

.order-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.order-details {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-secondary);
}

.side.buy {
  color: var(--accent-green);
}

.side.sell {
  color: var(--accent-red);
}

.status.filled {
  color: var(--accent-green);
}

.status.pending {
  color: var(--accent-yellow);
}

.status.cancelled {
  color: var(--accent-red);
}
</style>