<template>
  <div class="account-info">
    <div v-if="account" class="account-details">
      <div class="account-item">
        <span class="label">Balance:</span>
        <span class="value">${{ formatNumber(account.balance) }}</span>
      </div>
      <div class="account-item">
        <span class="label">P&L:</span>
        <span 
          class="value"
          :class="{ 'positive': account.dayPnL > 0, 'negative': account.dayPnL < 0 }"
        >
          ${{ formatNumber(account.dayPnL) }}
        </span>
      </div>
      <div class="account-item">
        <span class="label">BP:</span>
        <span class="value">${{ formatNumber(account.buyingPower) }}</span>
      </div>
    </div>
    <div v-else class="account-loading">
      Loading account...
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Account } from '../stores'

defineProps<{
  account: Account | null
}>()

function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value)
}
</script>

<style scoped>
.account-info {
  display: flex;
  align-items: center;
}

.account-details {
  display: flex;
  gap: 16px;
}

.account-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.label {
  font-size: 10px;
  color: var(--text-secondary);
  text-transform: uppercase;
}

.value {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
}

.value.positive {
  color: var(--accent-green);
}

.value.negative {
  color: var(--accent-red);
}

.account-loading {
  font-size: 12px;
  color: var(--text-secondary);
}
</style>