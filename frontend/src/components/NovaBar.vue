<script setup lang="ts">
import { ref } from 'vue'
import AppIcon from './common/AppIcon.vue'

const props = defineProps<{
  toast: {
    visible: boolean
    message: string
    icon: string
    isError: boolean
  }
  isSubmitting: boolean
  isRecording: boolean
}>()

const emit = defineEmits<{
  (e: 'submit', prompt: string): void
  (e: 'toggleVoice'): void
}>()

const inputText = ref('')

function handleSubmit() {
  if (inputText.value.trim()) {
    emit('submit', inputText.value.trim())
    inputText.value = ''
  }
}

function handleVoiceOrSubmit() {
  if (inputText.value.trim()) {
    handleSubmit()
  } else {
    emit('toggleVoice')
  }
}
</script>

<template>
  <div class="fixed top-0 md:top-auto md:bottom-6 inset-x-0 z-40 flex flex-col items-center pointer-events-none pt-[env(safe-area-inset-top,0.25rem)] md:pt-0 pb-2.5 md:pb-0 px-3 sm:px-6 bg-[#1c1e23]/95 md:bg-transparent backdrop-blur-xl md:backdrop-blur-none border-b border-white/[0.06] md:border-b-0 shadow-lg md:shadow-none">
    
    <!-- アシスタント トースト通知 (フィードバック表示) -->
    <transition
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="opacity-0 translate-y-3 scale-95"
      enter-to-class="opacity-100 translate-y-0 scale-100"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="opacity-100 translate-y-0 scale-100"
      leave-to-class="opacity-0 translate-y-2 scale-95"
    >
      <div
        v-if="toast.visible"
        id="assistant-toast"
        class="pointer-events-auto order-last md:order-first mt-2.5 md:mt-0 md:mb-2 max-w-xl bg-[#131518]/95 backdrop-blur-xl border border-white/[0.1] text-white text-sm px-4 py-2.5 rounded-2xl shadow-2xl flex items-center space-x-2.5 select-none"
      >
        <AppIcon
          :name="toast.icon"
          :size="18"
          class="shrink-0"
          :class="toast.isError ? 'text-rose-400' : 'text-[#2196f3]'"
        />
        <span class="font-medium tracking-wide">{{ toast.message }}</span>
      </div>
    </transition>

    <!-- Nova プロンプトバー本体 -->
    <div class="w-full max-w-2xl">
      <div
        id="command-bar-container"
        class="pointer-events-auto w-full bg-[#131518]/95 backdrop-blur-xl border border-[#2196f3]/25 focus-within:border-[#2196f3]/70 focus-within:ring-2 focus-within:ring-[#2196f3]/25 rounded-full shadow-[0_8px_32px_rgba(0,0,0,0.5),0_0_16px_rgba(33,150,243,0.14)] focus-within:shadow-[0_8px_32px_rgba(0,0,0,0.55),0_0_22px_rgba(33,150,243,0.25)] p-2 sm:p-2.5 min-h-[56px] sm:min-h-[62px] flex items-center gap-2.5 sm:gap-3.5 transition-all duration-200"
      >
        <!-- Nova アイコン (Gemini風 キラキラ) -->
        <div
          class="w-10 h-10 sm:w-11 sm:h-11 rounded-full bg-white/[0.05] flex items-center justify-center text-neutral-300 shrink-0 select-none ml-0.5 transition-transform duration-300"
          :class="{ 'animate-spin': isSubmitting }"
        >
          <AppIcon name="auto_awesome" :size="24" class="text-[#2196f3]" />
        </div>

        <!-- コマンド入力フォーム -->
        <input
          v-model="inputText"
          type="text"
          :placeholder="isRecording ? 'Novaがお聞きしています...' : 'Novaに話しかける...'"
          class="flex-1 bg-transparent text-[16px] sm:text-[17px] text-white placeholder-neutral-400 focus:outline-none px-2 py-1.5 font-normal"
          autocomplete="off"
          @keydown.enter.prevent="handleSubmit"
        />

        <!-- 音声コマンド / 送信ボタン -->
        <button
          type="button"
          @click="handleVoiceOrSubmit"
          class="w-10 h-10 sm:w-11 sm:h-11 rounded-full flex items-center justify-center transition-all shrink-0 mr-0.5 shadow-sm border"
          :class="[
            isRecording
              ? 'voice-listening'
              : inputText.trim()
                ? 'bg-[#1b222c] hover:bg-[#222b38] active:scale-95 text-[#60a5fa] border-[#2196f3]/35 shadow-[0_2px_8px_rgba(33,150,243,0.15)]'
                : 'bg-[#1e2128] hover:bg-[#282c35] active:scale-95 text-neutral-200 hover:text-white border-white/[0.04]'
          ]"
          :aria-label="isRecording ? '音声入力停止' : inputText.trim() ? 'コマンド送信' : 'Nova音声入力'"
        >
          <AppIcon
            :name="isRecording ? 'graphic_eq' : inputText.trim() ? 'send' : 'mic'"
            :size="24"
          />
        </button>
      </div>
    </div>

  </div>
</template>
