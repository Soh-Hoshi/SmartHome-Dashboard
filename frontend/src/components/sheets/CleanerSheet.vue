<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  status: string
  play: boolean
  timeMin: number
  area: number
  battery: number
  mop: boolean
  speed: 'Standard' | 'Boost_IQ' | 'Max'
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'selectAction', action: 'start' | 'pause' | 'stop'): void
  (e: 'selectSpeed', speed: 'Standard' | 'Boost_IQ' | 'Max'): void
  (e: 'pressFindMe'): void
}>()

const openDropup = ref<'action' | 'speed' | null>(null)

function toggleDropup(menu: 'action' | 'speed', e: MouseEvent) {
  e.stopPropagation()
  openDropup.value = openDropup.value === menu ? null : menu
}

function handleSelectAction(action: 'start' | 'pause' | 'stop') {
  openDropup.value = null
  emit('selectAction', action)
}

function handleSelectSpeed(s: 'Standard' | 'Boost_IQ' | 'Max') {
  openDropup.value = null
  emit('selectSpeed', s)
}

function getStatusText() {
  const st = (props.status || '').toLowerCase()
  if (st === 'running' && props.play) return '清掃中'
  if (st === 'charging') return '充電中'
  if (st === 'recharge') return '帰還中'
  if (st === 'standby') return '一時停止中'
  if (st === 'completed') return '充電完了'
  return '待機中'
}

function isRunning() {
  return (props.status || '').toLowerCase() === 'running' && props.play
}

function isRecharging() {
  return (props.status || '').toLowerCase() === 'recharge'
}

function isCharging() {
  return (props.status || '').toLowerCase() === 'charging'
}

const speedLabelMap = {
  Standard: '標準',
  Boost_IQ: 'BoostIQ',
  Max: '最大',
}
</script>

