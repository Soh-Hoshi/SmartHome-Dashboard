<script setup lang="ts">
import { ref, computed } from 'vue'
import SheetModal from '../common/SheetModal.vue'
import AppIcon from '../common/AppIcon.vue'
import SheetButton from '../common/SheetButton.vue'

const props = defineProps<{
  temp: number
  mode: 'cool' | 'dry' | 'off'
  fan: 'auto' | 'low' | 'medium' | 'high'
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'changeTemp', delta: number): void
  (e: 'selectMode', mode: 'cool' | 'dry' | 'off'): void
  (e: 'selectFan', fan: 'auto' | 'low' | 'medium' | 'high'): void
}>()

const modeLabel = computed(() => {
  switch (props.mode) {
    case 'cool': return '冷房'
    case 'dry': return '除湿'
    default: return 'オフ'
  }
})

const modeIconName = computed(() => {
  switch (props.mode) {
    case 'cool': return 'mode_cool'
    case 'dry': return 'water_drop'
    default: return 'power'
  }
})

const modeIconColor = computed(() => {
  switch (props.mode) {
    case 'cool': return 'text-[#2196f3]'
    case 'dry': return 'text-[#00bcd4]'
    default: return 'text-neutral-400'
  }
})

const fanLabel = computed(() => {
  switch (props.fan) {
    case 'low': return '弱'
    case 'medium': return '中'
    case 'high': return '強'
    default: return '自動'
  }
})

const fanIconName = computed(() => {
  switch (props.fan) {
    case 'low': return 'fan_speed_1'
    case 'medium': return 'fan_speed_2'
    case 'high': return 'fan_speed_3'
    default: return 'fan_auto'
  }
})

// --- ドロップアップ状態 ---
const openDropup = ref<'mode' | 'fan' | null>(null)

function toggleDropup(menu: 'mode' | 'fan', e: MouseEvent) {
  e.stopPropagation()
  openDropup.value = openDropup.value === menu ? null : menu
}

function handleSelectMode(m: 'cool' | 'dry' | 'off') {
  openDropup.value = null
  emit('selectMode', m)
}

function handleSelectFan(f: 'auto' | 'low' | 'medium' | 'high') {
  openDropup.value = null
  emit('selectFan', f)
}

// --- 蹄型ゲージ計算 ---
const minTemp = 22
const maxTemp = 28
const totalArcLength = 494.8

const ratio = computed(() => {
  return Math.max(0, Math.min(1, (props.temp - minTemp) / (maxTemp - minTemp)))
})

const visibleLength = computed(() => totalArcLength * ratio.value)

const knobPos = computed(() => {
  const startAngle = 135
  const currentAngleDeg = startAngle + ratio.value * 270
  const currentAngleRad = currentAngleDeg * (Math.PI / 180)
  return {
    x: (140 + 105 * Math.cos(currentAngleRad)).toFixed(2),
    y: (140 + 105 * Math.sin(currentAngleRad)).toFixed(2),
  }
})

// --- ドラッグ操作 ---
const svgRef = ref<SVGSVGElement | null>(null)
let isDragging = false

function handlePointerDown(e: PointerEvent) {
  if (!svgRef.value) return
  isDragging = true
  svgRef.value.setPointerCapture(e.pointerId)
  updateFromPointer(e)
}

function handlePointerMove(e: PointerEvent) {
  if (!isDragging || !svgRef.value) return
  updateFromPointer(e)
}

function handlePointerUp(e: PointerEvent) {
  if (!isDragging || !svgRef.value) return
  isDragging = false
  try { svgRef.value.releasePointerCapture(e.pointerId) } catch (err) {}
}

