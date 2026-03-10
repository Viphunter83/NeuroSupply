<script setup>
import { ref, onMounted } from 'vue';
import OrderCard from './OrderCard.vue';
import SuccessScreen from './SuccessScreen.vue';

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

// Restaurant Selection State
const restaurants = ref([]);
const isSelectingRestaurant = ref(false);

const getQueryParams = () => {
    const params = new URLSearchParams(window.location.search);
    return params.get('restaurant_id');
}

const fetchWithAuth = async (url, options = {}) => {
    const headers = { ...options.headers };
    if (window.Telegram?.WebApp?.initData) {
        headers['X-Telegram-Init-Data'] = window.Telegram.WebApp.initData;
    } else if (import.meta.env.DEV) {
        headers['X-Dev-User-Id'] = '1'; // Default for local dev
    }
    return fetch(url, { ...options, headers });
};

const fetchOrder = async () => {
    const queryRid = getQueryParams();
    let rId = props.restaurantId || queryRid;
    
    if (!rId) {
        // Try to get from /me
        try {
            const meResp = await fetchWithAuth('/api/v1/auth/me');
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
            const resp = await fetchWithAuth('/api/v1/analytics/restaurants');
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
        const response = await fetchWithAuth(`/api/v1/orders/latest?restaurant_id=${rId}`);
        if (response.status === 404) {
            isDone.value = true;
            loading.value = false;
            return;
        }
        if (!response.ok) throw new Error('Failed to fetch order');
        const data = await response.json();
        
        orderId.value = data.id;
        orderStatus.value = data.status;

        // If cook opens verified order, show success/waiting screen
        if (!props.isManager && data.status === 'verified_by_cook') {
            isSuccess.value = true;
            loading.value = false;
            return;
        }

        // If order is already approved, show done screen
        if (data.status === 'approved_by_manager' || data.status === 'exported_to_procob') {
            isDone.value = true;
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
        error.value = e.message;
    } finally {
        loading.value = false;
    }
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
            const response = await fetchWithAuth(`/api/v1/orders/${orderId.value}/approve`, {
                method: 'POST'
            });
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

        const updateResponse = await fetchWithAuth(`/api/v1/orders/${orderId.value}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!updateResponse.ok) throw new Error('Failed to update order');

        // 2. Confirm (POST)
        const response = await fetchWithAuth(`/api/v1/orders/${orderId.value}/confirm`, {
            method: 'POST'
        });
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
        const response = await fetchWithAuth(`/api/v1/products/extra${query}`);
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
    window.location.search = `?restaurant_id=${id}`;
};

onMounted(() => {
    fetchOrder();
});
</script>

<template>
  <div v-if="isSuccess">
      <SuccessScreen :orderId="orderId" />
  </div>
  <div v-else-if="isDone" class="min-h-screen bg-green-50 flex flex-col items-center justify-center p-6 text-center">
      <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
          <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
      </div>
      <h2 class="text-2xl font-bold text-green-800 mb-2">Отлично! / Tuyệt vời!</h2>
      <p class="text-green-600 font-medium">✅ На сегодня заказы и планы посчитаны, отдыхайте!</p>
      <p class="text-sm text-green-500 mt-2">Đã kiểm kê xong cho hôm nay.</p>
  </div>
  <div v-else class="min-h-screen bg-gray-50 pb-20">
    <!-- Header -->
    <div class="bg-white p-4 shadow-sm sticky top-0 z-10">
        <h1 class="text-xl font-bold text-gray-800">Дневной остаток / Kiểm tra hàng</h1>
        <p class="text-xs text-gray-500">Shop ID: {{ activeRestaurantId ? activeRestaurantId.slice(0,8) + '...' : 'Unknown' }}</p>
    </div>

    <!-- List -->
    <div class="p-4">
        <div v-if="loading" class="text-center py-10 text-gray-500">Loading...</div>
        <div v-else-if="isSelectingRestaurant" class="flex flex-col gap-4 py-6">
            <h2 class="text-lg font-bold text-center">Выберите ресторан / Chọn nhà hàng</h2>
            <div 
                v-for="rest in restaurants" 
                :key="rest.id"
                @click="selectRestaurant(rest.id)"
                class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex items-center justify-between hover:bg-gray-50 transition-colors cursor-pointer active:scale-95"
            >
                <div>
                   <span class="font-bold text-gray-800">{{ rest.name }}</span>
                   <p class="text-xs text-gray-400">ID: {{ rest.id.slice(0,8) }}</p>
                </div>
                <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
            </div>
            <div v-if="restaurants.length === 0" class="text-center text-gray-400">Нет доступных ресторанов</div>
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
  </div>
</template>
