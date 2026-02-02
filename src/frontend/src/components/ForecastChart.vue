
<script setup>
import { ref, onMounted, computed } from 'vue';
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale
} from 'chart.js'
import { Bar } from 'vue-chartjs'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const props = defineProps({
  restaurantId: String
});

const chartData = ref({
  labels: [],
  datasets: []
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: { position: 'bottom' },
    title: { display: true, text: 'Прогноз vs Факт (RUB)' } // TODO: Localization
  }
};

const loaded = ref(false);

const fetchData = async () => {
    try {
        let url = `/api/v1/analytics/forecast-vs-fact`;
        if (props.restaurantId) {
            url += `?restaurant_id=${props.restaurantId}`;
        }
        
        const res = await fetch(url);
        if (!res.ok) throw new Error("Failed to load chart data");
        const json = await res.json();
        const dataInfo = json.data; // List of {date, plan, fact}

        chartData.value = {
            labels: dataInfo.map(d => d.date.split('-').slice(1).join('.')), // MM.DD
            datasets: [
                {
                    label: 'План',
                    backgroundColor: '#3b82f6', // blue-500
                    data: dataInfo.map(d => d.plan)
                },
                {
                    label: 'Факт (Mock)',
                    backgroundColor: '#10b981', // green-500
                    data: dataInfo.map(d => d.fact)
                }
            ]
        };
        loaded.value = true;
    } catch (e) {
        console.error(e);
    }
};

onMounted(() => {
    fetchData();
});
</script>

<template>
  <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
    <div v-if="!loaded" class="h-64 flex items-center justify-center text-gray-400">Loading Chart...</div>
    <Bar v-else :data="chartData" :options="chartOptions" />
  </div>
</template>
