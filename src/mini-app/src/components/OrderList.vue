<script setup>
import { ref, onMounted } from 'vue';
import OrderCard from './OrderCard.vue';
import SuccessScreen from './SuccessScreen.vue';
import { api } from '../services/api';

const props = defineProps({
  restaurantId: String,
  isManager: Boolean
});

const items = ref([]);
const orderId = ref(null);
const orderStatus = ref(null); // Save status from backend
const loading = ref(true);
const error = ref(null);
const isSuccess = ref(false);
const isDone = ref(false);
const activeRestaurantId = ref(null);

// Extra Items Modal State
const isExtraModalOpen = ref(false);
const extraItems = ref([]);
const extraSearchQuery = ref('');
const isExtraLoading = ref(false);

// Help Modal State
const isHelpModalOpen = ref(false);

// Onboarding State
const isFirstVisit = ref(false);
const showOnboarding = ref(false);

const closeOnboarding = () => {
    showOnboarding.value = false;
    localStorage.setItem('neurosupply_onboarded', 'true');
};

const openHelp = () => {
    isHelpModalOpen.value = true;
};
const closeHelp = () => {
    isHelpModalOpen.value = false;
};

const reloadPage = () => {
    window.location.reload();
};

const getQueryParams = () => {
    const params = new URLSearchParams(window.location.search);
    return params.get('restaurant_id');
}

const fetchOrder = async () => {
    const queryRid = getQueryParams();
    const storageRid = localStorage.getItem('neurosupply_restaurant_id');
    let rId = props.restaurantId || queryRid || storageRid;
    
    if (!rId) {
        // Try to get from /me
        try {
            const meResp = await api.get('/api/v1/auth/me');
            if (meResp.ok) {
                const meData = await meResp.json();
                if (meData.restaurant?.id) {
                    rId = meData.restaurant.id;
                }
            }
        } catch (e) {
            console.error('Failed to fetch /me', e);
        }
    }

    if (!rId) {
        // Instead of error, let's fetch list of restaurants
        isSelectingRestaurant.value = true;
        try {
            const resp = await api.get('/api/v1/analytics/restaurants');
            if (resp.ok) {
                restaurants.value = await resp.json();
            }
        } catch (e) {
            error.value = 'Failed to load restaurants';
        } finally {
            loading.value = false;
        }
        return;
    }
    activeRestaurantId.value = rId;

    try {
        const response = await api.get(`/api/v1/orders/latest?restaurant_id=${rId}`);
        if (response.status === 404) {
            isDone.value = true;
            loading.value = false;
            return;
        }
        if (!response.ok) throw new Error('Failed to fetch order');
        if (!response.ok && response.status !== 404) throw new Error('Failed to fetch order');
        
        const data = response.status === 404 ? null : await response.json();

        if (response.status === 404 || (data && (data.status === 'approved_by_manager' || data.status === 'exported_to_procob'))) {
            // Check if we are in demo mode to show mock data instead of "Done"
            if (rId === '00000000-0000-0000-0000-000000000000') {
                useMockData();
                return;
            }
            isDone.value = true;
            loading.value = false;
            return;
        }
        
        orderId.value = data.id;
        orderStatus.value = data.status;

        // If cook opens verified order, show success/waiting screen
        if (!props.isManager && data.status === 'verified_by_cook') {
            isSuccess.value = true;
            loading.value = false;
            return;
        }

        items.value = data.items.map(i => ({
             ...i,
             id: i.product_id, // Map product_id to id for local usage
             original_quantity: parseFloat(i.quantity),
             original_stock: parseFloat(i.stock)
        }));
    } catch (e) {
        error.value = `Ошибка загрузки заказа (Error: ${e.message}). Пожалуйста, попробуйте обновить страницу.`;
        console.error('Fetch error:', e);
        // Fallback for demo if network fails
        if (activeRestaurantId.value === '00000000-0000-0000-0000-000000000000') {
            useMockData();
        }
    } finally {
        loading.value = false;
    }
};

