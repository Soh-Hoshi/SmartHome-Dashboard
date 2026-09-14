<script setup lang="ts">
import type { WeatherData } from '../../composables/useSmartHome'

defineProps<{
  weather: WeatherData
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
      class="bottom-sheet relative w-full max-w-lg sm:max-w-[460px] h-[calc(100dvh-36px)] sm:h-[min(720px,calc(100dvh-48px))] sm:min-h-[580px] max-h-[calc(100dvh-24px)] bg-[#1e2025] rounded-t-[32px] sm:rounded-[36px] flex flex-col justify-between p-5 pt-6 pb-6 overflow-y-auto shadow-2xl border-t sm:border border-white/[0.06]"
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
          <h2 class="text-xl font-bold text-white tracking-tight">気象情報</h2>
        </div>
        <div></div>
      </div>

      <!-- 中央メインヒーロー: 現在の天気・気温 -->
      <div class="my-auto py-4 flex flex-col items-center justify-center text-center select-none shrink-0">
        <div class="w-32 h-32 rounded-full bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400 mb-4 shadow-inner">
          <span class="material-symbols-rounded text-6xl">{{ weather.weather_icon || 'partly_cloudy_day' }}</span>
        </div>
        <div class="text-base sm:text-lg font-bold text-neutral-200 mb-0.5">{{ weather.weather }}</div>
        <div class="flex items-start justify-center">
          <span class="text-5xl sm:text-6xl font-bold tracking-tight text-white leading-none font-num">{{ weather.temp }}</span>
          <span class="text-2xl font-bold text-neutral-400 ml-1 mt-0.5 font-num">℃</span>
        </div>
        <div class="text-xs text-neutral-400 font-medium mt-2">
          最高 {{ weather.temp_max }}℃ / 最低 {{ weather.temp_min }}℃ ・ 体感 {{ weather.feels_like }}℃
        </div>
      </div>

      <!-- 1日の時間帯別予報 (横スクロール) -->
      <div class="shrink-0 space-y-1.5 py-1">
        <div class="text-xs font-bold text-neutral-400 px-1">今日の時間別予報</div>
        <div class="flex space-x-2 overflow-x-auto pb-1 no-scrollbar select-none">
          <div
            v-for="(h, idx) in weather.hourly"
            :key="idx"
            class="flex flex-col items-center justify-between p-2.5 rounded-2xl bg-[#2a2d36] min-w-[70px] shrink-0 border border-white/[0.03]"
          >
            <span class="text-[11px] font-medium text-neutral-400 font-num">{{ h.time }}</span>
            <span class="material-symbols-rounded text-2xl text-sky-400 my-1">{{ h.icon }}</span>
            <span class="text-xs font-bold text-white font-num">{{ h.temp }}℃</span>
            <span class="text-[10px] font-normal text-sky-300 font-num mt-0.5">{{ h.pop }}%</span>
          </div>
        </div>
      </div>

      <!-- 下部: 環境ステータスグリッド (2x2) -->
      <div class="grid grid-cols-2 gap-2 pt-1 shrink-0">
        <div class="bg-[#2a2d36] rounded-2xl p-2.5 flex items-center space-x-2.5 border border-white/[0.04]">
          <div class="w-8 h-8 rounded-xl bg-white/[0.04] text-sky-400 flex items-center justify-center shrink-0">
            <span class="material-symbols-rounded text-lg">humidity_mid</span>
          </div>
          <div>
            <div class="text-[10px] text-neutral-400 font-normal">湿度</div>
            <div class="text-xs sm:text-sm font-bold text-white font-num">{{ weather.humidity }}%</div>
          </div>
        </div>

        <div class="bg-[#2a2d36] rounded-2xl p-2.5 flex items-center space-x-2.5 border border-white/[0.04]">
          <div class="w-8 h-8 rounded-xl bg-white/[0.04] text-emerald-400 flex items-center justify-center shrink-0">
            <span class="material-symbols-rounded text-lg">air</span>
          </div>
          <div>
            <div class="text-[10px] text-neutral-400 font-normal">風速</div>
            <div class="text-xs sm:text-sm font-bold text-white font-num">{{ weather.wind_speed }} m/s</div>
          </div>
        </div>

        <div class="bg-[#2a2d36] rounded-2xl p-2.5 flex items-center space-x-2.5 border border-white/[0.04]">
          <div class="w-8 h-8 rounded-xl bg-white/[0.04] text-amber-400 flex items-center justify-center shrink-0">
            <span class="material-symbols-rounded text-lg">wb_twilight</span>
          </div>
          <div>
            <div class="text-[10px] text-neutral-400 font-normal">日の入り (日没)</div>
            <div class="text-xs sm:text-sm font-bold text-white font-num">{{ weather.sunset }}</div>
          </div>
        </div>

        <div class="bg-[#2a2d36] rounded-2xl p-2.5 flex items-center space-x-2.5 border border-white/[0.04]">
          <div class="w-8 h-8 rounded-xl bg-white/[0.04] text-yellow-400 flex items-center justify-center shrink-0">
            <span class="material-symbols-rounded text-lg">wb_sunny</span>
          </div>
          <div>
            <div class="text-[10px] text-neutral-400 font-normal">日の出</div>
            <div class="text-xs sm:text-sm font-bold text-white font-num">{{ weather.sunrise }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
