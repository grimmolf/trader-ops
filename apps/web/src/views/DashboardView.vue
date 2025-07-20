<template>
  <div class="dashboard-view">
    <h1>Trading Dashboard</h1>
    <p>Web-first TraderTerminal Dashboard</p>
    
    <div class="dashboard-grid">
      <div class="card">
        <h2>Account Overview</h2>
        <p>Account information and metrics</p>
      </div>
      
      <div class="card">
        <h2>Real-Time Data</h2>
        <p>Live market data and quotes</p>
      </div>
      
      <div class="card">
        <h2>Positions</h2>
        <p>Current trading positions</p>
      </div>
      
      <div class="card">
        <h2>Orders</h2>
        <p>Order management and history</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Dashboard view for the TraderTerminal web application
</script>

<style scoped>
.dashboard-view {
  padding: 2rem;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
}

.card {
  background: white;
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.card h2 {
  margin: 0 0 1rem 0;
  color: #1f2937;
}

.card p {
  margin: 0;
  color: #6b7280;
}
</style>