
<script setup>
import { ref, onMounted } from 'vue';
import { api } from '../services/api';
import ForecastChart from './ForecastChart.vue';
import PrepPlanTable from './PrepPlanTable.vue';
import OrderList from './OrderList.vue';
import SalesPlanEntry from './SalesPlanEntry.vue';
import BusinessGuide from './BusinessGuide.vue';

const props = defineProps({
    isManager: {
        type: Boolean,
        default: false
    }
});

// Default Demo ID or from URL
const restId = ref(null);
const tab = ref('dashboard'); // 'dashboard' | 'order' | 'plans'
const isGuideOpen = ref(false);

onMounted(async () => {
    const params = new URLSearchParams(window.location.search);
    let rId = params.get('restaurant_id');
    
    // Get user info to find linked restaurant
    try {
        const resp = await api.get('/api/v1/auth/me');
        if (resp.ok) {
            const data = await resp.json();
            // Auth endpoint usually returns user with linked_restaurant_id
            if (!rId && data.linked_restaurant_id) {
                rId = data.linked_restaurant_id;
            } else if (!rId && data.restaurant?.id) {
                rId = data.restaurant.id;
            }
        }
    } catch (e) {
        console.error('Failed to fetch user info for restaurant ID:', e);
    }
    
    if (!rId) {
        // As a final fallback, try to list restaurants and pick the first one
        try {
            const res = await api.get('/api/v1/analytics/restaurants');
            if (res.ok) {
                const list = await res.json();
                if (list.length > 0) rId = list[0].id;
            }
        } catch (e) {
            console.error('Final fallback failed:', e);
        }
    }
    
    restId.value = rId;
    if (rId) {
        fetchSummaryData();
    }
});

const monthPlan = ref('0 ₽');
const todayForecast = ref('0 ₽');
const iikoStatus = ref('Online');
const aiCredits = ref(0);

const fetchSummaryData = async () => {
    if (!restId.value) return;
    try {
        // Fetch forecast vs fact to get monthly plan total
        const resp = await api.get(`/api/v1/analytics/forecast-vs-fact?restaurant_id=${restId.value}`);
        if (resp.ok) {
            const json = await resp.json();
            const total = json.data.reduce((acc, d) => acc + (d.plan || 0), 0);
            monthPlan.value = new Intl.NumberFormat('ru-RU').format(total) + ' ₽';
        }

        // Fetch prep plan for today to get forecast source amount
        const resp2 = await api.get(`/api/v1/analytics/summary?restaurant_id=${restId.value}`);
        if (resp2.ok) {
            const json2 = await resp2.json();
            todayForecast.value = new Intl.NumberFormat('ru-RU').format(json2.plan_source || 0) + ' ₽';
            aiCredits.value = json2.ai_credits || 0;
        }
    } catch (e) {
        console.error('Failed to fetch dashboard summary:', e);
    }
};

</script>

