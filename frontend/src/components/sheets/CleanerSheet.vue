<script setup lang="ts">
import { ref } from 'vue'
import SheetModal from '../common/SheetModal.vue'
import AppIcon from '../common/AppIcon.vue'
import SheetButton from '../common/SheetButton.vue'

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
  emit('selectAction', action)
  openDropup.value = null
}

function handleSelectSpeed(s: 'Standard' | 'Boost_IQ' | 'Max') {
  emit('selectSpeed', s)
  openDropup.value = null
}

function getStatusText() {
  switch (props.status) {
    case 'running': return '清掃中'
    case 'charging': return '充電中'
    case 'standby': return '待機中'
    case 'sleeping': return 'スリープ'
    case 'recharge': return '帰還中'
    case 'completed': return '完了'
    default: return '待機中'
  }
}

function isRunning() {
  return props.status === 'running'
}

function isCharging() {
  return props.status === 'charging'
}

const speedLabelMap = {
  Standard: '標準',
  Boost_IQ: '自動',
  Max: '最大'
}
</script>

<template>
  <SheetModal title="ロボット掃除機" :scrollable="true" @close="emit('close')">
    <!-- 中央: ステータスリング ＆ アナリティクス -->
    <div class="flex-1 flex flex-col items-center justify-center my-auto relative space-y-4 py-2 shrink-0">
      <!-- 円形ステータスカード -->
      <div class="relative w-48 h-48 rounded-full bg-[#242730] border border-white/[0.05] flex flex-col items-center justify-center shadow-xl overflow-hidden shrink-0">
        <!-- ロボット掃除機アイコン (Material Symbols: vacuum_2) -->
        <div
          class="relative z-10 transition-colors duration-300"
          :class="[
            isRunning() ? 'text-[#2196f3] animate-pulse' :
            isCharging() ? 'text-amber-400' :
            'text-neutral-400'
          ]"
        >
          <AppIcon name="vacuum_2" :size="64" />
        </div>

        <!-- 中央ステータステキスト ＆ バッテリー残量 -->
        <div class="relative z-10 mt-2 text-center space-y-0.5">
          <div class="text-2xl font-bold text-white tracking-wide">
            {{ getStatusText() }}
          </div>
          <div class="flex items-center justify-center space-x-1 text-sm font-semibold text-neutral-300 font-num pt-0.5">
            <AppIcon
              :name="isCharging() ? 'battery_charging_full' : 'battery_full'"
              :size="14"
              :class="isCharging() ? 'text-[#2196f3]' : 'text-neutral-400'"
            />
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
              <AppIcon name="play" :size="20" class="text-neutral-300" />
              <span class="text-white">開始</span>
            </button>
            <button
              type="button"
              @click="handleSelectAction('pause')"
              class="w-full h-10 flex items-center space-x-3 px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
            >
              <AppIcon name="pause" :size="20" class="text-neutral-300" />
              <span class="text-white">停止</span>
            </button>
            <button
              type="button"
              @click="handleSelectAction('stop')"
              class="w-full h-10 flex items-center space-x-3 px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
            >
              <AppIcon name="home" :size="20" class="text-neutral-300" />
              <span class="text-white">ホーム</span>
            </button>
          </div>
        </div>

        <SheetButton
          label="アクション"
          icon="play_circle"
          :hasDropdown="true"
          @click="toggleDropup('action', $event)"
        />
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
                  <AppIcon name="air" :size="20" />
                  <span class="text-white">標準</span>
                </div>
                <span v-if="speed === 'Standard'" class="text-[#2196f3] shrink-0 w-5 h-5 flex items-center justify-center">
                  <AppIcon name="check" :size="18" />
                </span>
              </button>

              <button
                type="button"
                @click="handleSelectSpeed('Boost_IQ')"
                class="w-full h-10 flex items-center justify-between px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
              >
                <div class="flex items-center space-x-3 text-neutral-300">
                  <AppIcon name="speed_boost" :size="20" />
                  <span class="text-white">BoostIQ</span>
                </div>
                <span v-if="speed === 'Boost_IQ'" class="text-[#2196f3] shrink-0 w-5 h-5 flex items-center justify-center">
                  <AppIcon name="check" :size="18" />
                </span>
              </button>

              <button
                type="button"
                @click="handleSelectSpeed('Max')"
                class="w-full h-10 flex items-center justify-between px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
              >
                <div class="flex items-center space-x-3 text-neutral-300">
                  <AppIcon name="rocket_launch" :size="20" />
                  <span class="text-white">最大</span>
                </div>
                <span v-if="speed === 'Max'" class="text-[#2196f3] shrink-0 w-5 h-5 flex items-center justify-center">
                  <AppIcon name="check" :size="18" />
                </span>
              </button>
            </div>
          </div>

          <!-- 吸引力 トリガーボタン -->
          <SheetButton
            sublabel="吸引力"
            :label="speedLabelMap[speed] || '標準'"
            icon="air"
            :hasDropdown="true"
            @click="toggleDropup('speed', $event)"
          />
        </div>

        <!-- Find Me ボタン -->
        <SheetButton
          label="探す"
          icon="missing_controller"
          @click="emit('pressFindMe')"
        />
      </div>
    </div>
  </SheetModal>
</template>
