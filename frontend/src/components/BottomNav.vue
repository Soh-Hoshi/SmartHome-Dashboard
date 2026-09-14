<script setup lang="ts">
defineProps<{
  activeTab: 'dashboard' | 'automations' | 'scenes'
}>()

const emit = defineEmits<{
  (e: 'switchTab', tab: 'dashboard' | 'automations' | 'scenes'): void
}>()
</script>

<template>
  <nav
    id="bottom-nav"
    class="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-[#0d0f12]/90 backdrop-blur-xl px-3 pt-1.5 pb-[max(0.5rem,env(safe-area-inset-bottom))] border-t border-white/[0.04] select-none"
  >
    <div class="grid grid-cols-3 items-center max-w-md mx-auto">
      <!-- ダッシュボード -->
      <button
        type="button"
        @click="emit('switchTab', 'dashboard')"
        class="bottom-nav-btn flex flex-col items-center justify-center py-1 px-1 rounded-2xl transition-all duration-200 active:scale-95"
        :class="activeTab === 'dashboard' ? 'text-[#2196f3]' : 'text-neutral-400 hover:text-neutral-200'"
      >
        <div
          class="bottom-nav-icon-wrap w-14 h-8 rounded-full flex items-center justify-center transition-all duration-200"
          :class="activeTab === 'dashboard' ? 'bg-[#253546] text-[#2196f3]' : 'bg-transparent text-neutral-400'"
        >
          <span
            class="material-symbols-rounded text-[22px]"
            :class="activeTab === 'dashboard' ? 'symbol-fill' : ''"
          >grid_view</span>
        </div>
        <span
          class="bottom-nav-label text-[11px] mt-1 tracking-tight"
          :class="activeTab === 'dashboard' ? 'font-semibold text-[#2196f3]' : 'font-medium text-neutral-400'"
        >ダッシュボード</span>
      </button>

      <!-- オートメーション -->
      <button
        type="button"
        @click="emit('switchTab', 'automations')"
        class="bottom-nav-btn flex flex-col items-center justify-center py-1 px-1 rounded-2xl transition-all duration-200 active:scale-95"
        :class="activeTab === 'automations' ? 'text-[#2196f3]' : 'text-neutral-400 hover:text-neutral-200'"
      >
        <div
          class="bottom-nav-icon-wrap w-14 h-8 rounded-full flex items-center justify-center transition-all duration-200"
          :class="activeTab === 'automations' ? 'bg-[#253546] text-[#2196f3]' : 'bg-transparent text-neutral-400'"
        >
          <span
            class="material-symbols-rounded text-[22px]"
            :class="activeTab === 'automations' ? 'symbol-fill' : ''"
          >bolt</span>
        </div>
        <span
          class="bottom-nav-label text-[11px] mt-1 tracking-tight"
          :class="activeTab === 'automations' ? 'font-semibold text-[#2196f3]' : 'font-medium text-neutral-400'"
        >オートメーション</span>
      </button>

      <!-- シーン -->
      <button
        type="button"
        @click="emit('switchTab', 'scenes')"
        class="bottom-nav-btn flex flex-col items-center justify-center py-1 px-1 rounded-2xl transition-all duration-200 active:scale-95"
        :class="activeTab === 'scenes' ? 'text-[#2196f3]' : 'text-neutral-400 hover:text-neutral-200'"
      >
        <div
          class="bottom-nav-icon-wrap w-14 h-8 rounded-full flex items-center justify-center transition-all duration-200"
          :class="activeTab === 'scenes' ? 'bg-[#253546] text-[#2196f3]' : 'bg-transparent text-neutral-400'"
        >
          <span
            class="material-symbols-rounded text-[22px]"
            :class="activeTab === 'scenes' ? 'symbol-fill' : ''"
          >palette</span>
        </div>
        <span
          class="bottom-nav-label text-[11px] mt-1 tracking-tight"
          :class="activeTab === 'scenes' ? 'font-semibold text-[#2196f3]' : 'font-medium text-neutral-400'"
        >シーン</span>
      </button>
    </div>
  </nav>
</template>