<template>
  <div class="min-h-screen bg-gray-50 font-sans">
    <!-- Navbar -->
    <nav class="bg-white shadow-sm border-b border-gray-100 z-50 sticky top-0">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center space-x-8">
                    <span class="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
                        NeuroSupply
                    </span>
                    
                    <!-- Navigation -->
                    <div class="flex space-x-4">
                        <button 
                            @click="tab = 'dashboard'"
                            :class="tab === 'dashboard' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'"
                            class="px-3 py-2 text-sm font-medium transition-colors"
                        >
                            Обзор
                        </button>
                        <button 
                            @click="tab = 'order'"
                            :class="tab === 'order' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'"
                            class="px-3 py-2 text-sm font-medium transition-colors"
                        >
                            Заявки
                        </button>
                        <button 
                            @click="tab = 'plans'"
                            :class="tab === 'plans' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'"
                            class="px-3 py-2 text-sm font-medium transition-colors"
                        >
                            Планы
                        </button>
                    </div>
                </div>
                
                <!-- Right side: ID & Logout -->
                <div class="flex items-center space-x-4">
                    <div class="hidden lg:block text-xs text-gray-400">
                        Shop ID: {{ restId ? restId.slice(0, 8) : '...' }}
                    </div>
                    
                    <!-- Admin Panel Button for Managers -->
                    <a 
                        v-if="props.isManager"
                        href="/dashboard"
                        class="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-500 transition-all shadow-md shadow-blue-600/20 active:scale-95 border border-blue-400/20"
                    >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.1 0 1.258 0 1.258 0 2.238 1.58.583 0 1.58.558 1.135 1.594l.805.805c.805.805.805.805.805.805 1.036-.445 2.03.552 1.594 1.135l1.58 2.238c1.756.426 1.756 2.924 0 3.35l-1.58 2.238c.436 1.036-.558 2.03-1.135 1.594l-.805.805c-.805.805-.805.805-.805.805-1.036-.445-2.03.552-1.594 1.135l-1.58 2.238c-.426 1.756-2.924 1.756-3.35 0l-2.238-1.58c-1.036.436-2.03-.558-1.594-1.135l-.805-.805c-.805-.805-.805-.805-.805-.805-1.036.445-2.03-.552-1.594-1.135l-2.238-1.58c-1.756-.426-1.756-2.924 0-3.35l1.58-2.238c-.436-1.036.558-2.03 1.135-1.594l.805-.805c.805-.805.805-.805.805-.805 1.036.445 2.03-.552 1.594-1.135l1.58-2.238z" />
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        <span class="text-xs font-bold uppercase tracking-wider">Админ-панель</span>
                    </a>

                    <!-- Help Button -->
                    <button 
                        @click="isGuideOpen = true"
                        class="hidden sm:flex items-center space-x-2 px-3 py-1.5 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors border border-blue-100"
                    >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span class="text-xs font-bold uppercase tracking-wider">Гайд</span>
                    </button>
                    <button 
                        @click="$emit('logout')"
                        class="p-2 text-gray-400 hover:text-red-600 transition-colors rounded-full hover:bg-red-50"
                        title="Выход"
                    >
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    </nav>

    <!-- Content -->
    <main class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 space-y-6">
        
        <!-- Dashboard Tab -->
        <div v-if="tab === 'dashboard'" class="space-y-6">
            <!-- Summary Cards (Placeholder) -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
           <div class="bg-white p-4 md:p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 group cursor-default">
               <div class="text-gray-400 text-[10px] md:text-sm font-bold uppercase tracking-wider group-hover:text-blue-500 transition-colors">План на месяц</div>
               <div class="text-xl md:text-3xl font-black text-gray-900 mt-1">{{ monthPlan }}</div>
               <div class="mt-2 text-[10px] text-gray-400 uppercase tracking-tighter opacity-0 group-hover:opacity-100 transition-opacity">Текущий период</div>
           </div>
           <div class="bg-white p-4 md:p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 group cursor-default">
               <div class="text-gray-400 text-[10px] md:text-sm font-bold uppercase tracking-wider group-hover:text-blue-600 transition-colors">Прогноз (Сегодня)</div>
               <div class="text-xl md:text-3xl font-black text-blue-600 mt-1">{{ todayForecast }}</div>
               <div class="mt-2 flex items-center text-[10px] text-blue-400 uppercase font-bold">
                   <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
                   На базе AI V2.2
               </div>
           </div>
           <div class="bg-white p-4 md:p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 group cursor-default relative overflow-hidden">
               <div class="text-gray-400 text-[10px] md:text-sm font-bold uppercase tracking-wider group-hover:text-indigo-600 transition-colors">NeuroCredits</div>
               <div class="text-xl md:text-3xl font-black text-indigo-600 mt-1 flex items-center">
                   <span class="mr-2">{{ aiCredits }}</span>
                   <span class="text-[8px] md:text-xs bg-indigo-50 text-indigo-600 px-1.5 py-0.5 rounded-full font-bold uppercase tracking-tighter">Active</span>
               </div>
               <div class="absolute -right-2 -bottom-2 opacity-5 group-hover:opacity-20 group-hover:scale-110 transition-all duration-500">
                   <svg class="w-16 h-16 text-indigo-600" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path></svg>
               </div>
           </div>
           <div class="bg-white p-4 md:p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 group cursor-default">
               <div class="text-gray-400 text-[10px] md:text-sm font-bold uppercase tracking-wider group-hover:text-green-600 transition-colors">Статус Iiko</div>
               <div class="flex items-center mt-1">
                   <div class="relative flex h-2 w-2 mr-2">
                     <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                     <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                   </div>
                   <div class="text-xl md:text-3xl font-black text-green-600 uppercase tracking-tighter">{{ iikoStatus }}</div>
               </div>
               <div class="mt-2 text-[10px] text-green-500/60 font-medium uppercase">Синхронизация активна</div>
           </div>
      </div>

            <!-- Charts -->
            <ForecastChart :restaurantId="restId" />
            
            <!-- Prep Plan Table -->
            <PrepPlanTable :restaurantId="restId" />
        </div>

        <!-- Order Tab -->
        <div v-else-if="tab === 'order'">
            <OrderList :restaurantId="restId" :isManager="props.isManager" />
        </div>

        <!-- Plans Tab -->
        <div v-else-if="tab === 'plans'">
            <SalesPlanEntry :restaurantId="restId" />
        </div>
    </main>

    <!-- Interactive Guide Modal -->
    <BusinessGuide :isOpen="isGuideOpen" @close="isGuideOpen = false" />
  </div>
</template>
