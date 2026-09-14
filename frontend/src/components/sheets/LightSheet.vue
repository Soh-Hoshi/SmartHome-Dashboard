<script setup lang="ts">
import { ref } from 'vue'
import SheetModal from '../common/SheetModal.vue'

const props = defineProps<{
  lightOn: boolean
  lightBrightness: number
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'toggle'): void
  (e: 'selectAction', action: 'full' | 'night'): void
  (e: 'changeBrightness', delta: number): void
}>()

const openActionDropup = ref(false)

function handleSelectAction(action: 'full' | 'night') {
  openActionDropup.value = false
  emit('selectAction', action)
}
</script>

<template>
  <SheetModal title="リビング" @close="emit('close')">
    <!-- 中央: オン/オフ表示 ＆ 縦型スイッチスライダー -->
    <div class="flex-1 flex flex-col items-center justify-center my-auto py-2 shrink-0">
      <div class="text-3xl font-bold tracking-tight text-white mb-4 transition-all duration-300">
        {{ lightOn ? 'オン' : 'オフ' }}
      </div>
      
      <div
        @click.stop="emit('toggle')"
        class="slider-track relative w-[120px] h-[240px] rounded-[34px] overflow-hidden p-2 cursor-pointer shadow-inner shrink-0 transition-colors duration-300"
        :class="lightOn ? 'bg-[#443717]' : 'bg-[#282b32]'"
      >
        <div
          class="slider-thumb absolute inset-x-2 bottom-2 h-[112px] rounded-[26px] flex items-center justify-center text-white transition-all duration-300"
          :class="lightOn ? 'translate-y-[-112px] bg-[#fbc02d] shadow-[0_6px_18px_rgba(0,0,0,0.35)]' : 'translate-y-0 bg-[#434752] shadow-md'"
        >
          <div class="transition-transform duration-300 flex items-center justify-center">
            <span v-if="lightOn" class="material-symbols-rounded text-2xl text-white">power_settings_new</span>
            <div v-else class="w-5 h-5 rounded-full border-2 border-neutral-300"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 最下部コントロールエリア (1段目: アクション、2段目: 明るさ) -->
    <div class="relative space-y-2.5 pt-1">
      <!-- 1段目: アクション ドロップアップ -->
      <div class="relative">
        <div
          v-show="openActionDropup"
          class="dropup-menu open absolute bottom-full mb-3 left-0 w-56 bg-[#262932] border border-white/10 rounded-2xl p-1.5 shadow-2xl z-30 backdrop-blur-xl"
          @click.stop
        >
          <div class="text-[11px] font-semibold text-neutral-400 px-3 py-1.5 uppercase tracking-wider">アクション</div>
          <div class="space-y-0.5">
            <button
              type="button"
              @click="handleSelectAction('full')"
              class="w-full h-10 flex items-center space-x-3 px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
            >
              <span class="material-symbols-rounded text-xl text-neutral-300">light_mode</span>
              <span class="text-white">全灯</span>
            </button>
            <button
              type="button"
              @click="handleSelectAction('night')"
              class="w-full h-10 flex items-center space-x-3 px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
            >
              <span class="material-symbols-rounded text-xl text-neutral-300">bedtime</span>
              <span class="text-white">常夜灯</span>
            </button>
          </div>
        </div>

        <!-- アクション トリガーボタン (統一高さ h-[58px]) -->
        <button
          type="button"
          @click.stop="openActionDropup = !openActionDropup"
          class="w-full h-[58px] flex items-center space-x-3 px-4 rounded-2xl bg-[#2a2d36] hover:bg-[#323640] text-left transition-all shadow-sm border border-white/[0.04] active:scale-[0.98]"
          aria-label="アクションを選択"
        >
          <div class="text-neutral-400 shrink-0 flex items-center justify-center">
            <span class="material-symbols-rounded text-2xl">light_mode</span>
          </div>
          <div class="overflow-hidden leading-tight flex-1">
            <div class="text-[14px] font-semibold text-white truncate">アクション</div>
          </div>
          <span class="material-symbols-rounded text-lg text-neutral-400 shrink-0">expand_less</span>
        </button>
      </div>

      <!-- 2段目: 明るさ ［ー］ ［＋］ (統一高さ h-[58px]) -->
      <div class="w-full h-[58px] bg-[#2a2d36] rounded-2xl px-4 flex items-center justify-between shadow-sm border border-white/[0.04]">
        <div class="flex items-center space-x-3">
          <span
            class="material-symbols-rounded text-2xl shrink-0 transition-colors"
            :class="lightOn ? 'text-amber-400' : 'text-neutral-400'"
          >brightness_medium</span>
          <div class="overflow-hidden leading-tight flex-1">
            <div class="text-[14px] font-semibold text-white">明るさ</div>
          </div>
        </div>

        <div class="flex items-center space-x-2 bg-[#1e2025] p-1 rounded-xl border border-white/5">
          <button
            type="button"
            :disabled="!lightOn"
            @click.stop="emit('changeBrightness', -1)"
            class="w-9 h-9 rounded-lg bg-[#2b2e37] hover:bg-[#373b46] active:bg-[#404552] flex items-center justify-center text-white transition-all active:scale-95 disabled:opacity-30 disabled:pointer-events-none"
            aria-label="明るさを下げる"
          >
            <span class="material-symbols-rounded text-lg font-bold">remove</span>
          </button>

          <button
            type="button"
            :disabled="!lightOn"
            @click.stop="emit('changeBrightness', 1)"
            class="w-9 h-9 rounded-lg bg-[#2b2e37] hover:bg-[#373b46] active:bg-[#404552] flex items-center justify-center text-white transition-all active:scale-95 disabled:opacity-30 disabled:pointer-events-none"
            aria-label="明るさを上げる"
          >
            <span class="material-symbols-rounded text-lg font-bold">add</span>
          </button>
        </div>
      </div>
    </div>
  </SheetModal>
</template>
