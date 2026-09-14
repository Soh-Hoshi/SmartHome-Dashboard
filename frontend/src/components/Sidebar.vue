<script setup lang="ts">
import AppIcon from './common/AppIcon.vue'

defineProps<{
  activeTab: 'dashboard' | 'automations' | 'scenes'
}>()

const emit = defineEmits<{
  (e: 'switchTab', tab: 'dashboard' | 'automations' | 'scenes'): void
}>()
</script>

<template>
  <aside
    id="sidebar"
    class="group/sidebar hidden md:flex flex-col w-[68px] hover:w-56 shrink-0 min-h-screen py-6 px-2.5 sticky top-0 h-screen select-none bg-[#0d0f12]/90 backdrop-blur-md border-r border-white/[0.03] transition-all duration-300 ease-in-out z-30 overflow-hidden"
  >
    <nav class="space-y-2 w-full">
      <!-- ダッシュボード -->
      <button
        type="button"
        @click="emit('switchTab', 'dashboard')"
        class="nav-tab-btn w-full flex items-center px-2.5 py-2.5 rounded-2xl text-left transition-all duration-200 active:scale-98"
        :class="activeTab === 'dashboard' ? 'bg-[#253546] text-[#2196f3]' : 'bg-transparent hover:bg-white/[0.04] text-neutral-400 hover:text-white'"
      >
        <div class="w-6 flex items-center justify-center shrink-0">
          <AppIcon name="grid_view" :size="22" />
        </div>
        <span
          class="sidebar-label text-sm whitespace-nowrap overflow-hidden transition-all duration-200 opacity-0 group-hover/sidebar:opacity-100 max-w-0 group-hover/sidebar:max-w-[140px] group-hover/sidebar:ml-3"
          :class="activeTab === 'dashboard' ? 'font-semibold text-[#2196f3]' : 'font-medium text-neutral-400'"
        >ダッシュボード</span>
      </button>

      <!-- オートメーション -->
      <button
        type="button"
        @click="emit('switchTab', 'automations')"
        class="nav-tab-btn w-full flex items-center px-2.5 py-2.5 rounded-2xl text-left transition-all duration-200 active:scale-98"
        :class="activeTab === 'automations' ? 'bg-[#253546] text-[#2196f3]' : 'bg-transparent hover:bg-white/[0.04] text-neutral-400 hover:text-white'"
      >
        <div class="w-6 flex items-center justify-center shrink-0">
          <AppIcon name="bolt" :size="22" />
        </div>
        <span
          class="sidebar-label text-sm whitespace-nowrap overflow-hidden transition-all duration-200 opacity-0 group-hover/sidebar:opacity-100 max-w-0 group-hover/sidebar:max-w-[140px] group-hover/sidebar:ml-3"
          :class="activeTab === 'automations' ? 'font-semibold text-[#2196f3]' : 'font-medium text-neutral-400'"
        >オートメーション</span>
      </button>

      <!-- シーン -->
      <button
        type="button"
        @click="emit('switchTab', 'scenes')"
        class="nav-tab-btn w-full flex items-center px-2.5 py-2.5 rounded-2xl text-left transition-all duration-200 active:scale-98"
        :class="activeTab === 'scenes' ? 'bg-[#253546] text-[#2196f3]' : 'bg-transparent hover:bg-white/[0.04] text-neutral-400 hover:text-white'"
      >
        <div class="w-6 flex items-center justify-center shrink-0">
          <AppIcon name="palette" :size="22" />
        </div>
        <span
          class="sidebar-label text-sm whitespace-nowrap overflow-hidden transition-all duration-200 opacity-0 group-hover/sidebar:opacity-100 max-w-0 group-hover/sidebar:max-w-[140px] group-hover/sidebar:ml-3"
          :class="activeTab === 'scenes' ? 'font-semibold text-[#2196f3]' : 'font-medium text-neutral-400'"
        >シーン</span>
      </button>
    </nav>
  </aside>
</template>
