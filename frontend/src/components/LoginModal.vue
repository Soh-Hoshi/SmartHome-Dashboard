<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  (e: 'loginSuccess'): void
}>()

const password = ref('')
const error = ref('')
const loading = ref(false)
const showPassword = ref(false)

async function handleLogin() {
  if (!password.value.trim() || loading.value) return
  loading.value = true
  error.value = ''

  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'SmartHome-UI',
      },
      body: JSON.stringify({ key: password.value.trim() }),
    })

    const data = await res.json().catch(() => ({}))
    if (res.ok && data.status === 'success') {
      emit('loginSuccess')
    } else {
      error.value = data.message || 'パスワードが正しくありません'
    }
  } catch (err) {
    error.value = '通信エラーが発生しました'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md">
    <div class="w-full max-w-xs bg-[#131518]/95 backdrop-blur-xl border border-white/[0.08] rounded-3xl p-6 shadow-2xl flex flex-col items-center text-center">
      <!-- Nova アイコン -->
      <div class="w-12 h-12 rounded-full bg-white/[0.05] border border-white/[0.06] flex items-center justify-center text-neutral-300 mb-3 select-none">
        <span class="material-symbols-rounded text-2xl text-[#2196f3]">auto_awesome</span>
      </div>

      <h1 class="text-lg font-bold tracking-tight text-white mb-5">SmartHome</h1>

      <!-- エラーメッセージ -->
      <div
        v-if="error"
        class="w-full mb-3 px-3 py-2 rounded-2xl bg-red-500/10 border border-red-500/25 text-red-400 text-xs flex items-center gap-2"
      >
        <span class="material-symbols-rounded text-base shrink-0">error</span>
        <span>{{ error }}</span>
      </div>

      <!-- フォーム -->
      <form @submit.prevent="handleLogin" class="w-full space-y-3">
        <div class="relative flex items-center bg-[#1c1e23] border border-white/[0.08] focus-within:border-[#2196f3]/70 focus-within:ring-2 focus-within:ring-[#2196f3]/25 rounded-2xl transition-all px-3.5 py-2.5">
          <input
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            required
            autocomplete="current-password"
            placeholder="パスワード"
            class="flex-1 bg-transparent text-[15px] text-white placeholder-neutral-500 focus:outline-none font-normal pr-1"
          />
          <button
            type="button"
            @click="showPassword = !showPassword"
            class="text-neutral-400 hover:text-white p-1 transition-colors flex items-center justify-center shrink-0"
            tabindex="-1"
          >
            <span class="material-symbols-rounded text-[20px]">
              {{ showPassword ? 'visibility_off' : 'visibility' }}
            </span>
          </button>
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-[#2196f3] hover:bg-[#1e88e5] active:scale-[0.99] text-white font-medium text-sm py-3 rounded-2xl transition-all shadow-[0_4px_16px_rgba(33,150,243,0.3)] flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <span>{{ loading ? '認証中...' : 'ログイン' }}</span>
          <span v-if="loading" class="material-symbols-rounded text-sm animate-spin">progress_activity</span>
        </button>
      </form>
    </div>
  </div>
</template>
