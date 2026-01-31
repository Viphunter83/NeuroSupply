<script setup>
import { computed } from 'vue';

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  initialQuantity: {
    type: Number,
    required: true
  }
});

const emit = defineEmits(['update:quantity']);

const isChanged = computed(() => {
  return props.item.quantity !== props.initialQuantity;
});

const updateQuantity = (event) => {
  const newVal = parseInt(event.target.value);
  if (!isNaN(newVal) && newVal >= 0) {
    emit('update:quantity', props.item.id, newVal);
  }
};
</script>

<template>
  <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-4 mb-3">
    <!-- Image Placeholder -->
    <div class="w-16 h-16 bg-gray-200 rounded-lg flex-shrink-0 flex items-center justify-center text-xs text-gray-500 overflow-hidden">
        <img v-if="item.image_url" :src="item.image_url" class="w-full h-full object-cover" alt="Product" />
        <span v-else>No Img</span>
    </div>

    <!-- Content -->
    <div class="flex-1">
      <h3 class="font-bold text-gray-800 text-sm leading-tight">{{ item.product_name }}</h3>
      <p class="text-xs text-gray-500 mt-1">{{ item.product_name_vn || 'Tên tiếng Việt' }}</p>
    </div>

    <!-- Quantity Input -->
    <div class="w-16">
      <input 
        type="number" 
        :value="item.quantity"
        @input="updateQuantity"
        class="w-full text-center border-2 rounded-lg py-2 font-bold text-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        :class="isChanged ? 'bg-yellow-50 border-yellow-400 text-yellow-800' : 'bg-gray-50 border-gray-200 text-gray-800'"
      />
    </div>
  </div>
</template>
