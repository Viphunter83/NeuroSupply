<script setup>
const props = defineProps({
  orderId: {
    type: String,
    required: true
  }
});

const downloadExcel = () => {
  if (!props.orderId) return;
  window.open(`/api/v1/orders/${props.orderId}/export/excel`, '_blank');
};
</script>

<template>
  <div class="fixed inset-0 bg-green-500 flex flex-col items-center justify-center text-white z-50">
    <div class="bg-white text-green-500 rounded-full p-4 mb-4 shadow-lg">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
      </svg>
    </div>
    <h1 class="text-2xl font-bold mb-2">Отлично!</h1>
    <p class="text-center opacity-90 mb-6">Заказ подтвержден.</p>
    
    <button 
      @click="downloadExcel"
      class="bg-white text-green-600 font-bold py-3 px-6 rounded-xl shadow-md flex items-center space-x-2 hover:bg-gray-100 transition-colors"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
      </svg>
      <span>Скачать Excel</span>
    </button>
  </div>
</template>
