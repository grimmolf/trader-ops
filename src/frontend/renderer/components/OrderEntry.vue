<template>
  <div class="order-entry">
    <div class="order-header">
      <h3>Order Entry</h3>
      <span class="symbol">{{ symbol }}</span>
    </div>
    
    <div class="order-form">
      <div class="side-buttons">
        <button 
          @click="orderSide = 'buy'"
          class="side-btn buy"
          :class="{ active: orderSide === 'buy' }"
        >
          BUY
        </button>
        <button 
          @click="orderSide = 'sell'"
          class="side-btn sell"
          :class="{ active: orderSide === 'sell' }"
        >
          SELL
        </button>
      </div>
      
      <div class="form-row">
        <label>Type:</label>
        <select v-model="orderType" class="form-select">
          <option value="market">Market</option>
          <option value="limit">Limit</option>
          <option value="stop">Stop</option>
        </select>
      </div>
      
      <div class="form-row">
        <label>Quantity:</label>
        <input v-model.number="quantity" type="number" class="form-input" min="1" />
      </div>
      
      <div v-if="orderType === 'limit'" class="form-row">
        <label>Price:</label>
        <input v-model.number="price" type="number" class="form-input" step="0.01" />
      </div>
      
      <button @click="submitOrder" class="submit-btn" :disabled="!canSubmit">
        Submit {{ orderSide.toUpperCase() }} Order
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Account, Quote } from '../src/stores/trading'

const props = defineProps<{
  symbol: string
  account: Account | null
  currentQuote: Quote | undefined
}>()

const emit = defineEmits<{
  'order-submitted': [orderData: any]
}>()

const orderSide = ref<'buy' | 'sell'>('buy')
const orderType = ref<'market' | 'limit' | 'stop'>('market')
const quantity = ref(1)
const price = ref(0)

const canSubmit = computed(() => {
  return quantity.value > 0 && (orderType.value === 'market' || price.value > 0)
})

function submitOrder() {
  if (!canSubmit.value) return
  
  const orderData = {
    symbol: props.symbol,
    side: orderSide.value,
    type: orderType.value,
    quantity: quantity.value,
    price: orderType.value === 'market' ? (props.currentQuote?.price || 0) : price.value
  }
  
  emit('order-submitted', orderData)
  
  // Reset form
  quantity.value = 1
  if (orderType.value === 'limit') {
    price.value = 0
  }
}
</script>

<style scoped>
.order-entry {
  padding: 16px;
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.order-header h3 {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
}

.symbol {
  font-size: 13px;
  color: var(--accent-blue);
  font-weight: 500;
}

.side-buttons {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.side-btn {
  flex: 1;
  padding: 8px;
  border: 1px solid var(--border-primary);
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
}

.side-btn.buy.active {
  background: var(--accent-green);
  border-color: var(--accent-green);
  color: white;
}

.side-btn.sell.active {
  background: var(--accent-red);
  border-color: var(--accent-red);
  color: white;
}

.form-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.form-row label {
  font-size: 12px;
  color: var(--text-secondary);
}

.form-input,
.form-select {
  width: 100px;
  padding: 4px 8px;
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: 4px;
  color: var(--text-primary);
  font-size: 12px;
}

.submit-btn {
  width: 100%;
  padding: 10px;
  background: var(--accent-blue);
  border: none;
  border-radius: 4px;
  color: white;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 8px;
}

.submit-btn:disabled {
  background: var(--bg-hover);
  color: var(--text-secondary);
  cursor: not-allowed;
}
</style>