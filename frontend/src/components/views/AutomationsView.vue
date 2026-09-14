<script setup lang="ts">
const emit = defineEmits<{
  (e: 'runAutomation', id: string): void
}>()
</script>

<template>
  <div id="view-automations" class="tab-view w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 columns-1 md:columns-2 lg:columns-3 gap-6">
    <!-- セクション: デイリー -->
    <section class="break-inside-avoid mb-6 space-y-3">
      <h2 class="text-base font-bold text-white px-1">デイリー</h2>
      
      <div class="flex flex-col gap-3.5">
        <!-- オートメーション1: 平日 6:30 -->
        <div class="group relative bg-[#1c1e23] rounded-3xl p-3.5 flex items-center justify-between shadow-md border border-white/[0.03]">
          <div class="flex items-center space-x-3.5 min-w-0">
            <div class="w-11 h-11 rounded-full bg-[#272a31] text-amber-400 flex items-center justify-center shrink-0">
              <span class="material-symbols-rounded text-2xl">alarm</span>
            </div>
            <div class="text-[15px] font-semibold text-white leading-tight truncate">平日 6:30</div>
          </div>
          <button
            type="button"
            @click="emit('runAutomation', 'weekday_morning_light')"
            class="w-10 h-10 rounded-full bg-[#272a31] hover:bg-[#343842] text-white flex items-center justify-center transition-all duration-200 hover:scale-110 active:scale-95 shrink-0 shadow-sm border border-white/[0.04]"
            aria-label="平日 6:30を実行"
          >
            <span class="material-symbols-rounded text-xl text-neutral-200">play_arrow</span>
          </button>
        </div>

        <!-- オートメーション2: 平日 9:00 (Material Symbols: vacuum) -->
        <div class="group relative bg-[#1c1e23] rounded-3xl p-3.5 flex items-center justify-between shadow-md border border-white/[0.03]">
          <div class="flex items-center space-x-3.5 min-w-0">
            <div class="w-11 h-11 rounded-full bg-[#272a31] text-[#2196f3] flex items-center justify-center shrink-0">
              <span class="material-symbols-rounded text-2xl">vacuum</span>
            </div>
            <div class="text-[15px] font-semibold text-white leading-tight truncate">平日 9:00</div>
          </div>
          <button
            type="button"
            @click="emit('runAutomation', 'weekday_morning_cleaner')"
            class="w-10 h-10 rounded-full bg-[#272a31] hover:bg-[#343842] text-white flex items-center justify-center transition-all duration-200 hover:scale-110 active:scale-95 shrink-0 shadow-sm border border-white/[0.04]"
            aria-label="平日 9:00を実行"
          >
            <span class="material-symbols-rounded text-xl text-neutral-200">play_arrow</span>
          </button>
        </div>
      </div>
    </section>

    <!-- セクション: 外出 -->
    <section class="break-inside-avoid mb-6 space-y-3">
      <h2 class="text-base font-bold text-white px-1">外出</h2>
      
      <div class="flex flex-col gap-3.5">
        <!-- オートメーション3: 外出時 -->
        <div class="group relative bg-[#1c1e23] rounded-3xl p-3.5 flex items-center justify-between shadow-md border border-white/[0.03]">
          <div class="flex items-center space-x-3.5 min-w-0">
            <div class="w-11 h-11 rounded-full bg-[#272a31] text-rose-400 flex items-center justify-center shrink-0">
              <span class="material-symbols-rounded text-2xl">person_off</span>
            </div>
            <div class="text-[15px] font-semibold text-white leading-tight truncate">外出時</div>
          </div>
          <button
            type="button"
            @click="emit('runAutomation', 'away_device_warning')"
            class="w-10 h-10 rounded-full bg-[#272a31] hover:bg-[#343842] text-white flex items-center justify-center transition-all duration-200 hover:scale-110 active:scale-95 shrink-0 shadow-sm border border-white/[0.04]"
            aria-label="外出時をテスト実行"
          >
            <span class="material-symbols-rounded text-xl text-neutral-200">play_arrow</span>
          </button>
        </div>
      </div>
    </section>
  </div>
</template>
