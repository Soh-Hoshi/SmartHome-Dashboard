<script setup lang="ts">
import { ref, computed } from 'vue'
import SheetModal from '../common/SheetModal.vue'
import AppIcon from '../common/AppIcon.vue'
import SheetButton from '../common/SheetButton.vue'

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
            <AppIcon v-if="isSwitchActive" name="power" :size="24" class="text-white" />
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
              <AppIcon name="sleep" :size="20" class="text-neutral-300" />
              <span class="text-white">スリープ</span>
            </button>
            <button
              type="button"
              @click="handleSelectPowerOption('restart')"
              class="w-full h-10 flex items-center space-x-3 px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
            >
              <AppIcon name="restart" :size="20" class="text-neutral-300" />
              <span class="text-white">再起動</span>
            </button>
          </div>
        </div>

        <!-- 電源オプション トリガーボタン -->
        <SheetButton
          label="電源オプション"
          icon="power"
          :hasDropdown="true"
          @click="toggleDropup('power', $event)"
        />
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
                <AppIcon name="desktop_windows" :size="20" />
                <span class="text-white">Windows</span>
              </div>
              <span v-if="targetOs === 'Windows'" class="text-[#4a88e8] shrink-0 w-5 h-5 flex items-center justify-center">
                <AppIcon name="check" :size="18" />
              </span>
            </button>

            <button
              type="button"
              @click="handleSelectOs('Bazzite')"
              class="w-full h-10 flex items-center justify-between px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
            >
              <div class="flex items-center space-x-3 text-[#c084fc]">
                <AppIcon name="sports_esports" :size="20" />
                <span class="text-white">Bazzite</span>
              </div>
              <span v-if="targetOs === 'Bazzite'" class="text-[#c084fc] shrink-0 w-5 h-5 flex items-center justify-center">
                <AppIcon name="check" :size="18" />
              </span>
            </button>
          </div>
        </div>

        <!-- 起動OS トリガーボタン -->
        <SheetButton
          sublabel="起動OS"
          :label="targetOs"
          :icon="targetOs === 'Windows' ? 'desktop_windows' : 'sports_esports'"
          :iconColor="targetOs === 'Windows' ? 'text-[#4a88e8]' : 'text-[#c084fc]'"
          :hasDropdown="true"
          @click="toggleDropup('os', $event)"
        />
      </div>
    </div>
  </SheetModal>
</template>
