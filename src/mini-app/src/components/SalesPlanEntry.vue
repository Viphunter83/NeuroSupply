
<script setup>
import { ref, onMounted, computed } from 'vue';
import { api } from '../services/api';

const props = defineProps({
    restaurantId: String
});

const currentMonth = ref(new Date().getMonth() + 1);
const currentYear = ref(new Date().getFullYear());
const plans = ref([]);
const loading = ref(false);
const saving = ref(false);
const message = ref('');

const fetchPlans = async () => {
    loading.value = true;
    try {
        const start = new Date(currentYear.value, currentMonth.value - 1, 1).toISOString().split('T')[0];
        const end = new Date(currentYear.value, currentMonth.value, 0).toISOString().split('T')[0];
        
        const resp = await api.get(`/api/v1/sales-plans/?restaurant_id=${props.restaurantId}&start_date=${start}&end_date=${end}`);
        if (resp.ok) {
            const data = await resp.json();
            // Map existing plans to the month's days
            const daysInMonth = new Date(currentYear.value, currentMonth.value, 0).getDate();
            const newPlans = [];
            for (let d = 1; d <= daysInMonth; d++) {
                // Ensure date is created in local time or UTC consistently
                const date = new Date(currentYear.value, currentMonth.value - 1, d);
                // Simple YYYY-MM-DD
                const dateStr = date.getFullYear() + '-' + 
                              String(date.getMonth() + 1).padStart(2, '0') + '-' + 
                              String(date.getDate()).padStart(2, '0');
                
                const existing = data.find(p => p.date === dateStr);
                newPlans.push({
                    date: dateStr,
                    day: d,
                    amount_rub: existing ? existing.amount_rub : 0
                });
            }
            plans.value = newPlans;
        }
    } catch (e) {
        console.error(e);
    } finally {
        loading.value = false;
    }
};

const savePlans = async () => {
    saving.value = true;
    message.value = '';
    try {
        // Check permissions first (Frontend check)
        const meResp = await api.get('/api/v1/auth/me');
        if (meResp.ok) {
            const userData = await meResp.json();
            if (userData.role !== 'admin' && userData.role !== 'manager') {
                throw new Error('Доступ запрещен: Только Менеджер или Админ могут сохранять планы продаж. (Quyền truy cập bị từ chối: Chỉ Quản lý mới có thể lưu kế hoạch)');
            }
        }

        const payload = {
            plans: plans.value.map(p => ({
                restaurant_id: props.restaurantId,
                date: p.date,
                amount_rub: parseFloat(p.amount_rub)
            }))
        };
        const resp = await api.post('/api/v1/sales-plans/bulk', payload);
        if (resp.ok) {
            message.value = 'Планы успешно сохранены! (Kế hoạch đã được lưu thành công!)';
        } else if (resp.status === 403) {
            throw new Error('У вас недостаточно прав для этого действия. (Bạn không có đủ quyền cho hành động này)');
        } else {
            throw new Error('Ошибка сервера при сохранении. (Lỗi máy chủ khi lưu)');
        }
    } catch (e) {
        message.value = 'Ошибка: ' + e.message;
    } finally {
        saving.value = false;
    }
};

const distributeMonthlyTotal = () => {
    const total = parseFloat(prompt('Введите общую сумму на месяц (₽):'));
    if (isNaN(total)) return;
    
    const daily = Math.round((total / plans.value.length) * 100) / 100;
    plans.value.forEach(p => p.amount_rub = daily);
};

onMounted(fetchPlans);

const totalAmount = computed(() => {
    return plans.value.reduce((sum, p) => sum + (parseFloat(p.amount_rub) || 0), 0);
});

</script>

<template>
    <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <div class="flex justify-between items-center mb-6">
            <div>
                <h2 class="text-xl font-bold text-gray-900">Планирование продаж</h2>
                <p class="text-sm text-gray-500">Укажите ожидаемую выручку по дням</p>
            </div>
            <div class="flex gap-4">
                <button @click="distributeMonthlyTotal" class="text-sm bg-blue-50 text-blue-600 px-4 py-2 rounded-lg font-medium hover:bg-blue-100 transition-colors">
                    Распределить сумму
                </button>
                <button 
                    @click="savePlans" 
                    :disabled="saving"
                    class="bg-blue-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                    {{ saving ? 'Сохранение...' : 'Сохранить всё' }}
                </button>
            </div>
        </div>

        <div v-if="message" :class="message.includes('Ошибка') ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'" class="p-4 rounded-lg mb-6 font-medium">
            {{ message }}
        </div>

        <div v-if="loading" class="text-center py-10">Загрузка плана...</div>
        <div v-else class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
            <div v-for="plan in plans" :key="plan.day" class="p-4 border border-gray-100 rounded-lg hover:border-blue-200 transition-colors">
                <div class="text-[10px] font-bold text-gray-400 uppercase mb-1">{{ plan.date }}</div>
                <div class="flex flex-col">
                    <span class="text-sm font-bold text-gray-700 mb-1">День {{ plan.day }}</span>
                    <input 
                        v-model="plan.amount_rub" 
                        type="number" 
                        class="w-full border border-gray-200 rounded p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                        placeholder="0.00"
                    >
                </div>
            </div>
        </div>

        <div class="mt-8 pt-6 border-t border-gray-100 flex justify-end">
            <div class="text-right">
                <div class="text-sm text-gray-500">Итого за месяц:</div>
                <div class="text-3xl font-black text-blue-600">{{ totalAmount.toLocaleString() }} ₽</div>
            </div>
        </div>
    </div>
</template>
