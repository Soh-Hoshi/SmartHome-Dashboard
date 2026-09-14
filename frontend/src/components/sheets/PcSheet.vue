<script setup lang="ts">
import { ref, computed } from 'vue'
import SheetModal from '../common/SheetModal.vue'

const props = defineProps<{
  online: boolean
  booting: boolean
  shuttingDown: boolean
  os: string
  targetOs: 'Windows' | 'Bazzite'
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'togglePower'): void
  (e: 'selectPowerOption', action: 'sleep' | 'restart'): void
  (e: 'selectOs', os: 'Windows' | 'Bazzite'): void
}>()

const openDropup = ref<'power' | 'os' | null>(null)

function toggleDropup(menu: 'power' | 'os', e: MouseEvent) {
  e.stopPropagation()
  openDropup.value = openDropup.value === menu ? null : menu
}

function handleSelectPowerOption(action: 'sleep' | 'restart') {
  openDropup.value = null
  emit('selectPowerOption', action)
}

function handleSelectOs(os: 'Windows' | 'Bazzite') {
  openDropup.value = null
  emit('selectOs', os)
}

const isBooting = computed(() => props.booting || props.os === '起動中')
const isShuttingDown = computed(() => props.shuttingDown || props.os === '終了中')
const isSwitchActive = computed(() => isBooting.value || (props.online && !isShuttingDown.value))

const isBazziteActive = computed(() => {
  if (isBooting.value) return props.targetOs === 'Bazzite'
  if (props.online && !isShuttingDown.value) {
    return (props.os === 'Bazzite') || props.targetOs === 'Bazzite'
  }
  return props.targetOs === 'Bazzite'
})

const sheetBackgroundStyle = computed(() => {
  if (isSwitchActive.value && isBazziteActive.value) {
    return 'radial-gradient(ellipse at 50% 0%, rgba(192, 132, 252, 0.12) 0%, rgba(30, 32, 37, 1) 75%)'
  } else if (isSwitchActive.value) {
    return 'radial-gradient(ellipse at 50% 0%, rgba(74, 136, 232, 0.10) 0%, rgba(30, 32, 37, 1) 75%)'
  } else if (props.targetOs === 'Bazzite') {
    return 'radial-gradient(ellipse at 50% 0%, rgba(192, 132, 252, 0.05) 0%, rgba(30, 32, 37, 1) 75%)'
  }
  return undefined
})

const sliderTrackBg = computed(() => {
  if (!isSwitchActive.value) return '#282b32'
  return isBazziteActive.value ? '#311f4d' : '#192e4d'
})
</script>

