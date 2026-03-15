<template>
  <div class="login-page min-h-screen bg-neutral-900 flex items-center justify-center p-4">
    <div class="max-w-md w-full animate-in fade-in slide-in-from-bottom-4 duration-1000">
      <!-- Security/Tunnel Notice -->
      <div class="mb-6 bg-blue-500/10 border border-blue-500/20 rounded-2xl p-4 animate-in fade-in duration-700">
        <div class="flex items-start space-x-3">
          <svg class="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p class="text-[11px] text-blue-300 leading-relaxed font-medium">
            Примечание для Теста: Chrome может показать предупреждение из-за использования Cloudflare Tunnel. Нажмите "Пропустить" или "Advanced" для входа. В рабочей версии это предупреждение будет отсутствовать.
          </p>
        </div>
      </div>

      <div class="bg-neutral-800/50 backdrop-blur-xl rounded-3xl p-8 border border-white/10 shadow-2xl">
        <!-- Logo & Header -->
        <div class="text-center mb-10">
          <div class="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-blue-600/20 text-blue-500 mb-6 border border-blue-500/20 group hover:scale-110 transition-transform duration-500">
            <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h1 class="text-3xl font-bold text-white mb-2 tracking-tight">Вход</h1>
          <p class="text-neutral-400">Введите свои данные для доступа к платформе</p>
          <div class="mt-4 inline-block px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20">
            <span class="text-xs font-medium text-blue-400 uppercase tracking-widest">v2.2.0 Web Platform</span>
          </div>
        </div>

        <form @submit.prevent="handleLogin" class="space-y-6">
          <div class="space-y-2">
            <label class="text-sm font-medium text-neutral-300 ml-1">Email</label>
            <div class="relative group">
              <input 
                v-model="email"
                type="email" 
                placeholder="chef@neurosupply.pro"
                required
                class="w-full bg-neutral-900/50 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-neutral-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300"
              />
              <div class="absolute inset-0 rounded-xl bg-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
            </div>
          </div>

          <div class="space-y-2">
            <div class="flex items-center justify-between ml-1">
              <label class="text-sm font-medium text-neutral-300">Пароль</label>
              <button 
                type="button" 
                @click="error = 'Функция восстановления пароля временно недоступна. Свяжитесь с поддержкой.'"
                class="text-xs text-blue-400 hover:text-blue-300 transition-colors"
              >
                Забыли пароль?
              </button>
            </div>
            <div class="relative group">
              <input 
                v-model="password"
                type="password" 
                placeholder="••••••••"
                required
                class="w-full bg-neutral-900/50 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-neutral-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300"
              />
              <div class="absolute inset-0 rounded-xl bg-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
            </div>
          </div>

          <div class="pt-2">
            <button 
              type="submit" 
              :disabled="loading"
              class="w-full h-12 bg-blue-600 hover:bg-blue-500 disabled:bg-neutral-700 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-all duration-300 shadow-lg shadow-blue-600/20 active:scale-[0.98] flex items-center justify-center space-x-2 group"
            >
              <span v-if="loading" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              <span v-else>ВОЙТИ</span>
              <svg v-if="!loading" class="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </button>
          </div>

          <div v-if="error" class="bg-red-500/10 border border-red-500/20 rounded-xl p-4 animate-in fade-in slide-in-from-top-2">
            <div class="flex space-x-3">
              <svg class="w-5 h-5 text-red-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p class="text-sm text-red-400 leading-relaxed">{{ error }}</p>
            </div>
          </div>
        </form>

        <div class="mt-8 text-center space-y-4">
            <p class="text-neutral-500 text-sm">
                Нет аккаунта? 
                <button 
                  type="button"
                  @click="$emit('toggle-signup')" 
                  class="text-blue-400 hover:text-blue-300 font-medium transition-colors"
                >
                  Зарегистрироваться
                </button>
            </p>
        </div>
      </div>
      
      <!-- Footer Info -->
      <div class="mt-8 text-center space-y-2 opacity-50">
        <p class="text-xs text-neutral-400">© 2026 NeuroSupply AI Solutions</p>
        <p class="text-[10px] text-neutral-600 uppercase tracking-[0.2em]">Secure Enterprise Access Only</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { authService } from '../services/auth';

const email = ref('');
const password = ref('');
const loading = ref(false);
const error = ref('');

const emit = defineEmits(['login-success']);

const handleLogin = async () => {
  loading.value = true;
  error.value = '';
  
  try {
    await authService.login(email.value, password.value);
    emit('login-success');
  } catch (err) {
    error.value = 'Ошибка входа: ' + (err.message || 'Проверьте данные');
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
