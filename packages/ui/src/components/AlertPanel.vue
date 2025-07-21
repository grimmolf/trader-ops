<template>
  <div class="alert-panel">
    <div class="alerts-header">
      <h3>Active Alerts</h3>
    </div>
    <div class="alerts-list">
      <div v-if="alerts.length === 0" class="no-alerts">
        No active alerts
      </div>
      <div v-for="alert in alerts" :key="alert.id" class="alert-item">
        <div class="alert-info">
          <span class="symbol">{{ alert.symbol }}</span>
          <span class="condition">{{ alert.condition }}</span>
        </div>
        <div class="alert-details">
          <span class="price">${{ alert.price }}</span>
          <button @click="removeAlert(alert.id)" class="remove-btn">×</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  alerts: any[]
}>()

function removeAlert(alertId: string) {
  console.log('Remove alert:', alertId)
  // TODO: Implement alert removal
}
</script>

<style scoped>
.alert-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.alerts-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-primary);
}

.alerts-header h3 {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
}

.alerts-list {
  flex: 1;
  overflow-y: auto;
}

.no-alerts {
  padding: 16px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 12px;
}

.alert-item {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-secondary);
}

.alert-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.alert-details {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
}

.remove-btn {
  background: none;
  border: none;
  color: var(--accent-red);
  cursor: pointer;
  font-size: 14px;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>