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

const emit = defineEmits(['update:quantity', 'update:comment']);

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
  <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100 mb-3 transition-colors" :class="isChanged ? 'border-blue-200 bg-blue-50/30' : ''">
    <div class="flex items-center space-x-4">
        <!-- Image Placeholder -->
        <div class="w-16 h-16 bg-gray-200 rounded-lg flex-shrink-0 flex items-center justify-center text-xs text-gray-500 overflow-hidden">
            <img v-if="item.image_url" :src="item.image_url" class="w-full h-full object-cover" alt="Product" />
            <span v-else>No Img</span>
        </div>

        <!-- Content -->
        <div class="flex-1">
        <h3 class="font-bold text-gray-800 text-sm leading-tight">{{ item.product_name }}</h3>
        <p class="text-xs text-gray-500 mt-1">{{ item.unit }}</p>
        </div>

        <!-- Quantity Input -->
        <div class="w-16">
        <input 
            type="number" 
            :value="item.quantity"
            @input="updateQuantity"
            class="w-full text-center border-2 rounded-lg py-2 font-bold text-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            :class="isChanged ? 'bg-white border-blue-400 text-blue-800' : 'bg-gray-50 border-gray-200 text-gray-800'"
        />
        </div>
    </div>

    <!-- Comment Input (Visible ONLY if changed) -->
    <div v-if="isChanged" class="mt-3 pt-3 border-t border-blue-100 anim-slide-down">
        <div class="flex justify-between items-center mb-1">
            <label class="block text-xs font-semibold text-blue-600">Причина изменения / Reason:</label>
            <span class="text-xs text-gray-500 font-medium">План: {{ initialQuantity }} {{ item.unit }}</span>
        </div>
        <input 
            type="text" 
            :value="item.comment || ''"
            @input="$emit('update:comment', item.id, $event.target.value)"
            placeholder="Например/Example: 'На складе 5 кг' (In stock 5kg)"
            class="w-full px-3 py-2 text-sm border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
        />
    </div>
  </div>
</template>

<style scoped>
.anim-slide-down {
    animation: slideDown 0.3s ease-out forwards;
}
@keyframes slideDown {
    from { opacity: 0; transform: translateY(-5px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
