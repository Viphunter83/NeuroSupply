<template>
  <div v-if="loading" class="min-h-screen bg-neutral-900 flex items-center justify-center">
    <div class="flex flex-col items-center space-y-6 animate-pulse">
      <div class="w-16 h-16 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
      <div class="text-blue-500 font-medium tracking-widest text-sm uppercase">Инициализация AI платформы...</div>
    </div>
  </div>
  
  <div v-else class="min-h-screen bg-neutral-900">
    <!-- Landing / Login state -->
    <template v-if="!user">
      <div v-if="!showLogin" class="min-h-screen bg-[#050505] relative overflow-hidden flex flex-col items-center justify-center p-6">
        <!-- Background Glows -->
        <div class="absolute top-0 left-0 w-full h-full">
          <div class="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/10 blur-[120px] rounded-full"></div>
          <div class="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-600/10 blur-[120px] rounded-full"></div>
        </div>

        <!-- Static Header -->
        <header class="absolute top-0 w-full p-4 md:p-6 flex justify-between items-center z-20">
          <div class="flex items-center space-x-2">
            <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-black text-white text-xs">NS</div>
            <span class="text-white font-bold tracking-tight hidden md:block">NEUROSUPPLY</span>
          </div>
          <div class="flex items-center space-x-3 md:space-x-6">
            <template v-if="user">
              <span class="text-neutral-500 text-[10px] md:text-xs hidden sm:block">{{ user.email }}</span>
              <a v-if="user.role === 'manager' || user.role === 'admin'" 
                 href="/dashboard" 
                 class="px-2 py-1 md:px-4 md:py-2 bg-blue-600 border border-blue-500/20 text-white rounded-xl text-[10px] md:text-xs font-bold hover:bg-blue-500 transition-all shadow-lg shadow-blue-600/30 flex items-center space-x-1 md:space-x-2">
                <svg class="w-3 h-3 md:w-4 md:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>
                <span class="hidden xs:inline">Админ-панель</span>
                <span class="xs:hidden">Админ</span>
              </a>
              <button @click="handleLogout" class="text-neutral-500 hover:text-white transition-colors text-[10px] md:text-xs font-medium uppercase tracking-wider">Выход</button>
            </template>
            <template v-else>
              <a href="/dashboard" class="px-2.5 py-1.5 md:px-4 md:py-2 bg-white/5 hover:bg-white/10 text-neutral-400 hover:text-white transition-all text-[9px] md:text-xs font-bold uppercase tracking-widest rounded-xl border border-white/10 whitespace-nowrap">Менеджер</a>
            </template>
          </div>
        </header>

        <div class="relative z-10 max-w-4xl w-full text-center space-y-8 pt-24 md:pt-0">
          <div class="space-y-6 animate-in fade-in zoom-in duration-1000">
             <div class="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400">
               <span class="relative flex h-2 w-2">
                 <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                 <span class="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
               </span>
               <span class="text-xs font-bold uppercase tracking-widest">v2.4.0 Pure Web Platform</span>
             </div>
             
             <h1 class="text-6xl md:text-8xl font-black text-white tracking-tighter leading-none">
                NEURO<span class="text-blue-600">SUPPLY</span>
             </h1>
             
             <p class="text-xl md:text-2xl text-neutral-400 font-medium max-w-2xl mx-auto leading-relaxed">
                Интеллектуальная система управления поставками. Автоматизация заказов на базе ИИ.
             </p>
          </div>

          <div class="flex flex-col md:flex-row items-center justify-center gap-6 animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-300">
            <button 
              @click="showLogin = true"
              class="w-full md:w-auto px-10 py-5 bg-blue-600 hover:bg-blue-500 text-white text-lg font-bold rounded-2xl transition-all duration-300 shadow-2xl shadow-blue-600/20 hover:scale-105 active:scale-95 flex items-center justify-center space-x-3 group"
            >
              <span>НАЧАТЬ РАБОТУ 🚀</span>
            </button>
            <button 
              @click="isGuideOpen = true"
              class="w-full md:w-auto px-10 py-5 bg-white/5 hover:bg-white/10 text-white text-lg font-bold rounded-2xl border border-white/10 transition-all duration-300 hover:scale-105 active:scale-95 flex items-center justify-center space-x-2"
            >
              <span>УЗНАТЬ БОЛЬШЕ</span>
              <svg class="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </button>
          </div>

          <BusinessGuide :isOpen="isGuideOpen" @close="isGuideOpen = false" />

          <!-- Feature Grid -->
          <div id="features-section" class="grid grid-cols-1 md:grid-cols-3 gap-6 pt-12 animate-in fade-in slide-in-from-bottom-12 duration-1000 delay-500">
            <div v-for="(feature, i) in ['AI-прогнозирование', 'Smart-логистика', 'Облачная база']" :key="i" 
                 class="p-6 rounded-2xl bg-white/5 border border-white/10 text-left space-y-3 group hover:bg-white/10 transition-colors">
              <div class="w-10 h-10 rounded-lg bg-blue-600/20 flex items-center justify-center text-blue-500 group-hover:scale-110 transition-transform">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 class="text-white font-bold">{{ feature }}</h3>
              <p class="text-neutral-500 text-sm">Оптимизация процессов в реальном времени.</p>
            </div>
          </div>
        </div>
      </div>
      <template v-else>
        <LoginPage v-if="authMode === 'login'" @login-success="checkUser" @toggle-signup="authMode = 'signup'" />
        <SignupPage v-else @toggle-login="authMode = 'login'" />
      </template>
    </template>

    <!-- App Main state -->
    <Dashboard v-else :isManager="user.role === 'manager' || user.role === 'admin'" @logout="handleLogout" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { authService } from './services/auth';
import Dashboard from './components/Dashboard.vue';
import LoginPage from './components/LoginPage.vue';
import SignupPage from './components/SignupPage.vue';
import BusinessGuide from './components/BusinessGuide.vue';

const loading = ref(true);
const user = ref(null);
const showLogin = ref(false);
const authMode = ref('login'); // 'login' | 'signup'
const isGuideOpen = ref(false);

const scrollToFeatures = () => {
  const el = document.getElementById('features-section');
  if (el) {
    el.scrollIntoView({ behavior: 'smooth' });
  }
};

const checkUser = async () => {
    try {
        const timeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Auth Timeout')), 3000)
        );
        const userPromise = authService.getUser();
        user.value = await Promise.race([userPromise, timeoutPromise]);
        console.log('User detected:', user.value);
    } catch (e) {
        console.warn('Auth check failed or timed out:', e);
        user.value = null;
    } finally {
        loading.value = false;
        console.log('App Loaded, user:', user.value);
    }
};

const handleLogout = async () => {
    await authService.logout();
    user.value = null;
    showLogin.value = false;
};

onMounted(async () => {
    console.log('App Mounted - V2.2.1');
    await checkUser();
});
</script>

<style>
@import './style.css';

.animate-in {
  animation-fill-mode: forwards;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
