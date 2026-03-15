<template>
  <div class="signup-page min-h-screen bg-neutral-900 flex items-center justify-center p-4">
    <div class="max-w-md w-full animate-in fade-in slide-in-from-bottom-4 duration-1000">
      <div class="bg-neutral-800/50 backdrop-blur-xl rounded-3xl p-8 border border-white/10 shadow-2xl">
        <!-- Logo & Header -->
        <div class="text-center mb-10">
          <div class="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-blue-600/20 text-blue-500 mb-6 border border-blue-500/20">
            <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
          </div>
          <h1 class="text-3xl font-bold text-white mb-2 tracking-tight">Регистрация</h1>
          <p class="text-neutral-400">Создайте новый аккаунт в системе</p>
        </div>

        <form @submit.prevent="handleSignUp" class="space-y-6">
          <div class="space-y-2">
            <label class="text-sm font-medium text-neutral-300 ml-1">Email</label>
            <input 
              v-model="email"
              type="email" 
              placeholder="chef@neurosupply.pro"
              required
              class="w-full bg-neutral-900/50 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-neutral-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
            />
          </div>

          <div class="space-y-2">
            <label class="text-sm font-medium text-neutral-300 ml-1">Пароль</label>
            <input 
              v-model="password"
              type="password" 
              placeholder="••••••••"
              required
              class="w-full bg-neutral-900/50 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-neutral-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
            />
          </div>

          <div class="space-y-2">
            <label class="text-sm font-medium text-neutral-300 ml-1">Ваша роль</label>
            <select 
              v-model="role"
              class="w-full bg-neutral-900/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
            >
              <option value="cook">Повар (Cook)</option>
              <option value="manager">Менеджер (Manager)</option>
            </select>
          </div>

          <div class="pt-2">
            <button 
              type="submit" 
              :disabled="loading"
              class="w-full h-12 bg-blue-600 hover:bg-blue-500 disabled:bg-neutral-700 text-white font-semibold rounded-xl transition-all shadow-lg shadow-blue-600/20 active:scale-[0.98] flex items-center justify-center space-x-2"
            >
              <span v-if="loading" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              <span v-else>ЗАРЕГИСТРИРОВАТЬСЯ</span>
            </button>
          </div>

          <div v-if="error" class="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-sm text-red-400">
            {{ error }}
          </div>
          <div v-if="success" class="bg-green-500/10 border border-green-500/20 rounded-xl p-4 text-sm text-green-400">
            {{ success }}
          </div>
        </form>

        <div class="mt-8 text-center">
            <button @click="$emit('toggle-login')" class="text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors">
                Уже есть аккаунт? Войти
            </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { authService } from '../services/auth';

const email = ref('');
const password = ref('');
const role = ref('cook');
const loading = ref(false);
const error = ref('');
const success = ref('');

const emit = defineEmits(['toggle-login']);

const handleSignUp = async () => {
  loading.value = true;
  error.value = '';
  success.value = '';
  
  try {
    await authService.signUp(email.value, password.value, { role: role.value });
    success.value = 'Регистрация успешна! Проверьте почту для подтверждения или попробуйте войти.';
    setTimeout(() => {
        emit('toggle-login');
    }, 3000);
  } catch (err) {
    error.value = 'Ошибка регистрации: ' + (err.message || 'Попробуйте другой Email');
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.animate-spin {
  animation: spin 1s linear infinite;
}
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
