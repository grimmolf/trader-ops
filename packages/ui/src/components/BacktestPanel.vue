<template>
  <div class="backtest-panel">
    <div class="backtest-header">
      <h3>Backtesting</h3>
    </div>
    <div class="backtest-content">
      <div class="backtest-form">
        <div class="form-group">
          <label>Symbol:</label>
          <span class="symbol-display">{{ symbol }}</span>
        </div>
        <div class="form-group">
          <label>Strategy:</label>
          <select v-model="selectedStrategy" class="form-select">
            <option value="momentum">Momentum Strategy</option>
            <option value="mean_reversion">Mean Reversion</option>
          </select>
        </div>
        <div class="form-group">
          <label>Timeframe:</label>
          <select v-model="timeframe" class="form-select">
            <option value="1h">1 Hour</option>
            <option value="4h">4 Hour</option>
            <option value="1d">1 Day</option>
          </select>
        </div>
        <button @click="runBacktest" class="run-btn" :disabled="isRunning">
          {{ isRunning ? 'Running...' : 'Run Backtest' }}
        </button>
      </div>
      
      <div v-if="results" class="backtest-results">
        <h4>Results</h4>
        <div class="result-item">
          <span>Total Return:</span>
          <span class="value positive">+12.5%</span>
        </div>
        <div class="result-item">
          <span>Max Drawdown:</span>
          <span class="value negative">-3.2%</span>
        </div>
        <div class="result-item">
          <span>Sharpe Ratio:</span>
          <span class="value">1.8</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  symbol: string
}>()

const selectedStrategy = ref('momentum')
const timeframe = ref('1h')
const isRunning = ref(false)
const results = ref(null)

async function runBacktest() {
  isRunning.value = true
  
  try {
    // Simulate backtest
    await new Promise(resolve => setTimeout(resolve, 2000))
    results.value = { /* mock results */ }
  } catch (error) {
    console.error('Backtest failed:', error)
  } finally {
    isRunning.value = false
  }
}
</script>

<style scoped>
.backtest-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.backtest-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-primary);
}

.backtest-header h3 {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
}

.backtest-content {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 12px;
}

.form-group label {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.symbol-display {
  font-size: 13px;
  font-weight: 500;
  color: var(--accent-blue);
}

.form-select {
  width: 100%;
  padding: 6px 8px;
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: 4px;
  color: var(--text-primary);
  font-size: 12px;
}

.run-btn {
  width: 100%;
  padding: 8px;
  background: var(--accent-blue);
  border: none;
  border-radius: 4px;
  color: white;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 8px;
}

.run-btn:disabled {
  background: var(--bg-hover);
  color: var(--text-secondary);
  cursor: not-allowed;
}

.backtest-results {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-primary);
}

.backtest-results h4 {
  font-size: 13px;
  margin: 0 0 12px 0;
}

.result-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 12px;
}

.value.positive {
  color: var(--accent-green);
}

.value.negative {
  color: var(--accent-red);
}
</style>