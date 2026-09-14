<script setup lang="ts">
import AppIcon from '../common/AppIcon.vue'
import type { WeatherData, PresenceData, TileData } from '../../composables/useSmartHome'

const props = defineProps<{
  // AC
  acTemp: number
  acMode: 'cool' | 'dry' | 'off'
  // Heater
  heaterTemp: number
  heaterMode: 'heat' | 'off'
  // Light
  lightOn: boolean
  // Cleaner
  cleanerStatus: string
  cleanerPlay: boolean
  // PC
  pcOnline: boolean
  pcBooting: boolean
  pcShuttingDown: boolean
  pcOs: string
  pcTargetOs: 'Windows' | 'Bazzite'
  // Sensors
  weather: WeatherData
  presence: PresenceData
  tile: TileData
}>()

const emit = defineEmits<{
  (e: 'openSheet', sheetId: string): void
  (e: 'toggleLight'): void
  (e: 'toggleAcPower'): void
  (e: 'setAcMode', mode: 'cool' | 'dry' | 'off'): void
  (e: 'toggleHeaterPower'): void
  (e: 'toggleCleanerPower'): void
  (e: 'setCleanerMode', action: 'start' | 'pause' | 'stop'): void
  (e: 'togglePcPower'): void
}>()

function getCleanerStatusText() {
  const st = (props.cleanerStatus || '').toLowerCase()
  const isRunning = st === 'running' && props.cleanerPlay
  if (isRunning) return '清掃中'
  if (st === 'charging') return '充電中'
  if (st === 'recharge') return '帰還中'
  if (st === 'standby') return '一時停止中'
  if (st === 'completed') return '充電完了'
  return '待機中'
}

function isCleanerRunning() {
  return (props.cleanerStatus || '').toLowerCase() === 'running' && props.cleanerPlay
}

function getPcIcon() {
  const isBazzite = props.pcTargetOs === 'Bazzite' || (props.pcOnline && props.pcOs === 'Bazzite')
  return isBazzite ? 'sports_esports' : 'desktop_windows'
}

function getPcStatusText() {
  if (props.pcBooting) return '起動中'
  if (props.pcShuttingDown) return '終了中'
  if (props.pcOnline) {
    return props.pcOs && props.pcOs !== 'Unknown' && props.pcOs !== '起動中'
      ? props.pcOs
      : props.pcTargetOs
  }
  return 'オフ'
}
</script>

