<script setup lang="ts">
import { ref, computed } from 'vue'
import SheetModal from '../common/SheetModal.vue'
import AppIcon from '../common/AppIcon.vue'
import SheetButton from '../common/SheetButton.vue'

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
  <SheetModal title="ヒーター" @close="emit('close')">
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
            <AppIcon name="remove" :size="24" />
          </button>

          <button
            type="button"
            @click.stop="emit('changeTemp', 1)"
            class="w-11 h-11 rounded-full bg-[#2a2d36] hover:bg-[#343844] border border-white/[0.05] flex items-center justify-center text-white transition-all shadow-sm active:scale-95 shrink-0"
            aria-label="温度を上げる"
          >
            <AppIcon name="add" :size="24" />
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
                <AppIcon name="mode_heat" :size="20" />
                <span class="text-white">暖房</span>
              </div>
              <span v-if="mode === 'heat'" class="text-[#f57c00] flex items-center justify-center shrink-0 w-5 h-5">
                <AppIcon name="check" :size="18" />
              </span>
            </button>

            <div class="h-px bg-white/10 my-1"></div>

            <button
              type="button"
              @click="handleSelectMode('off')"
              class="w-full h-10 flex items-center justify-between px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
            >
              <div class="flex items-center space-x-3 text-neutral-400">
                <AppIcon name="power" :size="20" />
                <span class="text-neutral-300">オフ</span>
              </div>
              <span v-if="mode === 'off'" class="text-neutral-400 flex items-center justify-center shrink-0 w-5 h-5">
                <AppIcon name="check" :size="18" />
              </span>
            </button>
          </div>
        </div>

        <!-- モード トリガーボタン -->
        <SheetButton
          sublabel="モード"
          :label="mode === 'heat' ? '暖房' : 'オフ'"
          :icon="mode === 'heat' ? 'mode_heat' : 'power'"
          :iconColor="mode === 'heat' ? 'text-[#f57c00]' : 'text-neutral-400'"
          :hasDropdown="true"
          @click.stop="openModeDropup = !openModeDropup"
        />
      </div>

      <!-- 2段目: エコ & パワー ボタン -->
      <div class="grid grid-cols-2 gap-3">
        <SheetButton
          label="エコ"
          icon="eco"
          :disabled="mode === 'off'"
          @click.stop="emit('pressEco')"
        />

        <SheetButton
          label="パワー"
          icon="bolt"
          :disabled="mode === 'off'"
          @click.stop="emit('pressPower')"
        />
      </div>
    </div>
  </SheetModal>
</template>