<template>
  <div
    class="sheet-backdrop visible-sheet fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/65 backdrop-blur-sm"
    @click="emit('close')"
  >
    <div
      class="bottom-sheet relative w-full max-w-lg sm:max-w-[460px] h-[calc(100dvh-36px)] sm:h-[min(720px,calc(100dvh-48px))] sm:min-h-[580px] max-h-[calc(100dvh-24px)] bg-[#1e2025] rounded-t-[32px] sm:rounded-[36px] flex flex-col justify-between p-5 pt-6 pb-6 overflow-visible shadow-2xl border-t sm:border border-white/[0.06]"
      @click.stop="openDropup = null"
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
          <h2 class="text-xl font-bold text-white tracking-tight">クリーナー</h2>
        </div>
        <div></div>
      </div>

      <!-- 中央: ロボット掃除機ステータスビジュアル -->
      <div class="flex-1 flex flex-col items-center justify-center my-auto relative space-y-4 py-2 shrink-0">
        <!-- 円形ステータスカード -->
        <div class="relative w-48 h-48 rounded-full bg-[#242730] border border-white/[0.05] flex flex-col items-center justify-center shadow-xl overflow-hidden shrink-0">
          <!-- ロボット掃除機アイコン -->
          <div
            class="relative z-10 transition-colors duration-300"
            :class="[
              isRunning() ? 'text-[#38bdf8] animate-cleaner-moving' :
              isRecharging() ? 'text-neutral-400 animate-cleaner-moving' :
              'text-neutral-400'
            ]"
          >
            <svg class="w-12 h-12" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18.2A8.2 8.2 0 1 1 20.2 12 8.21 8.21 0 0 1 12 20.2z"/>
              <path d="M4.8 9.2a8 8 0 0 1 14.4 0" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
              <circle cx="12" cy="6.2" r="1.4"/>
              <circle cx="12" cy="13.5" r="2.6"/>
              <circle cx="12" cy="13.5" r="1.1" fill="#1c1e23"/>
            </svg>
          </div>

          <!-- 中央ステータステキスト ＆ バッテリー残量 -->
          <div class="relative z-10 mt-2 text-center space-y-0.5">
            <div class="text-2xl font-bold text-white tracking-wide">
              {{ getStatusText() }}
            </div>
            <div class="flex items-center justify-center space-x-1.5 text-sm font-semibold text-neutral-300 font-num pt-0.5">
              <span
                class="material-symbols-rounded text-base"
                :class="isCharging() ? 'text-[#2196f3]' : 'text-neutral-300'"
              >
                {{ isCharging() ? 'battery_charging_full' : 'battery_full' }}
              </span>
              <span>{{ battery }}%</span>
            </div>
          </div>
        </div>

        <!-- 3つの情報チップス (時間、面積、モップ) -->
        <div class="grid grid-cols-3 gap-2.5 w-72 shrink-0">
          <div class="bg-[#242730]/90 border border-white/[0.04] rounded-2xl py-2 px-2 text-center shadow-sm">
            <div class="text-[10px] text-neutral-400 font-normal">清掃時間</div>
            <div class="text-sm font-bold text-neutral-200 font-num mt-0.5">
              <template v-if="isRunning() || status === 'standby'">
                {{ timeMin }}<span class="text-[11px] font-normal text-neutral-400 ml-0.5">分</span>
              </template>
              <template v-else>
                --<span class="text-[11px] font-normal text-neutral-400 ml-0.5">分</span>
              </template>
            </div>
          </div>

          <div class="bg-[#242730]/90 border border-white/[0.04] rounded-2xl py-2 px-2 text-center shadow-sm">
            <div class="text-[10px] text-neutral-400 font-normal">清掃面積</div>
            <div class="text-sm font-bold text-neutral-200 font-num mt-0.5">
              <template v-if="isRunning() || status === 'standby'">
                {{ area }}<span class="text-[11px] font-normal text-neutral-400 ml-0.5">㎡</span>
              </template>
              <template v-else>
                --<span class="text-[11px] font-normal text-neutral-400 ml-0.5">㎡</span>
              </template>
            </div>
          </div>

          <div class="bg-[#242730]/90 border border-white/[0.04] rounded-2xl py-2 px-2 text-center shadow-sm">
            <div class="text-[10px] text-neutral-400 font-normal">モップ</div>
            <div class="text-sm font-bold mt-0.5" :class="mop ? 'text-sky-400' : 'text-neutral-300'">
              {{ mop ? '装着中' : '未装着' }}
            </div>
          </div>
        </div>
      </div>

      <!-- 最下部コントロールエリア (統一高さ h-[58px]) -->
      <div class="relative space-y-2.5 pt-1">
        <!-- 1段目: アクション ドロップアップ -->
        <div class="relative">
          <div
            v-show="openDropup === 'action'"
            class="dropup-menu open absolute bottom-full mb-3 left-0 w-56 bg-[#262932] border border-white/10 rounded-2xl p-1.5 shadow-2xl z-30 backdrop-blur-xl"
            @click.stop
          >
            <div class="text-[11px] font-semibold text-neutral-400 px-3 py-1.5 uppercase tracking-wider">アクション</div>
            <div class="space-y-0.5">
              <button
                type="button"
                @click="handleSelectAction('start')"
                class="w-full h-10 flex items-center space-x-3 px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
              >
                <span class="material-symbols-rounded text-xl text-neutral-300">play_arrow</span>
                <span class="text-white">開始</span>
              </button>
              <button
                type="button"
                @click="handleSelectAction('pause')"
                class="w-full h-10 flex items-center space-x-3 px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
              >
                <span class="material-symbols-rounded text-xl text-neutral-300">pause</span>
                <span class="text-white">停止</span>
              </button>
              <button
                type="button"
                @click="handleSelectAction('stop')"
                class="w-full h-10 flex items-center space-x-3 px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
              >
                <span class="material-symbols-rounded text-xl text-neutral-300">home</span>
                <span class="text-white">ホーム</span>
              </button>
            </div>
          </div>

          <button
            type="button"
            @click="toggleDropup('action', $event)"
            class="w-full h-[58px] flex items-center space-x-3 px-4 rounded-2xl bg-[#2a2d36] hover:bg-[#323640] text-left transition-all shadow-sm border border-white/[0.04] active:scale-[0.98]"
            aria-label="アクションを選択"
          >
            <div class="text-neutral-400 shrink-0 flex items-center justify-center">
              <span class="material-symbols-rounded text-2xl">play_circle</span>
            </div>
            <div class="overflow-hidden leading-tight flex-1">
              <div class="text-[14px] font-semibold text-white truncate">アクション</div>
            </div>
            <span class="material-symbols-rounded text-lg text-neutral-400 shrink-0">expand_less</span>
          </button>
        </div>

        <!-- 2段目: 吸引力 & Find Me ボタン -->
        <div class="grid grid-cols-2 gap-3">
          <!-- 吸引力 ドロップアップ -->
          <div class="relative">
            <div
              v-show="openDropup === 'speed'"
              class="dropup-menu open absolute bottom-full mb-3 left-0 w-56 bg-[#262932] border border-white/10 rounded-2xl p-1.5 shadow-2xl z-30 backdrop-blur-xl"
              @click.stop
            >
              <div class="text-[11px] font-semibold text-neutral-400 px-3 py-1.5 uppercase tracking-wider">吸引力</div>
              <div class="space-y-0.5">
                <button
                  type="button"
                  @click="handleSelectSpeed('Standard')"
                  class="w-full h-10 flex items-center justify-between px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
                >
                  <div class="flex items-center space-x-3 text-neutral-300">
                    <span class="material-symbols-rounded text-xl">air</span>
                    <span class="text-white">標準</span>
                  </div>
                  <span v-if="speed === 'Standard'" class="text-[#2196f3] shrink-0 w-5 h-5 flex items-center justify-center">
                    <span class="material-symbols-rounded symbol-bold text-lg leading-none">check</span>
                  </span>
                </button>

                <button
                  type="button"
                  @click="handleSelectSpeed('Boost_IQ')"
                  class="w-full h-10 flex items-center justify-between px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
                >
                  <div class="flex items-center space-x-3 text-neutral-300">
                    <span class="material-symbols-rounded text-xl">speed</span>
                    <span class="text-white">BoostIQ</span>
                  </div>
                  <span v-if="speed === 'Boost_IQ'" class="text-[#2196f3] shrink-0 w-5 h-5 flex items-center justify-center">
                    <span class="material-symbols-rounded symbol-bold text-lg leading-none">check</span>
                  </span>
                </button>

                <button
                  type="button"
                  @click="handleSelectSpeed('Max')"
                  class="w-full h-10 flex items-center justify-between px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
                >
                  <div class="flex items-center space-x-3 text-neutral-300">
                    <span class="material-symbols-rounded text-xl">rocket_launch</span>
                    <span class="text-white">最大</span>
                  </div>
                  <span v-if="speed === 'Max'" class="text-[#2196f3] shrink-0 w-5 h-5 flex items-center justify-center">
                    <span class="material-symbols-rounded symbol-bold text-lg leading-none">check</span>
                  </span>
                </button>
              </div>
            </div>

            <!-- 吸引力 トリガーボタン -->
            <button
              type="button"
              @click="toggleDropup('speed', $event)"
              class="w-full h-[58px] flex items-center space-x-3 px-4 rounded-2xl bg-[#2a2d36] hover:bg-[#323640] text-left transition-all shadow-sm border border-white/[0.04] active:scale-[0.98]"
            >
              <div class="text-neutral-400 shrink-0 flex items-center justify-center">
                <span class="material-symbols-rounded text-2xl">air</span>
              </div>
              <div class="overflow-hidden leading-tight flex-1">
                <div class="text-xs text-neutral-400 font-normal">吸引力</div>
                <div class="text-[14px] font-semibold text-white truncate mt-0.5">
                  {{ speedLabelMap[speed] || '標準' }}
                </div>
              </div>
              <span class="material-symbols-rounded text-lg text-neutral-400 shrink-0">expand_less</span>
            </button>
          </div>

          <!-- Find Me ボタン -->
          <button
            type="button"
            @click.stop="emit('pressFindMe')"
            class="w-full h-[58px] flex items-center space-x-3 px-4 rounded-2xl bg-[#2a2d36] hover:bg-[#323640] text-left transition-all shadow-sm border border-white/[0.04] active:scale-[0.98]"
          >
            <div class="text-neutral-400 shrink-0 flex items-center justify-center">
              <span class="material-symbols-rounded text-2xl">notifications_active</span>
            </div>
            <div class="overflow-hidden leading-tight flex-1">
              <div class="text-[14px] font-semibold text-white truncate">探す</div>
            </div>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
