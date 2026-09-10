<template>
  <div class="app-root">
    <div class="lk-aurora" />
    <AppLayout>
      <router-view />
    </AppLayout>
  </div>
</template>

<script setup>
import AppLayout from './layouts/AppLayout.vue'
</script>

<style>
.app-root {
  position: relative;
  min-height: 100vh;
}
</style>
