<template>
  <div class="not-found-view">
    <h1>404 - Page Not Found</h1>
    <p>The page you're looking for doesn't exist.</p>
    <router-link to="/" class="home-link">Go to Dashboard</router-link>
  </div>
</template>

<script setup lang="ts">
// 404 Not Found view
</script>

<style scoped>
.not-found-view {
  padding: 2rem;
  text-align: center;
}

.home-link {
  display: inline-block;
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background: #3b82f6;
  color: white;
  text-decoration: none;
  border-radius: 4px;
}

.home-link:hover {
  background: #2563eb;
}
</style>