const useMockData = () => {
    console.log("Using Mock Data for Demo...");
    isDone.value = false;
    items.value = [
        { 
            product_id: 'm1', 
            id: 'm1',
            product_name: 'Мясо (говядина) для Фо Бо', 
            product_name_vn: 'Thịt bò Phở', 
            image_url: '/demo/beef.png',
            unit: 'кг', 
            recommended: 15.0, 
            predicted_usage: 14.5,
            stock: 2.5, 
            comment: '', 
            original_stock: 2.5,
            original_quantity: 12.5,
            insight: 'AI: Ожидается рост спроса на Фо Бо на 20% в пятницу вечером.'
        },
        { 
            product_id: 'm2', 
            id: 'm2',
            product_name: 'Лапша рисовая (Bánh phở)', 
            product_name_vn: 'Bánh phở tươi', 
            image_url: '/demo/noodles.png',
            unit: 'кг', 
            recommended: 40, 
            predicted_usage: 38,
            stock: 5, 
            comment: '', 
            original_stock: 5,
            original_quantity: 35,
            insight: 'AI: Критический остаток. Лапши хватит только на обеденную смену.'
        },
        { 
            product_id: 'm3', 
            id: 'm3',
            product_name: 'Зелень микс (кинза, лук)', 
            product_name_vn: 'Rau thơm (ngò, hành)', 
            image_url: '/demo/herbs.png',
            unit: 'кг', 
            recommended: 8, 
            predicted_usage: 7.5,
            stock: 1.2, 
            comment: '', 
            original_stock: 1.2,
            original_quantity: 6.8,
            insight: 'AI: Рекомендуется заказ сегодня, чтобы сохранить свежесть к выходным.'
        }
    ];
    loading.value = false;
};

