<script setup lang="ts">
import AppIcon from './AppIcon.vue'

defineProps<{
  label: string
  sublabel?: string
  icon?: string
  iconColor?: string
  hasDropdown?: boolean
  disabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'click', event: MouseEvent): void
}>()
</script>

<template>
  <button
    type="button"
    :disabled="disabled"
    class="w-full h-[58px] flex items-center space-x-3 px-4 rounded-2xl bg-[#2a2d36] hover:bg-[#323640] text-left transition-all shadow-sm border border-white/[0.04] active:scale-[0.98] disabled:opacity-40 disabled:pointer-events-none"
    @click="emit('click', $event)"
  >
    <div
      v-if="icon"
      class="shrink-0 flex items-center justify-center transition-colors"
      :class="iconColor || 'text-neutral-400'"
    >
      <AppIcon :name="icon" :size="24" />
    </div>

    <div class="overflow-hidden leading-tight flex-1">
      <div v-if="sublabel" class="text-[10px] text-neutral-400 font-medium tracking-wide">
        {{ sublabel }}
      </div>
      <div
        class="font-semibold text-white truncate"
        :class="sublabel ? 'text-[14px] mt-0.5' : 'text-[14px]'"
      >
        {{ label }}
      </div>
    </div>

    <AppIcon
      v-if="hasDropdown"
      name="expand_less"
      :size="18"
      class="text-neutral-400 shrink-0 select-none"
    />
  </button>
</template>
