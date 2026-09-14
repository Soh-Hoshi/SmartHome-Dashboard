<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  temp: number
  mode: 'heat' | 'off'
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'changeTemp', delta: number): void
  (e: 'selectMode', mode: 'heat' | 'off'): void
  (e: 'pressEco'): void
  (e: 'pressPower'): void
}>()

const openModeDropup = ref(false)

const minTemp = 22
const maxTemp = 28
const totalArcLength = 494.8

const ratio = computed(() => {
  return Math.max(0, Math.min(1, (props.temp - minTemp) / (maxTemp - minTemp)))
})

const visibleLength = computed(() => totalArcLength * ratio.value)

function handleSelectMode(m: 'heat' | 'off') {
  openModeDropup.value = false
  emit('selectMode', m)
}
</script>

<template>
  <div
    class="sheet-backdrop visible-sheet fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/65 backdrop-blur-sm"
    @click="emit('close')"
  >
    <div
      class="bottom-sheet relative w-full max-w-lg sm:max-w-[460px] h-[calc(100dvh-36px)] sm:h-[min(720px,calc(100dvh-48px))] sm:min-h-[580px] max-h-[calc(100dvh-24px)] bg-[#1e2025] rounded-t-[32px] sm:rounded-[36px] flex flex-col justify-between p-5 pt-6 pb-6 overflow-visible shadow-2xl border-t sm:border border-white/[0.06]"
      @click.stop="openModeDropup = false"
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
          <h2 class="text-xl font-bold text-white tracking-tight">ヒーター</h2>
        </div>
        <div></div>
      </div>

      <!-- 中央: 蹄型 (Horseshoe) 温度ゲージ (ノブなし) ＆ 温度調節ボタン -->
      <div class="flex-1 flex flex-col items-center justify-center my-auto relative py-2 shrink-0">
        <div class="relative w-72 h-72 flex items-center justify-center shrink-0">
          <svg class="w-full h-full select-none pointer-events-none" viewBox="0 0 280 280">
            <path
              d="M 65.75 214.25 A 105 105 0 1 1 214.25 214.25"
              fill="none"
              :stroke="mode === 'heat' ? 'rgba(234, 122, 30, 0.15)' : 'rgba(255, 255, 255, 0.05)'"
              stroke-width="24"
              stroke-linecap="round"
            />
            <path
              v-if="mode !== 'off'"
              d="M 65.75 214.25 A 105 105 0 1 1 214.25 214.25"
              fill="none"
              stroke="#ea7a1e"
              stroke-width="24"
              stroke-linecap="round"
              :stroke-dasharray="`${visibleLength} ${totalArcLength}`"
              stroke-dashoffset="0"
            />
          </svg>

          <!-- 円の中央テキスト情報 -->
          <div class="absolute inset-0 flex flex-col items-center justify-center text-center select-none pointer-events-none pb-4">
            <template v-if="mode === 'off'">
              <span class="text-5xl font-bold tracking-tight text-white leading-none translate-y-1.5">オフ</span>
            </template>
            <template v-else>
              <span class="text-sm font-medium text-neutral-300 mb-1 tracking-wide">暖房</span>
              <div class="flex items-start justify-center">
                <span class="text-6xl font-bold tracking-tight text-white leading-none font-num translate-y-0">{{ temp }}</span>
                <span class="text-2xl font-bold text-neutral-300 ml-1 mt-0.5 font-num">℃</span>
              </div>
            </template>
          </div>

          <!-- 温度調節ボタン (ー / ＋) -->
          <div class="absolute bottom-1 inset-x-0 flex items-center justify-center space-x-7 z-10">
            <button
              type="button"
              @click.stop="emit('changeTemp', -1)"
              class="w-11 h-11 rounded-full bg-[#2a2d36] hover:bg-[#343844] border border-white/[0.05] flex items-center justify-center text-white transition-all shadow-sm active:scale-95 shrink-0"
              aria-label="温度を下げる"
            >
              <span class="material-symbols-rounded text-2xl font-bold">remove</span>
            </button>

            <button
              type="button"
              @click.stop="emit('changeTemp', 1)"
              class="w-11 h-11 rounded-full bg-[#2a2d36] hover:bg-[#343844] border border-white/[0.05] flex items-center justify-center text-white transition-all shadow-sm active:scale-95 shrink-0"
              aria-label="温度を上げる"
            >
              <span class="material-symbols-rounded text-2xl font-bold">add</span>
            </button>
          </div>
        </div>
      </div>

      <!-- 最下部コントロールエリア (1段目: モード、2段目: エコ & パワー) -->
      <div class="relative space-y-2.5 pt-1">
        <!-- 1段目: モード ドロップアップ -->
        <div class="relative">
          <div
            v-show="openModeDropup"
            class="dropup-menu open absolute bottom-full mb-3 left-0 w-56 bg-[#262932] border border-white/10 rounded-2xl p-1.5 shadow-2xl z-30 backdrop-blur-xl"
            @click.stop
          >
            <div class="text-[11px] font-semibold text-neutral-400 px-3 py-1.5 uppercase tracking-wider">モード</div>
            <div class="space-y-0.5">
              <button
                type="button"
                @click="handleSelectMode('heat')"
                class="w-full h-10 flex items-center justify-between px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
              >
                <div class="flex items-center space-x-3 text-[#f57c00]">
                  <span class="material-symbols-rounded text-xl">mode_heat</span>
                  <span class="text-white">暖房</span>
                </div>
                <span v-if="mode === 'heat'" class="text-[#f57c00] flex items-center justify-center shrink-0 w-5 h-5">
                  <span class="material-symbols-rounded symbol-bold text-lg leading-none">check</span>
                </span>
              </button>

              <div class="h-px bg-white/10 my-1"></div>

              <button
                type="button"
                @click="handleSelectMode('off')"
                class="w-full h-10 flex items-center justify-between px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
              >
                <div class="flex items-center space-x-3 text-neutral-400">
                  <span class="material-symbols-rounded text-xl">power_settings_new</span>
                  <span class="text-neutral-300">オフ</span>
                </div>
                <span v-if="mode === 'off'" class="text-neutral-400 flex items-center justify-center shrink-0 w-5 h-5">
                  <span class="material-symbols-rounded symbol-bold text-lg leading-none">check</span>
                </span>
              </button>
            </div>
          </div>

          <!-- モード トリガーボタン (フル幅 h-[58px]) -->
          <button
            type="button"
            @click.stop="openModeDropup = !openModeDropup"
            class="w-full h-[58px] flex items-center space-x-3 px-4 rounded-2xl bg-[#2a2d36] hover:bg-[#323640] text-left transition-all shadow-sm border border-white/[0.04] active:scale-[0.98]"
          >
            <div class="shrink-0 flex items-center justify-center" :class="mode === 'heat' ? 'text-[#f57c00]' : 'text-neutral-400'">
              <span class="material-symbols-rounded text-2xl">{{ mode === 'heat' ? 'mode_heat' : 'power_settings_new' }}</span>
            </div>
            <div class="overflow-hidden leading-tight flex-1">
              <div class="text-xs text-neutral-400 font-normal">モード</div>
              <div class="text-[14px] font-semibold text-white truncate mt-0.5">
                {{ mode === 'heat' ? '暖房' : 'オフ' }}
              </div>
            </div>
            <span class="material-symbols-rounded text-lg text-neutral-400 shrink-0">expand_less</span>
          </button>
        </div>

        <!-- 2段目: エコ & パワー ボタン (横幅半分ずつ h-[58px]) -->
        <div class="grid grid-cols-2 gap-3">
          <button
            type="button"
            :disabled="mode === 'off'"
            @click.stop="emit('pressEco')"
            class="w-full h-[58px] flex items-center space-x-3 px-4 rounded-2xl bg-[#2a2d36] hover:bg-[#323640] text-left transition-all shadow-sm border border-white/[0.04] active:scale-[0.98] disabled:opacity-40 disabled:pointer-events-none"
          >
            <div class="text-neutral-400 shrink-0 flex items-center justify-center transition-colors">
              <span class="material-symbols-rounded text-2xl">eco</span>
            </div>
            <div class="overflow-hidden leading-tight flex-1">
              <div class="text-[14px] font-semibold text-white truncate">エコ</div>
            </div>
          </button>

          <button
            type="button"
            :disabled="mode === 'off'"
            @click.stop="emit('pressPower')"
            class="w-full h-[58px] flex items-center space-x-3 px-4 rounded-2xl bg-[#2a2d36] hover:bg-[#323640] text-left transition-all shadow-sm border border-white/[0.04] active:scale-[0.98] disabled:opacity-40 disabled:pointer-events-none"
          >
            <div class="text-neutral-400 shrink-0 flex items-center justify-center transition-colors">
              <span class="material-symbols-rounded text-2xl">bolt</span>
            </div>
            <div class="overflow-hidden leading-tight flex-1">
              <div class="text-[14px] font-semibold text-white truncate">パワー</div>
            </div>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
