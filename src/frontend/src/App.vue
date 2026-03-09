<script setup>
import { computed } from 'vue'
import OrderList from './components/OrderList.vue'
import Dashboard from './components/Dashboard.vue'

const rawUrl = window.location.href
const isManager = computed(() => rawUrl.includes('/manager') || rawUrl.includes('view=manager'))
</script>

<template>
  <Dashboard v-if="isManager" :isManager="true" />
  <OrderList v-else />
</template>
