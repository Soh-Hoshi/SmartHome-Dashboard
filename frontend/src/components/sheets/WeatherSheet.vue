<script setup lang="ts">
import SheetModal from '../common/SheetModal.vue'
import StatCard from '../common/StatCard.vue'
import AppIcon from '../common/AppIcon.vue'
import type { WeatherData } from '../../composables/useSmartHome'

defineProps<{
  weather: WeatherData
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()
</script>

<template>
  <SheetModal title="気象情報" :scrollable="true" @close="emit('close')">
    <!-- 中央メインヒーロー: 現在の天気・気温 -->
    <div class="my-auto py-4 flex flex-col items-center justify-center text-center select-none shrink-0">
      <div class="w-32 h-32 rounded-full bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400 mb-4 shadow-inner">
        <AppIcon :name="weather.weather_icon || 'partly_cloudy_day'" :size="64" />
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
          <AppIcon :name="h.icon" :size="24" class="text-sky-400 my-1" />
          <span class="text-xs font-bold text-white font-num">{{ h.temp }}℃</span>
          <span class="text-[10px] font-normal text-sky-300 font-num mt-0.5">{{ h.pop }}%</span>
        </div>
      </div>
    </div>

    <!-- 下部: 環境ステータスグリッド (2x2) -->
    <div class="grid grid-cols-2 gap-2 pt-1 shrink-0">
      <StatCard label="湿度" :value="`${weather.humidity}%`" icon="humidity_mid" iconColor="text-sky-400" />
      <StatCard label="風速" :value="`${weather.wind_speed} m/s`" icon="air" iconColor="text-emerald-400" />
      <StatCard label="日の入り (日没)" :value="weather.sunset" icon="wb_twilight" iconColor="text-amber-400" />
      <StatCard label="日の出" :value="weather.sunrise" icon="wb_sunny" iconColor="text-yellow-400" />
    </div>
  </SheetModal>
</template>
