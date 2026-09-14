<script setup lang="ts">
import { ref, computed } from 'vue'

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
          <h2 class="text-xl font-bold text-white tracking-tight">エアコン</h2>
        </div>
        <div></div>
      </div>

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
              <span class="material-symbols-rounded text-2xl font-bold">remove</span>
            </button>

            <button
              type="button"
              @click.stop="emit('changeTemp', 1)"
              class="w-11 h-11 rounded-full bg-[#2a2d36] hover:bg-[#343844] border border-white/[0.05] flex items-center justify-center text-white transition-all shadow-sm active:scale-95 shrink-0"
              aria-label="温度を上げる"
            >
              <span class="material-symbols-rounded text-2xl font-bold">add</span>
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
                  <span class="material-symbols-rounded text-xl">ac_unit</span>
                  <span class="text-white">冷房</span>
                </div>
                <span v-if="mode === 'cool'" class="text-[#2196f3] flex items-center justify-center shrink-0 w-5 h-5">
                  <span class="material-symbols-rounded symbol-bold text-lg leading-none">check</span>
                </span>
              </button>

              <button
                type="button"
                @click="handleSelectMode('dry')"
                class="w-full h-10 flex items-center justify-between px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
              >
                <div class="flex items-center space-x-3 text-[#00bcd4]">
                  <span class="material-symbols-rounded symbol-fill text-xl">water_drop</span>
                  <span class="text-white">除湿</span>
                </div>
                <span v-if="mode === 'dry'" class="text-[#00bcd4] flex items-center justify-center shrink-0 w-5 h-5">
                  <span class="material-symbols-rounded symbol-bold text-lg leading-none">check</span>
                </span>
              </button>

              <div class="h-px bg-white/10 my-1"></div>

              <button
                type="button"
                @click="handleSelectMode('off')"
                class="w-full h-10 flex items-center justify-between px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
              >
                <div class="flex items-center space-x-3 text-neutral-400">
                  <span class="material-symbols-rounded text-xl">power_settings_new</span>
                  <span class="text-neutral-300">オフ</span>
                </div>
                <span v-if="mode === 'off'" class="text-neutral-400 flex items-center justify-center shrink-0 w-5 h-5">
                  <span class="material-symbols-rounded symbol-bold text-lg leading-none">check</span>
                </span>
              </button>
            </div>
          </div>

          <!-- モード トリガーボタン -->
          <button
            type="button"
            @click="toggleDropup('mode', $event)"
            class="w-full h-[58px] flex items-center space-x-3 px-4 rounded-2xl bg-[#2a2d36] hover:bg-[#323640] text-left transition-all shadow-sm border border-white/[0.04] active:scale-[0.98]"
          >
            <div class="shrink-0 flex items-center justify-center" :class="mode === 'cool' ? 'text-[#2196f3]' : mode === 'dry' ? 'text-[#00bcd4]' : 'text-neutral-400'">
              <span class="material-symbols-rounded text-2xl">
                {{ mode === 'cool' ? 'ac_unit' : mode === 'dry' ? 'water_drop' : 'power_settings_new' }}
              </span>
            </div>
            <div class="overflow-hidden leading-tight flex-1">
              <div class="text-xs text-neutral-400 font-normal">モード</div>
              <div class="text-[14px] font-semibold text-white truncate mt-0.5">
                {{ mode === 'cool' ? '冷房' : mode === 'dry' ? '除湿' : 'オフ' }}
              </div>
            </div>
            <span class="material-symbols-rounded text-lg text-neutral-400 shrink-0">expand_less</span>
          </button>
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
                <div class="flex items-center space-x-3 text-neutral-200">
                  <div class="w-5 h-5 flex items-center justify-center shrink-0">
                    <svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 11a1 1 0 1 0 1 1 1 1 0 0 0-1-1zm0-9a4 4 0 0 0-4 4 1 1 0 0 0 2 0 2 2 0 0 1 4 0c0 1.5-1.5 2.5-2 3.5v.5h1.5c1.5 0 2.5-1.5 3.5-2a4 4 0 0 0-5-6zm-6 9a2 2 0 0 1 0-4 4 4 0 0 0-4 4 1 1 0 0 0 2 0 2 2 0 0 1 2 0zm14.5 4h-1.1l-.4 1.2h-1.3l1.8-5h1.4l1.8 5h-1.3zm-.4-1.2l-.4-1.4-.4 1.4zM12 15a4 4 0 0 0 4-4 1 1 0 0 0-2 0 2 2 0 0 1-4 0c0-1.5 1.5-2.5 2-3.5v-.5h-1.5c-1.5 0-2.5 1.5-3.5 2a4 4 0 0 0 5 6z"/>
                    </svg>
                  </div>
                  <span>自動</span>
                </div>
                <span v-if="fan === 'auto'" class="text-sky-400 flex items-center justify-center shrink-0 w-5 h-5">
                  <span class="material-symbols-rounded symbol-bold text-lg leading-none">check</span>
                </span>
              </button>

              <!-- 弱 -->
              <button
                type="button"
                @click="handleSelectFan('low')"
                class="w-full h-10 flex items-center justify-between px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
              >
                <div class="flex items-center space-x-3 text-neutral-200">
                  <div class="w-5 h-5 flex items-center justify-center shrink-0">
                    <svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                      <circle cx="12" cy="12" r="2.5"/>
                      <path d="M12 4a3.5 3.5 0 0 0-3.5 3.5 1 1 0 0 0 2 0 1.5 1.5 0 0 1 3 0c0 1-1 1.8-1.5 2.5h1.5c1 0 2-1 2.5-2a3.5 3.5 0 0 0-4-4zm-8 8a3.5 3.5 0 0 0 3.5-3.5 1 1 0 0 0 0 2 1.5 1.5 0 0 1 0 3c-1 0-1.8-1-2.5-1.5v1.5c0 1 1 2 2 2.5a3.5 3.5 0 0 0-3-7.5zm8 8a3.5 3.5 0 0 0 3.5-3.5 1 1 0 0 0-2 0 1.5 1.5 0 0 1-3 0c0-1 1-1.8 1.5-2.5h-1.5c-1 0-2 1-2.5 2a3.5 3.5 0 0 0 4 4z"/>
                      <rect x="19" y="16" width="3" height="4" rx="1" fill="#38bdf8"/>
                    </svg>
                  </div>
                  <span>弱</span>
                </div>
                <span v-if="fan === 'low'" class="text-sky-400 flex items-center justify-center shrink-0 w-5 h-5">
                  <span class="material-symbols-rounded symbol-bold text-lg leading-none">check</span>
                </span>
              </button>

              <!-- 中 -->
              <button
                type="button"
                @click="handleSelectFan('medium')"
                class="w-full h-10 flex items-center justify-between px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
              >
                <div class="flex items-center space-x-3 text-neutral-200">
                  <div class="w-5 h-5 flex items-center justify-center shrink-0">
                    <svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                      <circle cx="12" cy="12" r="2.5"/>
                      <path d="M12 4a3.5 3.5 0 0 0-3.5 3.5 1 1 0 0 0 2 0 1.5 1.5 0 0 1 3 0c0 1-1 1.8-1.5 2.5h1.5c1 0 2-1 2.5-2a3.5 3.5 0 0 0-4-4zm-8 8a3.5 3.5 0 0 0 3.5-3.5 1 1 0 0 0 0 2 1.5 1.5 0 0 1 0 3c-1 0-1.8-1-2.5-1.5v1.5c0 1 1 2 2 2.5a3.5 3.5 0 0 0-3-7.5zm8 8a3.5 3.5 0 0 0 3.5-3.5 1 1 0 0 0-2 0 1.5 1.5 0 0 1-3 0c0-1 1-1.8 1.5-2.5h-1.5c-1 0-2 1-2.5 2a3.5 3.5 0 0 0 4 4z"/>
                      <rect x="17.5" y="14" width="2.5" height="6" rx="1" fill="#38bdf8"/>
                      <rect x="21" y="11" width="2.5" height="9" rx="1" fill="#38bdf8"/>
                    </svg>
                  </div>
                  <span>中</span>
                </div>
                <span v-if="fan === 'medium'" class="text-sky-400 flex items-center justify-center shrink-0 w-5 h-5">
                  <span class="material-symbols-rounded symbol-bold text-lg leading-none">check</span>
                </span>
              </button>

              <!-- 強 -->
              <button
                type="button"
                @click="handleSelectFan('high')"
                class="w-full h-10 flex items-center justify-between px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
              >
                <div class="flex items-center space-x-3 text-neutral-200">
                  <div class="w-5 h-5 flex items-center justify-center shrink-0">
                    <svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                      <circle cx="12" cy="12" r="2.5"/>
                      <path d="M12 4a3.5 3.5 0 0 0-3.5 3.5 1 1 0 0 0 2 0 1.5 1.5 0 0 1 3 0c0 1-1 1.8-1.5 2.5h1.5c1 0 2-1 2.5-2a3.5 3.5 0 0 0-4-4zm-8 8a3.5 3.5 0 0 0 3.5-3.5 1 1 0 0 0 0 2 1.5 1.5 0 0 1 0 3c-1 0-1.8-1-2.5-1.5v1.5c0 1 1 2 2 2.5a3.5 3.5 0 0 0-3-7.5zm8 8a3.5 3.5 0 0 0 3.5-3.5 1 1 0 0 0-2 0 1.5 1.5 0 0 1-3 0c0-1 1-1.8 1.5-2.5h-1.5c-1 0-2 1-2.5 2a3.5 3.5 0 0 0 4 4z"/>
                      <rect x="14" y="16" width="2.5" height="4" rx="1" fill="#38bdf8"/>
                      <rect x="17.5" y="13" width="2.5" height="7" rx="1" fill="#38bdf8"/>
                      <rect x="21" y="9" width="2.5" height="11" rx="1" fill="#38bdf8"/>
                    </svg>
                  </div>
                  <span>強</span>
                </div>
                <span v-if="fan === 'high'" class="text-sky-400 flex items-center justify-center shrink-0 w-5 h-5">
                  <span class="material-symbols-rounded symbol-bold text-lg leading-none">check</span>
                </span>
              </button>
            </div>
          </div>

          <!-- ファンモード トリガーボタン -->
          <button
            type="button"
            @click="toggleDropup('fan', $event)"
            class="w-full h-[58px] flex items-center space-x-3 px-4 rounded-2xl bg-[#2a2d36] hover:bg-[#323640] text-left transition-all shadow-sm border border-white/[0.04] active:scale-[0.98]"
          >
            <div class="text-neutral-200 shrink-0 flex items-center justify-center">
              <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 11a1 1 0 1 0 1 1 1 1 0 0 0-1-1zm0-9a4 4 0 0 0-4 4 1 1 0 0 0 2 0 2 2 0 0 1 4 0c0 1.5-1.5 2.5-2 3.5v.5h1.5c1.5 0 2.5-1.5 3.5-2a4 4 0 0 0-5-6zm-6 9a2 2 0 0 1 0-4 4 4 0 0 0-4 4 1 1 0 0 0 2 0 2 2 0 0 1 2 0zm14.5 4h-1.1l-.4 1.2h-1.3l1.8-5h1.4l1.8 5h-1.3zm-.4-1.2l-.4-1.4-.4 1.4zM12 15a4 4 0 0 0 4-4 1 1 0 0 0-2 0 2 2 0 0 1-4 0c0-1.5 1.5-2.5 2-3.5v-.5h-1.5c-1.5 0-2.5 1.5-3.5 2a4 4 0 0 0 5 6z"/>
              </svg>
            </div>
            <div class="overflow-hidden leading-tight flex-1">
              <div class="text-xs text-neutral-400 font-normal">ファンモード</div>
              <div class="text-[14px] font-semibold text-white truncate mt-0.5">
                {{ fan === 'auto' ? '自動' : fan === 'low' ? '弱' : fan === 'medium' ? '中' : '強' }}
              </div>
            </div>
            <span class="material-symbols-rounded text-lg text-neutral-400 shrink-0">expand_less</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
