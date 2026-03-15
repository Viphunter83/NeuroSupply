
<template>
  <div v-if="isOpen" class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-300">
    <div class="bg-white w-full max-w-4xl max-h-[90vh] rounded-3xl shadow-2xl overflow-hidden flex flex-col animate-in zoom-in-95 duration-300">
      <!-- Header -->
      <div class="px-8 py-6 border-b border-gray-100 flex justify-between items-center bg-gradient-to-r from-blue-50 to-indigo-50">
        <div>
          <h2 class="text-2xl font-black text-gray-900 tracking-tight">Гайд по системе NeuroSupply</h2>
          <p class="text-gray-500 text-sm font-medium">Как ИИ трансформирует управление вашим рестораном</p>
        </div>
        <button @click="$emit('close')" class="p-2 hover:bg-white rounded-full transition-colors">
          <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto p-8 space-y-12">
        <!-- Scenario 1: Prediction -->
        <section class="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
          <div class="space-y-4">
            <div class="inline-flex px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-xs font-bold uppercase tracking-wider">Этап 1: Анализ спроса</div>
            <h3 class="text-3xl font-bold text-gray-900 tracking-tighter">🤖 AI Прогнозирование</h3>
            <p class="text-gray-600 leading-relaxed">
              NeuroSupply подключается к <strong>iiko</strong> и анализирует историю продаж за последние 2 года. ИИ учитывает праздники, погоду и день недели, чтобы предсказать выручку на сегодня с точностью до 95%.
            </p>
            <ul class="space-y-2">
              <li class="flex items-center space-x-2 text-sm text-gray-700 font-medium">
                <svg class="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/></svg>
                <span>Авто-синхронизация с iiko Cloud</span>
              </li>
              <li class="flex items-center space-x-2 text-sm text-gray-700 font-medium">
                <svg class="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/></svg>
                <span>Учет внешних факторов (погода, события)</span>
              </li>
            </ul>
          </div>
          <div class="bg-gray-50 rounded-2xl p-6 border border-gray-100 shadow-inner">
            <div class="text-xs font-bold text-gray-400 mb-4 uppercase tracking-widest">Визуализация: График спроса</div>
            <div class="h-32 flex items-end justify-between space-x-2">
              <div v-for="i in [40, 70, 45, 90, 65, 80, 50]" :key="i" :style="{ height: i + '%' }" class="w-full bg-blue-500/20 rounded-t-md relative group">
                <div class="absolute -top-6 left-1/2 -translate-x-1/2 scale-0 group-hover:scale-100 transition-transform bg-gray-900 text-white text-[10px] px-1.5 py-0.5 rounded italic">AI Pred</div>
              </div>
            </div>
            <div class="mt-4 pt-4 border-t border-gray-200 flex justify-between text-[10px] text-gray-400 font-bold">
              <span>ПН</span><span>ВТ</span><span>СР</span><span>ЧТ</span><span>ПТ</span><span class="text-blue-600">СБ</span><span class="text-blue-600">ВС</span>
            </div>
          </div>
        </section>

        <!-- Scenario 2: Prep Plan -->
        <section class="grid grid-cols-1 md:grid-cols-2 gap-8 items-center border-t border-gray-100 pt-12">
          <div class="order-2 md:order-1 bg-gray-900 rounded-2xl p-6 shadow-xl overflow-hidden relative">
            <div class="absolute top-0 right-0 p-4 opacity-10">
              <svg class="w-24 h-24 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M11 9H9V2H7V9H5V2H3V9C3 11.12 4.66 12.84 6.75 12.97V22H9.25V12.97C11.34 12.84 13 11.12 13 9V2H11V9ZM16 6V14h3v8h2.5V2h-5.5C16 4.21 16 6 16 6Z"/></svg>
            </div>
            <div class="space-y-3">
              <div class="flex justify-between items-center text-[10px] text-gray-400 font-bold uppercase tracking-tighter">
                <span>План заготовок (Смена 1)</span>
                <span class="text-green-400">Ready</span>
              </div>
              <div v-for="item in [{n:'Заправка Фо Бо', q:'15.5 л'}, {n:'Говядина су-вид', q:'8.2 кг'}]" :key="item.n" class="flex justify-between items-center p-3 rounded-lg bg-white/5 border border-white/10">
                <span class="text-white text-sm">{{ item.n }}</span>
                <span class="text-blue-400 font-mono text-sm font-bold">{{ item.q }}</span>
              </div>
            </div>
          </div>
          <div class="order-1 md:order-2 space-y-4">
            <div class="inline-flex px-3 py-1 rounded-full bg-purple-100 text-purple-700 text-xs font-bold uppercase tracking-wider">Этап 2: Работа Кухни</div>
            <h3 class="text-3xl font-bold text-gray-900 tracking-tighter">🍳 План заготовок</h3>
            <p class="text-gray-600 leading-relaxed">
              На основе прогноза система автоматически рассчитывает объем заготовок. Повара больше не гадают "сколько нарезать" — они видят точные цифры, основанные на <strong>реальном спросе</strong>.
            </p>
            <p class="text-sm text-purple-600 font-bold">🎯 Результат: Снижение списаний на 15-20% за первый месяц.</p>
          </div>
        </section>

        <!-- Scenario 3: Smart Orders -->
        <section class="grid grid-cols-1 md:grid-cols-2 gap-8 items-center border-t border-gray-100 pt-12">
          <div class="space-y-4">
             <div class="inline-flex px-3 py-1 rounded-full bg-green-100 text-green-700 text-xs font-bold uppercase tracking-wider">Этап 3: Поставки</div>
            <h3 class="text-3xl font-bold text-gray-900 tracking-tighter">📦 Смарт-Заявки</h3>
            <p class="text-gray-600 leading-relaxed">
              Менеджеру больше не нужно тратить 2 часа на инвентаризацию и звонки поставщикам. Система видит остатки в iiko и <strong>сама формирует заказ</strong>.
            </p>
            <div class="p-4 bg-green-50 rounded-xl border border-green-100 flex items-start space-x-3">
              <div class="p-2 bg-green-500 rounded-lg text-white">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7"/></svg>
              </div>
              <div>
                <div class="text-sm font-bold text-green-800">Экономия времени</div>
                <div class="text-xs text-green-700">Заказ формируется в 4 клика вместо 2 часов рутины.</div>
              </div>
            </div>
          </div>
          <div class="relative group cursor-pointer">
            <div class="absolute -inset-1 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl blur opacity-25 group-hover:opacity-100 transition duration-1000 group-hover:duration-200"></div>
            <div class="relative bg-white p-6 rounded-2xl border border-gray-100 shadow-xl space-y-4">
               <div class="flex items-center justify-between">
                 <span class="text-lg font-bold">Новая заявка</span>
                 <span class="text-[10px] bg-blue-100 text-blue-800 px-2 py-0.5 rounded italic">Auto-generated</span>
               </div>
               <div class="space-y-2">
                 <div class="h-2 w-full bg-gray-100 rounded"></div>
                 <div class="h-2 w-3/4 bg-gray-100 rounded"></div>
                 <div class="h-2 w-1/2 bg-gray-100 rounded"></div>
               </div>
               <button class="w-full py-3 bg-blue-600 text-white rounded-xl font-bold shadow-lg shadow-blue-600/30">ПОДТВЕРДИТЬ ЗАКАЗ</button>
            </div>
          </div>
        </section>
      </div>

      <!-- Footer -->
      <div class="px-8 py-6 border-t border-gray-100 bg-gray-50 flex justify-center">
        <button 
          @click="$emit('close')"
          class="px-8 py-3 bg-gray-900 text-white font-bold rounded-xl hover:bg-gray-800 transition-all active:scale-95"
        >
          ПОНЯТНО, К РАБОТЕ!
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  isOpen: Boolean
});

defineEmits(['close']);
</script>

<style scoped>
.animate-in {
  animation-fill-mode: forwards;
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes zoom-in-95 {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
</style>
