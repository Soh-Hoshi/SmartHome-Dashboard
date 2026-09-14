<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  icon: string
  iconColor?: string
}>()
</script>

<template>
  <div class="bg-[#2a2d36] rounded-2xl p-2.5 flex items-center space-x-2.5 border border-white/[0.04]">
    <!-- アイコン背面の薄い角丸四角形を除去し、すっきりとアイコン本来のカラーと形状を強調 -->
    <div class="w-7 h-7 flex items-center justify-center shrink-0" :class="iconColor || 'text-neutral-400'">
      <span class="material-symbols-rounded text-xl">{{ icon }}</span>
    </div>
    <div class="overflow-hidden min-w-0 flex-1">
      <div class="text-[10px] text-neutral-400 font-normal truncate">{{ label }}</div>
      <div class="text-xs sm:text-sm font-bold text-white font-num truncate">{{ value }}</div>
    </div>
  </div>
</template>
