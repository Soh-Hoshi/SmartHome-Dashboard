<script setup lang="ts">
defineProps<{
  title: string
  backgroundStyle?: string
  scrollable?: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()
</script>

<template>
  <div
    class="sheet-backdrop visible-sheet fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/65 backdrop-blur-sm"
    @click="emit('close')"
  >
    <div
      class="bottom-sheet relative w-full max-w-lg sm:max-w-[460px] h-[calc(100dvh-36px)] sm:h-[min(720px,calc(100dvh-48px))] sm:min-h-[580px] max-h-[calc(100dvh-24px)] bg-[#1e2025] rounded-t-[32px] sm:rounded-[36px] flex flex-col justify-between p-5 pt-6 pb-6 shadow-2xl border-t sm:border border-white/[0.06] transition-all duration-300"
      :class="scrollable ? 'overflow-y-auto' : 'overflow-visible'"
      :style="backgroundStyle ? { backgroundImage: backgroundStyle } : undefined"
      @click.stop
    >
      <!-- 上部ヘッダー (共通) -->
      <div class="flex items-center justify-between pb-1 shrink-0">
        <div class="flex items-center space-x-3.5">
          <button
            type="button"
            @click="emit('close')"
            class="w-9 h-9 rounded-full bg-white/[0.04] hover:bg-white/[0.08] text-neutral-400 hover:text-white transition-colors flex items-center justify-center"
            aria-label="閉じる"
          >
            <span class="material-symbols-rounded text-2xl">close</span>
          </button>
          <h2 class="text-xl font-bold text-white tracking-tight leading-tight">{{ title }}</h2>
        </div>
        <slot name="header-right"></slot>
      </div>

      <!-- シート内部スロット -->
      <slot></slot>
    </div>
  </div>
</template>
