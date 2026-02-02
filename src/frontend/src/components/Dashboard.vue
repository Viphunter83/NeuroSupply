
<script setup>
import { ref } from 'vue';
import ForecastChart from './ForecastChart.vue';
import PrepPlanTable from './PrepPlanTable.vue';
import OrderList from './OrderList.vue';

// Default Demo ID or from URL
const getInitialId = () => {
    const params = new URLSearchParams(window.location.search);
    return params.get('restaurant_id') || 'f2c046ab-4068-4794-b6e1-e41045f9ea31';
}

const restId = ref(getInitialId());
const tab = ref('dashboard'); // 'dashboard' | 'order'

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
                            Заказ
                        </button>
                    </div>
                </div>
                
                <!-- ID Display -->
                <div class="flex items-center text-xs text-gray-400">
                    ID: {{ restId.slice(0, 8) }}...
                </div>
            </div>
        </div>
    </nav>

    <!-- Content -->
    <main class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 space-y-6">
        
        <!-- Dashboard Tab -->
        <div v-if="tab === 'dashboard'" class="space-y-6">
            <!-- Summary Cards (Placeholder) -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                 <!-- Just simple placeholders for visual completeness -->
                 <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                     <div class="text-gray-500 text-sm">План на месяц</div>
                     <div class="text-2xl font-bold text-gray-900 mt-1">2.4M ₽</div>
                 </div>
                 <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                     <div class="text-gray-500 text-sm">Прогноз (Сегодня)</div>
                     <div class="text-2xl font-bold text-blue-600 mt-1">85,000 ₽</div>
                 </div>
                 <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                     <div class="text-gray-500 text-sm">Статус Iiko</div>
                     <div class="text-2xl font-bold text-green-500 mt-1">Online</div>
                 </div>
            </div>

            <!-- Charts -->
            <ForecastChart :restaurantId="restId" />
            
            <!-- Prep Plan Table -->
            <PrepPlanTable :restaurantId="restId" />
        </div>

        <!-- Order Tab -->
        <div v-else>
            <OrderList :restaurantId="restId" />
        </div>
    </main>
  </div>
</template>
