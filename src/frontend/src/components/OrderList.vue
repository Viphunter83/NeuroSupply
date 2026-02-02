<script setup>
import { ref, onMounted } from 'vue';
import OrderCard from './OrderCard.vue';
import SuccessScreen from './SuccessScreen.vue';

const props = defineProps({
  restaurantId: String
});

const items = ref([]);
const orderId = ref(null);
const loading = ref(true);
const error = ref(null);
const isSuccess = ref(false);
const activeRestaurantId = ref(null);

// Get query params
const getQueryParams = () => {
    const params = new URLSearchParams(window.location.search);
    return params.get('restaurant_id');
}

const fetchOrder = async () => {
    const rId = props.restaurantId || getQueryParams();
    // Fallback ID for testing if not in URL 
    const finalId = rId || 'f2c046ab-4068-4794-b6e1-e41045f9ea31'; // Default Test ID
    activeRestaurantId.value = finalId;

    try {
        const response = await fetch(`/api/v1/order/latest?restaurant_id=${finalId}`);
        if (!response.ok) throw new Error('Failed to fetch order');
        const data = await response.json();
        
        orderId.value = data.id;
        items.value = data.items.map(i => ({
             ...i,
             id: i.product_id, // Map product_id to id for local usage
             quantity: i.quantity,
             original_quantity: i.quantity // Store explicit original
        }));
    } catch (e) {
        error.value = e.message;
    } finally {
        loading.value = false;
    }
};

const handleQuantityUpdate = (productId, newQty) => {
    const item = items.value.find(i => i.id === productId);
    if (item) {
        item.quantity = newQty;
    }
};

const handleCommentUpdate = (productId, comment) => {
    const item = items.value.find(i => i.id === productId);
    if (item) {
        item.comment = comment;
    }
};

const submitOrder = async () => {
    if (!orderId.value) return;

    // Validation: Check for changed items without comments
    const invalidItems = items.value.filter(i => {
        const isChanged = i.quantity !== i.original_quantity;
        const comment = (i.comment || '').trim();
        return isChanged && !comment;
    });

    if (invalidItems.length > 0) {
        alert('Please provide a reason for changing the quantity for: \n' + invalidItems.map(i => i.product_name).join(', '));
        return;
    }
    
    // In a real app we would send the updated items back.
    // The current backend endpoint confirms "as is" or we need to update items first?
    // The user requirement: "POST /api/v1/order/{id}/confirm".
    // It implies we just confirm. But if we changed quantities, we should probably update the order first?
    // MVP: Just confirm (and assume basic flow). 
    // Wait, requirement said: "Если повар меняет число...".
    // If backend only confirms, then changes are LOST.
    // But for this iteration task, let's stick to the requested endpoints.
    try {
        // 1. Save changes (PUT)
        // We need to send full items list as per schema
        const payload = {
            items: items.value.map(i => ({
                product_id: i.product_id,
                product_name: i.product_name,
                product_name_vn: i.product_name_vn,
                image_url: i.image_url,
                unit: i.unit,
                quantity: parseFloat(i.quantity),
                predicted_usage: i.predicted_usage,
                stock: i.stock,
                comment: i.comment || null
            }))
        };

        const updateResponse = await fetch(`/api/v1/order/${orderId.value}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!updateResponse.ok) throw new Error('Failed to update order');

        // 2. Confirm (POST)
        const response = await fetch(`/api/v1/order/${orderId.value}/confirm`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to confirm');
        isSuccess.value = true;
    } catch (e) {
        alert('Error confirming: ' + e.message);
    }
};

onMounted(() => {
    fetchOrder();
});
</script>

<template>
  <div v-if="isSuccess">
      <SuccessScreen :orderId="orderId" />
  </div>
  <div v-else class="min-h-screen bg-gray-50 pb-20">
    <!-- Header -->
    <div class="bg-white p-4 shadow-sm sticky top-0 z-10">
        <h1 class="text-xl font-bold text-gray-800">Review Order / Kiểm tra</h1>
        <p class="text-xs text-gray-500">Shop ID: {{ activeRestaurantId ? activeRestaurantId.slice(0,8) + '...' : 'Unknown' }}</p>
    </div>

    <!-- List -->
    <div class="p-4">
        <div v-if="loading" class="text-center py-10 text-gray-500">Loading...</div>
        <div v-else-if="error" class="text-center py-10 text-red-500">{{ error }}</div>
        
        <div v-else>
            <OrderCard 
                v-for="item in items" 
                :key="item.id" 
                :item="item" 
                :initialQuantity="item.original_quantity"
                @update:quantity="handleQuantityUpdate"
                @update:comment="handleCommentUpdate"
            />
        </div>
    </div>

    <!-- Footer Button -->
    <div class="fixed bottom-0 left-0 right-0 p-4 bg-white border-t border-gray-200">
        <button 
            @click="submitOrder"
            class="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-4 rounded-xl shadow-lg text-lg transition-colors flex flex-col items-center leading-none"
        >
            <span>Подтвердить</span>
            <span class="text-xs opacity-80 font-normal mt-1">Xác nhận</span>
        </button>
    </div>
  </div>
</template>