function updateFromPointer(e: PointerEvent) {
  if (!svgRef.value) return
  const rect = svgRef.value.getBoundingClientRect()
  const x = ((e.clientX - rect.left) / rect.width) * 280
  const y = ((e.clientY - rect.top) / rect.height) * 280

  const dx = x - 140
  const dy = y - 140
  let angle = Math.atan2(dy, dx) * (180 / Math.PI)
  if (angle < 0) angle += 360

  let mappedAngle: number
  if (angle >= 135) {
    mappedAngle = angle
  } else if (angle <= 45) {
    mappedAngle = angle + 360
  } else {
    mappedAngle = angle < 90 ? 405 : 135
  }

  const dragRatio = Math.max(0, Math.min(1, (mappedAngle - 135) / 270))
  const newTemp = Math.round(minTemp + dragRatio * (maxTemp - minTemp))
  const delta = newTemp - props.temp
  if (delta !== 0) {
    emit('changeTemp', delta)
  }
}
</script>

<template>
  <SheetModal title="エアコン" @close="emit('close')">
    <!-- 中央: 蹄型 (Horseshoe) 温度ゲージ & 純白ノブ -->
    <div class="flex-1 flex flex-col items-center justify-center my-auto relative py-2 shrink-0">
      <div class="relative w-72 h-72 flex items-center justify-center shrink-0">
        <!-- SVG 蹄型ゲージ (22℃ 〜 28℃) -->
        <svg
          ref="svgRef"
          class="w-full h-full cursor-pointer touch-none select-none"
          viewBox="0 0 280 280"
          @pointerdown="handlePointerDown"
          @pointermove="handlePointerMove"
          @pointerup="handlePointerUp"
          @pointercancel="handlePointerUp"
        >
          <!-- 蹄型 背景トラック -->
          <path
            d="M 65.75 214.25 A 105 105 0 1 1 214.25 214.25"
            fill="none"
            :stroke="mode === 'cool' ? 'rgba(33, 150, 243, 0.15)' : mode === 'dry' ? 'rgba(0, 188, 212, 0.15)' : 'rgba(255, 255, 255, 0.05)'"
            stroke-width="24"
            stroke-linecap="round"
          />

          <!-- アクティブなカラーアーク -->
          <path
            v-if="mode !== 'off'"
            d="M 65.75 214.25 A 105 105 0 1 1 214.25 214.25"
            fill="none"
            :stroke="mode === 'cool' ? '#2196f3' : '#00bcd4'"
            stroke-width="24"
            stroke-linecap="round"
            :stroke-dasharray="`${visibleLength} ${totalArcLength}`"
            stroke-dashoffset="0"
          />

          <!-- ドラッグ可能なノブ -->
          <g v-if="mode !== 'off'" class="cursor-grab active:cursor-grabbing">
            <circle :cx="knobPos.x" :cy="knobPos.y" r="22" fill="transparent" />
            <circle
              :cx="knobPos.x"
              :cy="knobPos.y"
              r="9.5"
              fill="#e2e8f0"
              class="drop-shadow-md"
            />
          </g>
        </svg>

        <!-- 円の中央テキスト情報 -->
        <div class="absolute inset-0 flex flex-col items-center justify-center text-center select-none pointer-events-none pb-4">
          <template v-if="mode === 'off'">
            <span class="text-5xl font-bold tracking-tight text-white leading-none translate-y-1.5">オフ</span>
          </template>
          <template v-else>
            <span class="text-sm font-medium text-neutral-300 mb-1 tracking-wide">
              {{ mode === 'cool' ? '冷房' : '除湿' }}
            </span>
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

    <!-- 最下部: ドロップアップ切り替えボタン (モード & ファンモード) -->
    <div class="relative grid grid-cols-2 gap-3 pt-2">
      <!-- モード ドロップアップ -->
      <div class="relative">
        <div
          v-show="openDropup === 'mode'"
          class="dropup-menu open absolute bottom-full mb-3 left-0 w-56 bg-[#262932] border border-white/10 rounded-2xl p-1.5 shadow-2xl z-30 backdrop-blur-xl"
          @click.stop
        >
          <div class="text-[11px] font-semibold text-neutral-400 px-3 py-1.5 uppercase tracking-wider">モード</div>
          <div class="space-y-0.5">
            <button
              type="button"
              @click="handleSelectMode('cool')"
              class="w-full h-10 flex items-center justify-between px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
            >
              <div class="flex items-center space-x-3 text-[#2196f3]">
                <AppIcon name="mode_cool" :size="20" />
                <span class="text-white">冷房</span>
              </div>
              <span v-if="mode === 'cool'" class="text-[#2196f3] flex items-center justify-center shrink-0 w-5 h-5">
                <AppIcon name="check" :size="18" />
              </span>
            </button>

            <button
              type="button"
              @click="handleSelectMode('dry')"
              class="w-full h-10 flex items-center justify-between px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
            >
              <div class="flex items-center space-x-3 text-[#00bcd4]">
                <AppIcon name="water_drop" :size="20" />
                <span class="text-white">除湿</span>
              </div>
              <span v-if="mode === 'dry'" class="text-[#00bcd4] flex items-center justify-center shrink-0 w-5 h-5">
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
          :label="modeLabel"
          :icon="modeIconName"
          :iconColor="modeIconColor"
          :hasDropdown="true"
          @click="toggleDropup('mode', $event)"
        />
      </div>

      <!-- ファンモード ドロップアップ -->
      <div class="relative">
        <div
          v-show="openDropup === 'fan'"
          class="dropup-menu open absolute bottom-full mb-3 right-0 w-56 bg-[#262932] border border-white/10 rounded-2xl p-1.5 shadow-2xl z-30 backdrop-blur-xl"
          @click.stop
        >
          <div class="text-[11px] font-semibold text-neutral-400 px-3 py-1.5 uppercase tracking-wider">ファンモード</div>
          <div class="space-y-0.5">
            <!-- 自動 -->
            <button
              type="button"
              @click="handleSelectFan('auto')"
              class="w-full h-10 flex items-center justify-between px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
            >
              <div class="flex items-center space-x-3 text-neutral-300">
                <AppIcon name="fan_auto" :size="20" />
                <span class="text-white">自動</span>
              </div>
              <span v-if="fan === 'auto'" class="text-sky-400 flex items-center justify-center shrink-0 w-5 h-5">
                <AppIcon name="check" :size="18" />
              </span>
            </button>

            <!-- 弱 -->
            <button
              type="button"
              @click="handleSelectFan('low')"
              class="w-full h-10 flex items-center justify-between px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
            >
              <div class="flex items-center space-x-3 text-neutral-300">
                <AppIcon name="fan_speed_1" :size="20" />
                <span class="text-white">弱</span>
              </div>
              <span v-if="fan === 'low'" class="text-sky-400 flex items-center justify-center shrink-0 w-5 h-5">
                <AppIcon name="check" :size="18" />
              </span>
            </button>

            <!-- 中 -->
            <button
              type="button"
              @click="handleSelectFan('medium')"
              class="w-full h-10 flex items-center justify-between px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
            >
              <div class="flex items-center space-x-3 text-neutral-300">
                <AppIcon name="fan_speed_2" :size="20" />
                <span class="text-white">中</span>
              </div>
              <span v-if="fan === 'medium'" class="text-sky-400 flex items-center justify-center shrink-0 w-5 h-5">
                <AppIcon name="check" :size="18" />
              </span>
            </button>

            <!-- 強 -->
            <button
              type="button"
              @click="handleSelectFan('high')"
              class="w-full h-10 flex items-center justify-between px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
            >
              <div class="flex items-center space-x-3 text-neutral-300">
                <AppIcon name="fan_speed_3" :size="20" />
                <span class="text-white">強</span>
              </div>
              <span v-if="fan === 'high'" class="text-sky-400 flex items-center justify-center shrink-0 w-5 h-5">
                <AppIcon name="check" :size="18" />
              </span>
            </button>
          </div>
        </div>

        <!-- ファンモード トリガーボタン -->
        <SheetButton
          sublabel="ファンモード"
          :label="fanLabel"
          :icon="fanIconName"
          iconColor="text-neutral-400"
          :hasDropdown="true"
          @click="toggleDropup('fan', $event)"
        />
      </div>
    </div>
  </SheetModal>
</template>
