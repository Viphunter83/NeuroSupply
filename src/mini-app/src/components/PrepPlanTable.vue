
<script setup>
import { ref, onMounted, watch } from 'vue';
import { api } from '../services/api';

const props = defineProps({
  restaurantId: String
});

const items = ref([]);
const loading = ref(false);
const planAmount = ref(0);

const fetchPlan = async () => {
    loading.value = true;
    try {
        let url = `/api/v1/analytics/prep-plan`;
        if (props.restaurantId) {
            url += `?restaurant_id=${props.restaurantId}`;
        }
        
        const res = await api.get(url);
        if (!res.ok) throw new Error("Failed to load prep plan");
        const json = await res.json();
        
        items.value = json.items; // List of {product_name, quantity, unit, stock, predicted_usage}
        planAmount.value = json.plan_source;
    } catch (e) {
        console.error(e);
    } finally {
        loading.value = false;
    }
};

onMounted(() => {
    fetchPlan();
});

watch(() => props.restaurantId, () => {
    fetchPlan();
});
</script>

<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
    <div class="p-4 border-b border-gray-100 flex justify-between items-center">
        <div>
            <h2 class="font-bold text-gray-800">План заготовок (Лист 2а)</h2>
            <p class="text-xs text-gray-400">На базе плана продаж: {{ planAmount?.toLocaleString() }} ₽</p>
        </div>
        <button @click="fetchPlan" class="text-blue-500 text-sm hover:underline">Обновить</button>
    </div>
    
    <div v-if="loading" class="p-8 text-center text-gray-400">Загрузка...</div>
    
    <div v-else class="overflow-x-auto">
        <table class="w-full text-sm text-left">
            <thead class="bg-gray-50 text-gray-500 uppercase text-xs">
                <tr>
                    <th class="px-4 py-3">Продукт / Ингредиент</th>
                    <th class="px-4 py-3 text-right">Потребность</th>
                    <th class="px-4 py-3 text-right">Остаток</th>
                    <th class="px-4 py-3 text-right">К Заказу</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="item in items" :key="item.product_id" class="border-b hover:bg-gray-50">
                    <td class="px-4 py-3 font-medium text-gray-900">
                        {{ item.product_name }}
                        <div class="text-xs text-gray-400 font-normal">{{ item.product_name_vn }}</div>
                    </td>
                    <td class="px-4 py-3 text-right">
                        {{ item.predicted_usage?.toFixed(2) }} {{ item.unit }}
                    </td>
                    <td class="px-4 py-3 text-right text-yellow-600">
                        {{ item.stock }}
                    </td>
                    <td class="px-4 py-3 text-right font-bold text-blue-600">
                        {{ item.quantity }}
                    </td>
                </tr>
                <tr v-if="items.length === 0" class="text-center">
                    <td colspan="4" class="py-8 text-gray-400">Нет данных для заказа</td>
                </tr>
            </tbody>
        </table>
    </div>
  </div>
</template>
