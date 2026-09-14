<script setup lang="ts">
const emit = defineEmits<{
  (e: 'runScene', name: string): void
}>()
</script>

<template>
  <div id="view-scenes" class="tab-view w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 columns-1 md:columns-2 lg:columns-3 gap-6">
    <!-- セクション: デイリー -->
    <section class="break-inside-avoid mb-6 space-y-3">
      <h2 class="text-base font-bold text-white px-1">デイリー</h2>
      
      <div class="flex flex-col gap-3.5">
        <!-- シーン1: おはよう -->
        <div class="group relative bg-[#1c1e23] rounded-3xl p-3.5 flex items-center justify-between shadow-md border border-white/[0.03]">
          <div class="flex items-center space-x-3.5 min-w-0">
            <div class="w-11 h-11 rounded-full bg-[#272a31] text-amber-400 flex items-center justify-center shrink-0">
              <span class="material-symbols-rounded text-2xl">wb_sunny</span>
            </div>
            <div class="text-[15px] font-semibold text-white leading-tight truncate">おはよう</div>
          </div>
          <button
            type="button"
            @click="emit('runScene', 'おはよう')"
            class="w-10 h-10 rounded-full bg-[#272a31] hover:bg-[#343842] text-white flex items-center justify-center transition-all duration-200 hover:scale-110 active:scale-95 shrink-0 shadow-sm border border-white/[0.04]"
            aria-label="おはようを実行"
          >
            <span class="material-symbols-rounded text-xl text-neutral-200">play_arrow</span>
          </button>
        </div>

        <!-- シーン2: おやすみ -->
        <div class="group relative bg-[#1c1e23] rounded-3xl p-3.5 flex items-center justify-between shadow-md border border-white/[0.03]">
          <div class="flex items-center space-x-3.5 min-w-0">
            <div class="w-11 h-11 rounded-full bg-[#272a31] text-indigo-400 flex items-center justify-center shrink-0">
              <span class="material-symbols-rounded text-2xl">bedtime</span>
            </div>
            <div class="text-[15px] font-semibold text-white leading-tight truncate">おやすみ</div>
          </div>
          <button
            type="button"
            @click="emit('runScene', 'おやすみ')"
            class="w-10 h-10 rounded-full bg-[#272a31] hover:bg-[#343842] text-white flex items-center justify-center transition-all duration-200 hover:scale-110 active:scale-95 shrink-0 shadow-sm border border-white/[0.04]"
            aria-label="おやすみを実行"
          >
            <span class="material-symbols-rounded text-xl text-neutral-200">play_arrow</span>
          </button>
        </div>

        <!-- シーン3: いってきます -->
        <div class="group relative bg-[#1c1e23] rounded-3xl p-3.5 flex items-center justify-between shadow-md border border-white/[0.03]">
          <div class="flex items-center space-x-3.5 min-w-0">
            <div class="w-11 h-11 rounded-full bg-[#272a31] text-rose-400 flex items-center justify-center shrink-0">
              <span class="material-symbols-rounded text-2xl">logout</span>
            </div>
            <div class="text-[15px] font-semibold text-white leading-tight truncate">いってきます</div>
          </div>
          <button
            type="button"
            @click="emit('runScene', 'いってきます')"
            class="w-10 h-10 rounded-full bg-[#272a31] hover:bg-[#343842] text-white flex items-center justify-center transition-all duration-200 hover:scale-110 active:scale-95 shrink-0 shadow-sm border border-white/[0.04]"
            aria-label="いってきますを実行"
          >
            <span class="material-symbols-rounded text-xl text-neutral-200">play_arrow</span>
          </button>
        </div>

        <!-- シーン4: ただいま -->
        <div class="group relative bg-[#1c1e23] rounded-3xl p-3.5 flex items-center justify-between shadow-md border border-white/[0.03]">
          <div class="flex items-center space-x-3.5 min-w-0">
            <div class="w-11 h-11 rounded-full bg-[#272a31] text-[#2196f3] flex items-center justify-center shrink-0">
              <span class="material-symbols-rounded text-2xl">home</span>
            </div>
            <div class="text-[15px] font-semibold text-white leading-tight truncate">ただいま</div>
          </div>
          <button
            type="button"
            @click="emit('runScene', 'ただいま')"
            class="w-10 h-10 rounded-full bg-[#272a31] hover:bg-[#343842] text-white flex items-center justify-center transition-all duration-200 hover:scale-110 active:scale-95 shrink-0 shadow-sm border border-white/[0.04]"
            aria-label="ただいまを実行"
          >
            <span class="material-symbols-rounded text-xl text-neutral-200">play_arrow</span>
          </button>
        </div>
      </div>
    </section>
  </div>
</template>