<template>
  <main id="view-dashboard" class="tab-view w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 columns-1 md:columns-2 lg:columns-3 gap-6">
    
    <!-- セクション: ライト -->
    <section class="break-inside-avoid mb-6 space-y-3">
      <h2 class="text-base font-bold text-white px-1">ライト</h2>
      
      <div class="flex flex-col gap-3.5">
        <!-- リビング タイル -->
        <div
          @click="emit('openSheet', 'light-sheet')"
          class="group relative bg-[#1c1e23] hover:bg-[#23262d] rounded-3xl p-3.5 flex items-center space-x-3.5 cursor-pointer transition-colors duration-150 shadow-md border border-white/[0.03]"
        >
          <!-- アイコンボタン -->
          <button
            type="button"
            @click.stop="emit('toggleLight')"
            class="w-11 h-11 rounded-full flex items-center justify-center transition-all duration-300 hover:scale-105 active:scale-95 shrink-0"
            :class="lightOn ? 'bg-[#383226] text-amber-400' : 'bg-[#272a31] text-neutral-400'"
            aria-label="ライトのオン/オフ切り替え"
          >
            <AppIcon name="lightbulb" :size="24" />
          </button>

          <!-- テキスト -->
          <div class="flex-1">
            <div class="text-[15px] font-semibold text-white leading-tight">リビング</div>
            <div class="text-xs text-neutral-400 font-normal mt-0.5 transition-colors">
              {{ lightOn ? 'オン' : 'オフ' }}
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- セクション: 空調 -->
    <section class="break-inside-avoid mb-6 space-y-3">
      <h2 class="text-base font-bold text-white px-1">空調</h2>
      
      <div class="flex flex-col gap-3.5">
        <!-- エアコンタイル -->
        <div
          @click="emit('openSheet', 'ac-sheet')"
          class="group relative bg-[#1c1e23] hover:bg-[#23262d] rounded-3xl p-3.5 space-y-3 cursor-pointer transition-colors duration-150 shadow-md border border-white/[0.03]"
        >
          <!-- 上部情報 (統一 MDI: mode_cool / water_drop) -->
          <div class="flex items-center space-x-3.5">
            <button
              type="button"
              @click.stop="emit('toggleAcPower')"
              class="w-11 h-11 rounded-full flex items-center justify-center transition-all duration-300 hover:scale-105 active:scale-95 shrink-0"
              :class="[
                acMode === 'cool' ? 'bg-[#253546] text-[#2196f3]' :
                acMode === 'dry' ? 'bg-[#213840] text-[#00bcd4]' :
                'bg-[#272a31] text-neutral-400'
              ]"
              aria-label="エアコンのオン/オフ切り替え"
            >
              <AppIcon name="mode_fan" :size="24" />
            </button>
            <div class="flex-1">
              <div class="text-[15px] font-semibold text-white leading-tight">エアコン</div>
              <div class="text-xs text-neutral-400 font-normal mt-0.5 font-num flex items-center space-x-1">
                <span v-if="acMode === 'off'">オフ</span>
                <template v-else>
                  <span>{{ acMode === 'cool' ? '冷房' : '除湿' }}</span>
                  <span>・</span>
                  <span>{{ acTemp }}℃</span>
                </template>
              </div>
            </div>
          </div>

          <!-- 下部操作ボタングループ (オフ、除湿、冷房) -->
          <div class="grid grid-cols-3 gap-2 pt-0.5" @click.stop>
            <button
              type="button"
              @click="emit('setAcMode', 'off')"
              class="h-11 rounded-2xl flex items-center justify-center transition-all"
              :class="acMode === 'off' ? 'bg-[#333741] hover:bg-[#3c414d] text-white' : 'bg-[#292c34] hover:bg-[#323640] text-neutral-400 hover:text-white'"
              aria-label="オフ"
            >
              <AppIcon name="power" :size="20" />
            </button>

            <button
              type="button"
              @click="emit('setAcMode', 'dry')"
              class="h-11 rounded-2xl flex items-center justify-center transition-all"
              :class="acMode === 'dry' ? 'bg-[#213840] hover:bg-[#284550] text-[#00bcd4]' : 'bg-[#292c34] hover:bg-[#323640] text-neutral-300 hover:text-white'"
              aria-label="除湿"
            >
              <AppIcon name="water_drop" :size="20" />
            </button>

            <button
              type="button"
              @click="emit('setAcMode', 'cool')"
              class="h-11 rounded-2xl flex items-center justify-center transition-all"
              :class="acMode === 'cool' ? 'bg-[#253546] hover:bg-[#2e4156] text-[#2196f3]' : 'bg-[#292c34] hover:bg-[#323640] text-neutral-400 hover:text-white'"
              aria-label="冷房"
            >
              <AppIcon name="ac_unit" :size="20" />
            </button>
          </div>
        </div>

        <!-- ヒータータイル (統一 Material Symbols: hvac) -->
        <div
          @click="emit('openSheet', 'heater-sheet')"
          class="group relative bg-[#1c1e23] hover:bg-[#23262d] rounded-3xl p-3.5 flex items-center space-x-3.5 cursor-pointer transition-colors duration-150 shadow-md border border-white/[0.03]"
        >
          <button
            type="button"
            @click.stop="emit('toggleHeaterPower')"
            class="w-11 h-11 rounded-full flex items-center justify-center transition-all duration-300 hover:scale-105 active:scale-95 shrink-0"
            :class="heaterMode === 'heat' ? 'bg-[#3a2c24] text-[#ea7a1e]' : 'bg-[#272a31] text-neutral-400'"
            aria-label="ヒーターのオン/オフ切り替え"
          >
            <AppIcon name="hvac" :size="24" />
          </button>

          <div class="flex-1">
            <div class="text-[15px] font-semibold text-white leading-tight">ヒーター</div>
            <div class="text-xs text-neutral-400 font-normal mt-0.5 transition-colors">
              <span v-if="heaterMode === 'off'">オフ</span>
              <span v-else>暖房・{{ heaterTemp }}℃</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- セクション: 掃除 -->
    <section class="break-inside-avoid mb-6 space-y-3">
      <h2 class="text-base font-bold text-white px-1">掃除</h2>
      
      <div class="flex flex-col gap-3.5">
        <!-- クリーナータイル (統一 MDI: vacuum) -->
        <div
          @click="emit('openSheet', 'cleaner-sheet')"
          class="group relative bg-[#1c1e23] hover:bg-[#23262d] rounded-3xl p-3.5 space-y-3 cursor-pointer transition-colors duration-150 shadow-md border border-white/[0.03]"
        >
          <div class="flex items-center space-x-3.5">
            <button
              type="button"
              @click.stop="emit('toggleCleanerPower')"
              class="w-11 h-11 rounded-full flex items-center justify-center transition-all duration-300 hover:scale-105 active:scale-95 shrink-0"
              :class="isCleanerRunning() ? 'bg-[#253546] text-[#2196f3] shadow-sm' : 'bg-[#272a31] text-neutral-400'"
              aria-label="クリーナーの開始/停止切り替え"
            >
              <AppIcon name="vacuum" :size="24" />
            </button>
            <div class="flex-1">
              <div class="text-[15px] font-semibold text-white leading-tight">クリーナー</div>
              <div
                class="text-xs font-normal mt-0.5 transition-colors"
                :class="isCleanerRunning() ? 'text-sky-400' : 'text-neutral-400'"
              >
                {{ getCleanerStatusText() }}
              </div>
            </div>
          </div>

          <!-- 下部操作ボタングループ (起動、一時停止、停止) -->
          <div class="grid grid-cols-3 gap-2 pt-0.5" @click.stop>
            <button
              type="button"
              @click="emit('setCleanerMode', 'start')"
              class="h-11 rounded-2xl flex items-center justify-center transition-all active:scale-95"
              :class="isCleanerRunning() ? 'bg-[#253546] hover:bg-[#2e4156] text-[#2196f3]' : 'bg-[#292c34] hover:bg-[#323640] text-neutral-400 hover:text-white'"
              aria-label="起動"
            >
              <AppIcon name="play" :size="20" />
            </button>

            <button
              type="button"
              @click="emit('setCleanerMode', 'pause')"
              class="h-11 rounded-2xl flex items-center justify-center transition-all active:scale-95"
              :class="cleanerStatus === 'standby' ? 'bg-[#333741] hover:bg-[#3c414d] text-white' : 'bg-[#292c34] hover:bg-[#323640] text-neutral-400 hover:text-white'"
              aria-label="一時停止"
            >
              <AppIcon name="pause" :size="20" />
            </button>

            <button
              type="button"
              @click="emit('setCleanerMode', 'stop')"
              class="h-11 rounded-2xl flex items-center justify-center transition-all active:scale-95"
              :class="cleanerStatus === 'recharge' ? 'bg-[#253546] hover:bg-[#2e4156] text-[#2196f3]' : 'bg-[#292c34] hover:bg-[#323640] text-neutral-400 hover:text-white'"
              aria-label="停止"
            >
              <AppIcon name="home" :size="20" />
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- セクション: スイッチ -->
    <section class="break-inside-avoid mb-6 space-y-3">
      <h2 class="text-base font-bold text-white px-1">スイッチ</h2>
      
      <div class="flex flex-col gap-3.5">
        <!-- デスクトップPCタイル -->
        <div
          @click="emit('openSheet', 'pc-sheet')"
          class="group relative bg-[#1c1e23] hover:bg-[#23262d] rounded-3xl p-3.5 flex items-center space-x-3.5 cursor-pointer transition-colors duration-150 shadow-md border border-white/[0.03]"
        >
          <button
            type="button"
            @click.stop="emit('togglePcPower')"
            class="w-11 h-11 rounded-full flex items-center justify-center transition-all duration-300 hover:scale-105 active:scale-95 shrink-0 cursor-pointer"
            :class="[
              pcBooting ? (pcTargetOs === 'Bazzite' ? 'bg-[#251f35] text-[#c084fc] animate-slow-pulse' : 'bg-[#1e293b] text-[#4a88e8] animate-slow-pulse') :
              pcShuttingDown ? 'bg-[#272a31] text-neutral-400 animate-slow-pulse' :
              pcOnline ? (pcOs === 'Bazzite' || pcTargetOs === 'Bazzite' ? 'bg-[#251f35] text-[#c084fc]' : 'bg-[#1e293b] text-[#4a88e8]') :
              'bg-[#272a31] text-neutral-400'
            ]"
            aria-label="デスクトップPCの電源オン/オフ切り替え"
          >
            <AppIcon :name="getPcIcon()" :size="24" />
          </button>

          <div class="flex-1 select-none">
            <div class="text-[15px] font-semibold text-white leading-tight">デスクトップPC</div>
            <div class="text-xs text-neutral-400 font-normal mt-0.5 transition-colors">
              {{ getPcStatusText() }}
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- セクション: センサー -->
    <section class="break-inside-avoid mb-6 space-y-3">
      <h2 class="text-base font-bold text-white px-1">センサー</h2>
      
      <div class="flex flex-col gap-3.5">
        <!-- 1. 気象タイル -->
        <div
          @click="emit('openSheet', 'weather-sheet')"
          class="group relative bg-[#1c1e23] hover:bg-[#23262d] rounded-3xl p-3.5 flex items-center space-x-3.5 cursor-pointer transition-colors duration-150 shadow-md border border-white/[0.03] active:scale-[0.98]"
        >
          <div class="w-11 h-11 rounded-full bg-[#272a31] text-sky-400 flex items-center justify-center transition-all duration-300 group-hover:scale-105 shrink-0">
            <AppIcon :name="weather.weather_icon || 'partly_cloudy_day'" :size="24" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-[15px] font-semibold text-white leading-tight">気象</div>
            <div class="text-xs text-neutral-400 font-normal mt-0.5 truncate transition-colors">
              {{ weather.weather !== '--' ? `${weather.weather}・${weather.temp}℃` : '-- / --.-℃' }}
            </div>
          </div>
        </div>

        <!-- 2. 在宅確認センサータイル -->
        <div
          @click="emit('openSheet', 'presence-sheet')"
          class="group relative bg-[#1c1e23] hover:bg-[#23262d] rounded-3xl p-3.5 flex items-center space-x-3.5 cursor-pointer transition-colors duration-150 shadow-md border border-white/[0.03] active:scale-[0.98]"
        >
          <div
            class="w-11 h-11 rounded-full flex items-center justify-center transition-all duration-300 group-hover:scale-105 shrink-0"
            :class="presence.is_home ? 'bg-[#1b332b] text-emerald-400' : 'bg-[#272a31] text-neutral-400'"
          >
            <AppIcon name="home_pin" :size="24" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-[15px] font-semibold text-white leading-tight">在宅確認</div>
            <div class="text-xs text-neutral-400 font-normal mt-0.5 truncate transition-colors">
              {{ presence.is_home ? '在宅' : '不在' }}
            </div>
          </div>
        </div>

        <!-- 3. 鍵（Tile）センサータイル -->
        <div
          @click="emit('openSheet', 'tile-sheet')"
          class="group relative bg-[#1c1e23] hover:bg-[#23262d] rounded-3xl p-3.5 flex items-center space-x-3.5 cursor-pointer transition-colors duration-150 shadow-md border border-white/[0.03] active:scale-[0.98]"
        >
          <div
            class="w-11 h-11 rounded-full flex items-center justify-center transition-all duration-300 group-hover:scale-105 shrink-0"
            :class="tile.in_home ? 'bg-[#3d2d1d] text-amber-400' : 'bg-[#272a31] text-neutral-400'"
          >
            <AppIcon :name="tile.in_home ? 'vpn_key_alert' : 'key'" :size="24" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-[15px] font-semibold text-white leading-tight">鍵</div>
            <div class="text-xs text-neutral-400 font-normal mt-0.5 truncate transition-colors">
              {{ tile.in_home ? '検知' : '検知なし' }}
            </div>
          </div>
        </div>
      </div>
    </section>

  </main>
</template>