<template>
  <SheetModal
    title="デスクトップPC"
    :backgroundStyle="sheetBackgroundStyle"
    @close="emit('close')"
  >
    <!-- 中央: オン/オフ表示 ＆ 縦型スイッチスライダー -->
    <div class="flex-1 flex flex-col items-center justify-center my-auto py-2 shrink-0">
      <div class="text-3xl font-bold tracking-tight text-white mb-4 transition-all duration-300">
        {{ isSwitchActive ? 'オン' : 'オフ' }}
      </div>
      
      <div
        @click.stop="emit('togglePower')"
        class="slider-track relative w-[120px] h-[240px] rounded-[34px] overflow-hidden p-2 cursor-pointer shadow-inner shrink-0 transition-colors duration-300"
        :style="{ backgroundColor: sliderTrackBg }"
      >
        <div
          class="slider-thumb absolute inset-x-2 bottom-2 h-[112px] rounded-[26px] flex items-center justify-center text-white transition-all duration-300"
          :class="[
            isSwitchActive
              ? (isBazziteActive ? 'translate-y-[-112px] bg-[#c084fc] shadow-lg shadow-purple-500/30' : 'translate-y-[-112px] bg-[#4a88e8] shadow-lg shadow-blue-500/25')
              : 'translate-y-0 bg-[#434752] shadow-md',
            (isBooting || isShuttingDown) ? 'animate-slow-pulse' : ''
          ]"
        >
          <div class="transition-transform duration-300 flex items-center justify-center">
            <span v-if="isSwitchActive" class="material-symbols-rounded text-2xl text-white">power_settings_new</span>
            <div v-else class="w-5 h-5 rounded-full border-2 border-neutral-300"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 最下部コントロールエリア (1段目: 電源オプション、2段目: 起動OS) -->
    <div class="relative space-y-2.5 pt-1 shrink-0">
      <!-- 1段目: 電源オプション ドロップアップ -->
      <div class="relative">
        <div
          v-show="openDropup === 'power'"
          class="dropup-menu open absolute bottom-full mb-3 left-0 w-56 bg-[#262932] border border-white/10 rounded-2xl p-1.5 shadow-2xl z-30 backdrop-blur-xl"
          @click.stop
        >
          <div class="text-[11px] font-semibold text-neutral-400 px-3 py-1.5 uppercase tracking-wider">電源オプション</div>
          <div class="space-y-0.5">
            <button
              type="button"
              @click="handleSelectPowerOption('sleep')"
              class="w-full h-10 flex items-center space-x-3 px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
            >
              <span class="material-symbols-rounded text-xl text-neutral-300">bedtime</span>
              <span class="text-white">スリープ</span>
            </button>
            <button
              type="button"
              @click="handleSelectPowerOption('restart')"
              class="w-full h-10 flex items-center space-x-3 px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
            >
              <span class="material-symbols-rounded text-xl text-neutral-300">restart_alt</span>
              <span class="text-white">再起動</span>
            </button>
          </div>
        </div>

        <!-- 電源オプション トリガーボタン (統一高さ h-[58px]) -->
        <button
          type="button"
          @click="toggleDropup('power', $event)"
          class="w-full h-[58px] flex items-center space-x-3 px-4 rounded-2xl bg-[#2a2d36] hover:bg-[#323640] text-left transition-all shadow-sm border border-white/[0.04] active:scale-[0.98]"
          aria-label="電源オプションを選択"
        >
          <div class="text-neutral-400 shrink-0 flex items-center justify-center">
            <span class="material-symbols-rounded text-2xl">power_settings_new</span>
          </div>
          <div class="overflow-hidden leading-tight flex-1">
            <div class="text-[14px] font-semibold text-white truncate">電源オプション</div>
          </div>
          <span class="material-symbols-rounded text-lg text-neutral-400 shrink-0">expand_less</span>
        </button>
      </div>

      <!-- 2段目: 起動OS ドロップアップ -->
      <div class="relative">
        <div
          v-show="openDropup === 'os'"
          class="dropup-menu open absolute bottom-full mb-3 left-0 w-56 bg-[#262932] border border-white/10 rounded-2xl p-1.5 shadow-2xl z-30 backdrop-blur-xl"
          @click.stop
        >
          <div class="text-[11px] font-semibold text-neutral-400 px-3 py-1.5 uppercase tracking-wider">起動OS</div>
          <div class="space-y-0.5">
            <button
              type="button"
              @click="handleSelectOs('Windows')"
              class="w-full h-10 flex items-center justify-between px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
            >
              <div class="flex items-center space-x-3 text-[#4a88e8]">
                <span class="material-symbols-rounded text-xl">desktop_windows</span>
                <span class="text-white">Windows</span>
              </div>
              <span v-if="targetOs === 'Windows'" class="text-[#4a88e8] shrink-0 w-5 h-5 flex items-center justify-center">
                <span class="material-symbols-rounded symbol-bold text-lg leading-none">check</span>
              </span>
            </button>

            <button
              type="button"
              @click="handleSelectOs('Bazzite')"
              class="w-full h-10 flex items-center justify-between px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
            >
              <div class="flex items-center space-x-3 text-[#c084fc]">
                <span class="material-symbols-rounded text-xl">sports_esports</span>
                <span class="text-white">Bazzite</span>
              </div>
              <span v-if="targetOs === 'Bazzite'" class="text-[#c084fc] shrink-0 w-5 h-5 flex items-center justify-center">
                <span class="material-symbols-rounded symbol-bold text-lg leading-none">check</span>
              </span>
            </button>
          </div>
        </div>

        <!-- 起動OS トリガーボタン (統一高さ h-[58px]) -->
        <button
          type="button"
          @click="toggleDropup('os', $event)"
          class="w-full h-[58px] flex items-center space-x-3 px-4 rounded-2xl bg-[#2a2d36] hover:bg-[#323640] text-left transition-all shadow-sm border border-white/[0.04] active:scale-[0.98]"
          aria-label="起動OSを選択"
        >
          <div
            class="shrink-0 flex items-center justify-center"
            :class="targetOs === 'Windows' ? 'text-[#4a88e8]' : 'text-[#c084fc]'"
          >
            <span class="material-symbols-rounded text-2xl">
              {{ targetOs === 'Windows' ? 'desktop_windows' : 'sports_esports' }}
            </span>
          </div>
          <div class="overflow-hidden leading-tight flex-1">
            <div class="text-xs text-neutral-400 font-normal">起動OS</div>
            <div class="text-[14px] font-semibold text-white truncate mt-0.5">
              {{ targetOs }}
            </div>
          </div>
          <span class="material-symbols-rounded text-lg text-neutral-400 shrink-0">expand_less</span>
        </button>
      </div>
    </div>
  </SheetModal>
</template>