const handleStockUpdate = (productId, newStock) => {
    const item = items.value.find(i => i.id === productId);
    if (item) {
        item.stock = newStock;
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

    // IF MANAGER -> APPROVE FLOW
    if (props.isManager && orderStatus.value === 'verified_by_cook') {
        try {
            const response = await api.post(`/api/v1/orders/${orderId.value}/approve`);
            if (!response.ok) throw new Error('Failed to approve');
            isSuccess.value = true;
            return;
        } catch (e) {
            alert('Error approving: ' + e.message);
            return;
        }
    }

    // IF COOK/DRAFT -> CONFIRM FLOW
    // Validation: Check for changed items without comments
    const invalidItems = items.value.filter(i => {
        const isChanged = i.stock !== i.original_stock;
        const comment = (i.comment || '').trim();
        return isChanged && !comment;
    });

    if (invalidItems.length > 0) {
        alert('Please provide a reason for changing the quantity for: \n' + invalidItems.map(i => i.product_name).join(', '));
        return;
    }
    
    try {
        // 1. Save changes (PUT)
        const payload = {
            items: items.value.map(i => {
                const stockDiff = i.original_stock - i.stock;
                const newQuantity = Math.max(0, i.original_quantity + stockDiff);
                return {
                    product_id: i.product_id,
                    product_name: i.product_name,
                    product_name_vn: i.product_name_vn,
                    image_url: i.image_url,
                    unit: i.unit,
                    quantity: newQuantity,
                    predicted_usage: i.predicted_usage,
                    stock: i.stock,
                    comment: i.comment || null
                };
            })
        };

        const updateResponse = await api.put(`/api/v1/orders/${orderId.value}`, payload);
        
        if (!updateResponse.ok) throw new Error('Failed to update order');

        // 2. Confirm (POST)
        const response = await api.post(`/api/v1/orders/${orderId.value}/confirm`);
        if (!response.ok) throw new Error('Failed to confirm');
        isSuccess.value = true;
    } catch (e) {
        alert('Error confirming: ' + e.message);
    }
};

let extraSearchTimeout = null;
const fetchExtraItems = async () => {
    isExtraLoading.value = true;
    try {
        const query = extraSearchQuery.value ? `?q=${encodeURIComponent(extraSearchQuery.value)}` : '';
        const response = await api.get(`/api/v1/products/extra${query}`);
        if (!response.ok) throw new Error('Failed to fetch extra products');
        extraItems.value = await response.json();
    } catch (e) {
        console.error(e);
    } finally {
        isExtraLoading.value = false;
    }
};

const handleExtraSearchInput = () => {
    clearTimeout(extraSearchTimeout);
    extraSearchTimeout = setTimeout(() => {
        fetchExtraItems();
    }, 300);
};

const openExtraModal = () => {
    isExtraModalOpen.value = true;
    if (extraItems.value.length === 0) {
        fetchExtraItems();
    }
};

const closeExtraModal = () => {
    isExtraModalOpen.value = false;
};

const addExtraItem = (extraItem) => {
    // Check if already added
    const existing = items.value.find(i => i.id === extraItem.product_id);
    if (existing) {
        alert('Этот товар уже есть в списке.');
        return;
    }
    
    // Append to main items list as anomaly (0 predicted, 0 stock initially)
    items.value.push({
        id: extraItem.product_id,
        product_id: extraItem.product_id,
        product_name: extraItem.product_name,
        product_name_vn: extraItem.product_name_vn,
        image_url: null,
        unit: extraItem.unit,
        quantity: 0,
        predicted_usage: 0,
        stock: 0,
        original_stock: 0,
        original_quantity: 0,
        comment: ''
    });
    
    closeExtraModal();
    // Scroll to bottom so they see it
    setTimeout(() => window.scrollTo(0, document.body.scrollHeight), 100);
};

const selectRestaurant = (id) => {
    isSelectingRestaurant.value = false;
    loading.value = true;
    localStorage.setItem('neurosupply_restaurant_id', id);
    window.location.search = `?restaurant_id=${id}`;
};

const enterDemoMode = () => {
    isSelectingRestaurant.value = false;
    loading.value = true;
    // Redirect to a specific demo ID OR just mock locally
    window.location.search = `?restaurant_id=00000000-0000-0000-0000-000000000000`;
};

onMounted(() => {
    fetchOrder();
    
    // Check onboarding
    if (!localStorage.getItem('neurosupply_onboarded')) {
        showOnboarding.value = true;
    }
});
</script>

<template>
  <div v-if="isSuccess">
      <SuccessScreen :orderId="orderId" />
  </div>
    <div v-else-if="isDone" class="min-h-screen flex flex-col items-center justify-center p-8 text-center bg-green-50">
        <div class="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-6">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
            </svg>
        </div>
        <h2 class="text-3xl font-black text-green-900 mb-2">Отлично! / Tuyệt vời!</h2>
        <p class="text-green-700 font-medium mb-1">На сегодня заказы и планы посчитаны, отдыхайте!</p>
        <p class="text-green-600 text-sm mb-8 italic">Đã kiểm kê xong cho hôm nay.</p>
        
        <button @click="useMockData" class="text-sm font-bold text-blue-600 hover:underline">
            🔄 Показать демо-данные (для презентации)
        </button>
    </div>
  <div v-else class="min-h-screen bg-gray-50 pb-20">
    <!-- Header -->
    <div class="bg-white p-4 shadow-sm sticky top-0 z-10 border-b border-gray-100">
        <div class="flex justify-between items-start">
            <div>
                <h1 class="text-xl font-black text-gray-900 leading-tight">Дневной остаток<br><span class="text-blue-600 text-sm font-bold">Kiểm tra hàng</span></h1>
                <p class="text-[10px] text-gray-400 mt-1 uppercase tracking-wider font-semibold">Shop ID: {{ activeRestaurantId ? activeRestaurantId.slice(0,8) + '...' : 'Unknown' }} | v2.1.2</p>
            </div>
            <div class="flex items-center gap-2">
                <button @click="openHelp" class="p-2 bg-blue-50 text-blue-600 rounded-full hover:bg-blue-100 transition-colors">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                </button>
                <button @click="reloadPage" class="p-2 bg-gray-50 text-gray-400 rounded-full hover:bg-gray-100 transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                </button>
                <div class="bg-blue-50 text-blue-600 px-2 py-1 rounded text-[10px] font-bold uppercase tracking-tighter">
                    Live
                </div>
            </div>
        </div>
    </div>

    <!-- List -->
    <div class="p-4">
        <div v-if="loading" class="text-center py-20">
            <div class="inline-block w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
            <p class="text-gray-400 font-medium">Загрузка данных...</p>
        </div>
        <div v-else-if="isSelectingRestaurant" class="flex flex-col gap-6 py-6 pb-20 justify-center min-h-[60vh]">
            <div class="text-center space-y-2 mb-4">
                <div class="inline-flex p-3 bg-blue-50 rounded-full text-blue-600 mb-2">
                    <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path></svg>
                </div>
                <h2 class="text-2xl font-black text-gray-900 leading-tight">Добро пожаловать!<br><span class="text-blue-600">NeuroSupply</span></h2>
                <p class="text-gray-500 text-sm">Выберите ресторан для начала работы / Chọn nhà hàng</p>
            </div>

            <div class="space-y-3">
                <div 
                    v-for="rest in restaurants" 
                    :key="rest.id"
                    @click="selectRestaurant(rest.id)"
                    class="bg-white p-5 rounded-2xl border border-gray-100 shadow-md hover:shadow-xl hover:border-blue-200 transition-all cursor-pointer active:scale-95 group"
                >
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-4">
                            <div class="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center text-gray-400 group-hover:bg-blue-50 group-hover:text-blue-600 transition-colors capitalize">
                                {{ rest.name[0] }}
                            </div>
                            <div>
                               <span class="font-bold text-gray-900 group-hover:text-blue-700 transition-colors">{{ rest.name }}</span>
                               <p class="text-[10px] text-gray-400 font-mono mt-0.5">{{ rest.id }}</p>
                            </div>
                        </div>
                        <div class="w-8 h-8 rounded-full bg-gray-50 flex items-center justify-center text-gray-300 group-hover:bg-blue-600 group-hover:text-white transition-all">
                             <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
                        </div>
                    </div>
                </div>
            </div>

            <div v-if="restaurants.length === 0" class="text-center py-10 space-y-4">
                <div class="bg-amber-50 rounded-2xl p-6 border border-amber-100">
                    <p class="text-amber-800 text-sm font-bold mb-2">Активные рестораны не найдены</p>
                    <p class="text-amber-600 text-xs leading-relaxed">
                        Ваш аккаунт еще не привязан ни к одному ресторану. Пожалуйста, свяжитесь с администратором или Шеф-поваром вашей точки для настройки доступа.
                    </p>
                </div>
                <p class="text-gray-400 text-xs">Или попробуйте возможности системы прямо сейчас:</p>
            </div>

            <div class="mt-8 border-t border-gray-100 pt-8 text-center">
                 <button 
                    @click="enterDemoMode"
                    class="inline-flex items-center gap-2 text-sm font-bold text-blue-600 hover:text-blue-800 transition-colors px-6 py-2 bg-blue-50 rounded-full"
                 >
                    🚀 Запустить в демо-режиме (Chế độ demo)
                 </button>
            </div>
        </div>
        <div v-else-if="error" class="text-center py-10 text-red-500">{{ error }}</div>
        
        <div v-else>
            <OrderCard 
                v-for="item in items" 
                :key="item.id" 
                :item="item" 
                :initialStock="item.original_stock"
                @update:stock="handleStockUpdate"
                @update:comment="handleCommentUpdate"
            />
        </div>
    </div>

    <!-- Footer Buttons -->
    <div class="fixed bottom-0 left-0 right-0 p-4 bg-white border-t border-gray-200 z-10 flex flex-col gap-3">
        <button 
            @click="openExtraModal"
            class="w-full bg-white border-2 border-green-600 outline-none text-green-700 font-bold py-3 rounded-xl text-lg transition-colors flex justify-center items-center gap-2"
            type="button"
        >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path></svg>
            <span>Доп. заказ / Đặt thêm</span>
        </button>
        <button 
            @click="submitOrder"
            class="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-4 rounded-xl shadow-lg text-lg transition-colors flex flex-col items-center leading-none"
        >
            <span v-if="isManager && orderStatus === 'verified_by_cook'">Утвердить заказ</span>
            <span v-else>Подтвердить</span>
            
            <span v-if="isManager && orderStatus === 'verified_by_cook'" class="text-xs opacity-80 font-normal mt-1">Phê duyệt đơn hàng</span>
            <span v-else class="text-xs opacity-80 font-normal mt-1">Xác nhận</span>
        </button>
    </div>

    <!-- Extra Items Slide-over Modal -->
    <div v-if="isExtraModalOpen" class="fixed inset-0 z-50 flex justify-end">
        <!-- Backdrop -->
        <div class="fixed inset-0 bg-black/40 backdrop-blur-sm transition-opacity" @click="closeExtraModal"></div>
        
        <!-- Drawer Panel -->
        <div class="relative w-full max-w-md bg-white h-full shadow-2xl flex flex-col transform transition-transform duration-300 translate-x-0 rounded-l-2xl">
            <!-- Modal Header -->
            <div class="flex items-center justify-between p-4 border-b border-gray-100">
                <div>
                    <h2 class="text-lg font-bold text-gray-800">Доп. товары</h2>
                    <p class="text-xs text-gray-500">Hàng ngoài danh sách</p>
                </div>
                <button @click="closeExtraModal" class="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100 transition-colors">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
            </div>
            
            <!-- Search Input -->
            <div class="p-4 border-b border-gray-100 bg-gray-50">
                <div class="relative">
                    <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <svg class="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" /></svg>
                    </div>
                    <input 
                        v-model="extraSearchQuery" 
                        @input="handleExtraSearchInput"
                        type="text" 
                        class="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm" 
                        placeholder="Поиск товара / Tìm kiếm..."
                    >
                </div>
            </div>

            <!-- Items List -->
            <div class="flex-1 overflow-y-auto p-4 space-y-3">
                <div v-if="isExtraLoading" class="text-center py-6 text-gray-400">Загрузка...</div>
                <div v-else-if="extraItems.length === 0" class="text-center py-6 text-gray-400">Ничего не найдено</div>
                <template v-else>
                    <div 
                        v-for="eItem in extraItems" 
                        :key="eItem.product_id"
                        class="flex justify-between items-center p-3 border border-gray-100 bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow"
                    >
                        <div class="flex-1 pr-3">
                            <h3 class="text-sm font-bold text-gray-800">{{ eItem.product_name }}</h3>
                            <p v-if="eItem.product_name_vn" class="text-xs text-green-700 font-medium">{{ eItem.product_name_vn }}</p>
                            <span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-gray-100 text-gray-800 mt-1">
                                {{ eItem.unit }}
                            </span>
                        </div>
                        <button 
                            @click="addExtraItem(eItem)"
                            class="flex-shrink-0 w-10 h-10 bg-green-50 text-green-600 rounded-full flex items-center justify-center hover:bg-green-100 transition-colors"
                        >
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path></svg>
                        </button>
                    </div>
                </template>
            </div>
        </div>
    </div>

    <!-- Onboarding Overlay -->
    <div v-if="showOnboarding" class="fixed inset-0 z-[100] flex items-center justify-center p-6 sm:p-10">
        <div class="absolute inset-0 bg-blue-900/60 backdrop-blur-md" @click="closeOnboarding"></div>
        <div class="relative bg-white w-full max-w-sm rounded-[32px] overflow-hidden shadow-2xl transform transition-all animate-in fade-in zoom-in duration-300">
            <div class="bg-blue-600 p-8 text-center text-white relative">
                <div class="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
                    <svg viewBox="0 0 100 100" class="w-full h-full"><circle cx="50" cy="50" r="40" stroke="currentColor" stroke-width="0.5" fill="none" /></svg>
                </div>
                <div class="w-20 h-20 bg-white/20 rounded-3xl mx-auto mb-6 flex items-center justify-center backdrop-blur-sm border border-white/30 rotate-3">
                    <span class="text-4xl">🤖</span>
                </div>
                <h2 class="text-2xl font-black mb-2 leading-tight">Добро пожаловать в NeuroSupply!</h2>
                <p class="text-blue-100 text-sm font-medium">Ваш интеллектуальный помощник в закупках</p>
            </div>
            <div class="p-8">
                <div class="space-y-6">
                    <div class="flex gap-4">
                        <div class="w-10 h-10 rounded-full bg-blue-50 flex-shrink-0 flex items-center justify-center text-blue-600 font-bold">1</div>
                        <div>
                            <h4 class="font-bold text-gray-900 text-sm">AI Анализ</h4>
                            <p class="text-xs text-gray-500 mt-0.5">Система проанализировала продажи и остатки в iIko за вас.</p>
                        </div>
                    </div>
                    <div class="flex gap-4">
                        <div class="w-10 h-10 rounded-full bg-blue-50 flex-shrink-0 flex items-center justify-center text-blue-600 font-bold">2</div>
                        <div>
                            <h4 class="font-bold text-gray-900 text-sm">Умные рекомендации</h4>
                            <p class="text-xs text-gray-500 mt-0.5">В каждом товаре вы увидите "Прогноз AI" и обоснование заказа.</p>
                        </div>
                    </div>
                    <div class="flex gap-4">
                        <div class="w-10 h-10 rounded-full bg-blue-50 flex-shrink-0 flex items-center justify-center text-blue-600 font-bold">3</div>
                        <div>
                            <h4 class="font-bold text-gray-900 text-sm">Подтверждение</h4>
                            <p class="text-xs text-gray-500 mt-0.5">Вам остается только проверить остатки и нажать одну кнопку.</p>
                        </div>
                    </div>
                </div>
                
                <button 
                    @click="closeOnboarding"
                    class="w-full bg-blue-600 hover:bg-blue-700 text-white font-black py-4 rounded-2xl mt-10 shadow-lg shadow-blue-200 transition-all active:scale-95"
                >
                    ПОНЯТНО, НАЧНЕМ! 🚀
                </button>
            </div>
        </div>
    </div>

    <!-- Help Modal -->
    <div v-if="isHelpModalOpen" class="fixed inset-0 z-[110] flex items-center justify-center p-6 sm:p-10">
        <div class="absolute inset-0 bg-gray-900/60 backdrop-blur-sm" @click="closeHelp"></div>
        <div class="relative bg-white w-full max-w-md rounded-[32px] overflow-hidden shadow-2xl animate-in fade-in zoom-in duration-200 flex flex-col max-h-[90vh]">
            <div class="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                <div>
                    <h2 class="text-xl font-black text-gray-900">Инструкция</h2>
                    <p class="text-xs text-gray-500 font-medium">Hướng dẫn sử dụng</p>
                </div>
                <button @click="closeHelp" class="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
            </div>
            
            <div class="p-6 overflow-y-auto space-y-8">
                <section>
                    <h3 class="font-black text-blue-600 uppercase text-xs tracking-widest mb-4">Для Повара (Đầu bếp)</h3>
                    <div class="space-y-4">
                        <div class="flex gap-4">
                            <div class="w-8 h-8 rounded-lg bg-blue-50 flex-shrink-0 flex items-center justify-center text-blue-600 font-bold text-sm">1</div>
                            <p class="text-sm text-gray-600 font-medium leading-tight">Проверьте текущие остатки на складе и введите их в поле "Остаток".</p>
                        </div>
                        <div class="flex gap-4">
                            <div class="w-8 h-8 rounded-lg bg-blue-50 flex-shrink-0 flex items-center justify-center text-blue-600 font-bold text-sm">2</div>
                            <p class="text-sm text-gray-600 font-medium leading-tight">Система автоматически изменит "К заказу" на основе вашего ввода.</p>
                        </div>
                        <div class="flex gap-4">
                            <div class="w-8 h-8 rounded-lg bg-blue-50 flex-shrink-0 flex items-center justify-center text-blue-600 font-bold text-sm">3</div>
                            <p class="text-sm text-gray-600 font-medium leading-tight">Нажмите зеленую кнопку "Подтвердить" внизу экрана.</p>
                        </div>
                    </div>
                </section>

                <section class="pt-4 border-t border-gray-100">
                    <h3 class="font-black text-indigo-600 uppercase text-xs tracking-widest mb-4">Для Менеджера (Quản lý)</h3>
                    <div class="space-y-4">
                        <div class="flex gap-4">
                            <div class="w-8 h-8 rounded-lg bg-indigo-50 flex-shrink-0 flex items-center justify-center text-indigo-600 font-bold text-sm">1</div>
                            <p class="text-sm text-gray-600 font-medium leading-tight">Проверьте заголовок заказа. Он должен быть в статусе "Проверено поваром".</p>
                        </div>
                        <div class="flex gap-4">
                            <div class="w-8 h-8 rounded-lg bg-indigo-50 flex-shrink-0 flex items-center justify-center text-indigo-600 font-bold text-sm">2</div>
                            <p class="text-sm text-gray-600 font-medium leading-tight">Нажмите "Утвердить заказ", чтобы отправить его поставщикам.</p>
                        </div>
                    </div>
                </section>

                <div class="bg-gray-50 p-4 rounded-2xl flex items-start gap-3">
                    <span class="text-xl">💡</span>
                    <p class="text-xs text-gray-500 italic leading-relaxed">
                        Совет: Если нужного товара нет в списке, используйте кнопку "Доп. заказ", чтобы добавить его вручную.
                    </p>
                </div>
            </div>
            
            <div class="p-6 border-t border-gray-100 bg-white">
                <button 
                    @click="closeHelp"
                    class="w-full bg-gray-900 text-white font-black py-4 rounded-2xl shadow-lg active:scale-95 transition-all outline-none"
                >
                    ПОНЯТНО
                </button>
            </div>
        </div>
    </div>
  </div>
</template>
