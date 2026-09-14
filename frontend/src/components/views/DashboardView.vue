<script setup lang="ts">
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
            <span class="material-symbols-rounded text-2xl">lightbulb</span>
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
          <!-- 上部情報 -->
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
              <svg class="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 4H5c-1.1 0-2 .9-2 2v4c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 6H5V6h14v4z"/>
                <rect x="17" y="7.5" width="1.5" height="1.5" rx="0.75" />
                <path d="M6 15c.8-.5 1.7-.5 2.5 0 .8.5 1.7.5 2.5 0 .8.5 1.7.5 2.5 0 .8.5 1.7.5 2.5 0" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                <path d="M4.5 18c1.1-.6 2.4-.6 3.5 0 1.1.6 2.4.6 3.5 0 1.1.6 2.4.6 3.5 0 1.1.6 2.4.6 3.5 0" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
              </svg>
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
            >
              <span class="material-symbols-rounded text-[22px]">power_settings_new</span>
            </button>

            <button
              type="button"
              @click="emit('setAcMode', 'dry')"
              class="h-11 rounded-2xl flex items-center justify-center transition-all"
              :class="acMode === 'dry' ? 'bg-[#213840] hover:bg-[#284550] text-[#00bcd4]' : 'bg-[#292c34] hover:bg-[#323640] text-neutral-300 hover:text-white'"
            >
              <span class="material-symbols-rounded symbol-fill text-[22px]">water_drop</span>
            </button>

            <button
              type="button"
              @click="emit('setAcMode', 'cool')"
              class="h-11 rounded-2xl flex items-center justify-center transition-all"
              :class="acMode === 'cool' ? 'bg-[#253546] hover:bg-[#2e4156] text-[#2196f3]' : 'bg-[#292c34] hover:bg-[#323640] text-neutral-400 hover:text-white'"
            >
              <span class="material-symbols-rounded text-[22px]">ac_unit</span>
            </button>
          </div>
        </div>

        <!-- ヒータータイル -->
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
            <svg class="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
              <path d="M4 6c-1.1 0-2 .9-2 2v9c0 1.1.9 2 2 2h1v1a1 1 0 0 0 2 0v-1h10v1a1 1 0 0 0 2 0v-1h1c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2H4zm0 2h16v9H4V8z"/>
              <rect x="6" y="10" width="2" height="5" rx="1"/>
              <rect x="9.5" y="10" width="2" height="5" rx="1"/>
              <rect x="13" y="10" width="2" height="5" rx="1"/>
              <rect x="16.5" y="10" width="2" height="5" rx="1"/>
            </svg>
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
        <!-- クリーナータイル -->
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
              <svg class="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18.2A8.2 8.2 0 1 1 20.2 12 8.21 8.21 0 0 1 12 20.2z"/>
                <path d="M4.8 9.2a8 8 0 0 1 14.4 0" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                <circle cx="12" cy="6.2" r="1.4"/>
                <circle cx="12" cy="13.5" r="2.6"/>
                <circle cx="12" cy="13.5" r="1.1" fill="#1c1e23"/>
              </svg>
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
              <span class="material-symbols-rounded text-[22px]">play_arrow</span>
            </button>

            <button
              type="button"
              @click="emit('setCleanerMode', 'pause')"
              class="h-11 rounded-2xl flex items-center justify-center transition-all active:scale-95"
              :class="cleanerStatus === 'standby' ? 'bg-[#333741] hover:bg-[#3c414d] text-white' : 'bg-[#292c34] hover:bg-[#323640] text-neutral-400 hover:text-white'"
              aria-label="一時停止"
            >
              <span class="material-symbols-rounded text-[22px]">pause</span>
            </button>

            <button
              type="button"
              @click="emit('setCleanerMode', 'stop')"
              class="h-11 rounded-2xl flex items-center justify-center transition-all active:scale-95"
              :class="cleanerStatus === 'recharge' ? 'bg-[#253546] hover:bg-[#2e4156] text-[#2196f3]' : 'bg-[#292c34] hover:bg-[#323640] text-neutral-400 hover:text-white'"
              aria-label="停止"
            >
              <span class="material-symbols-rounded text-[22px]">home</span>
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
            <span class="material-symbols-rounded text-2xl">{{ getPcIcon() }}</span>
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
            <span class="material-symbols-rounded text-2xl">{{ weather.weather_icon || 'partly_cloudy_day' }}</span>
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
            <span class="material-symbols-rounded text-2xl">home_pin</span>
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
            <span class="material-symbols-rounded text-2xl">{{ tile.in_home ? 'vpn_key_alert' : 'key' }}</span>
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
