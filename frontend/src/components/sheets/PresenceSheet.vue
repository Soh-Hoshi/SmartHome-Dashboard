<script setup lang="ts">
import type { PresenceData } from '../../composables/useSmartHome'

defineProps<{
  presence: PresenceData
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
      class="bottom-sheet relative w-full max-w-lg sm:max-w-[460px] h-[calc(100dvh-36px)] sm:h-[min(640px,calc(100dvh-48px))] sm:min-h-[480px] max-h-[calc(100dvh-24px)] bg-[#1e2025] rounded-t-[32px] sm:rounded-[36px] flex flex-col justify-between p-5 pt-6 pb-6 overflow-y-auto shadow-2xl border-t sm:border border-white/[0.06]"
      @click.stop
    >
      <!-- 上部ヘッダー -->
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
          <h2 class="text-xl font-bold text-white tracking-tight">在宅確認</h2>
        </div>
        <div></div>
      </div>

      <!-- 中央メインヒーロー: 在宅/不在ステータス -->
      <div class="my-auto py-6 flex flex-col items-center justify-center text-center select-none shrink-0">
        <div
          class="w-32 h-32 rounded-full flex items-center justify-center mb-4 shadow-inner border transition-colors"
          :class="presence.is_home ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-white/[0.04] border-white/[0.06] text-neutral-400'"
        >
          <span class="material-symbols-rounded text-6xl">home_pin</span>
        </div>
        <div class="text-3xl font-bold text-white">
          {{ presence.is_home ? '在宅' : '不在' }}
        </div>
      </div>

      <!-- 下部: デバイス詳細グリッド (2x2) -->
      <div class="grid grid-cols-2 gap-2 pt-1 shrink-0">
        <div class="bg-[#2a2d36] rounded-2xl p-2.5 flex items-center space-x-2.5 border border-white/[0.04]">
          <div class="w-8 h-8 rounded-xl bg-white/[0.04] text-sky-400 flex items-center justify-center shrink-0">
            <span class="material-symbols-rounded text-lg">smartphone</span>
          </div>
          <div class="overflow-hidden">
            <div class="text-[10px] text-neutral-400 font-normal">端末</div>
            <div class="text-xs font-bold text-white truncate">{{ presence.device_name || 'スマートフォン' }}</div>
          </div>
        </div>

        <div class="bg-[#2a2d36] rounded-2xl p-2.5 flex items-center space-x-2.5 border border-white/[0.04]">
          <div class="w-8 h-8 rounded-xl bg-white/[0.04] text-emerald-400 flex items-center justify-center shrink-0">
            <span class="material-symbols-rounded text-lg">wifi</span>
          </div>
          <div class="overflow-hidden">
            <div class="text-[10px] text-neutral-400 font-normal">IP アドレス</div>
            <div class="text-xs font-bold text-white font-num truncate">{{ presence.ip || '192.168.0.30' }}</div>
          </div>
        </div>

        <div class="bg-[#2a2d36] rounded-2xl p-2.5 flex items-center space-x-2.5 border border-white/[0.04]">
          <div class="w-8 h-8 rounded-xl bg-white/[0.04] text-amber-400 flex items-center justify-center shrink-0">
            <span class="material-symbols-rounded text-lg">fingerprint</span>
          </div>
          <div class="overflow-hidden">
            <div class="text-[10px] text-neutral-400 font-normal">MAC アドレス</div>
            <div class="text-[10px] font-bold text-white font-num truncate">{{ presence.mac || '72:58:BA:C7:40:FA' }}</div>
          </div>
        </div>

        <div class="bg-[#2a2d36] rounded-2xl p-2.5 flex items-center space-x-2.5 border border-white/[0.04]">
          <div class="w-8 h-8 rounded-xl bg-white/[0.04] text-purple-400 flex items-center justify-center shrink-0">
            <span class="material-symbols-rounded text-lg">history</span>
          </div>
          <div class="overflow-hidden">
            <div class="text-[10px] text-neutral-400 font-normal">最終検知</div>
            <div class="text-xs font-bold text-white font-num truncate">{{ presence.last_seen_str || '--:--:--' }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
