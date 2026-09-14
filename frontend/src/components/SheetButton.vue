<script setup lang="ts">
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
      <span class="material-symbols-rounded text-2xl">{{ icon }}</span>
    </div>

    <div class="overflow-hidden leading-tight flex-1">
      <div v-if="sublabel" class="text-xs text-neutral-400 font-normal">
        {{ sublabel }}
      </div>
      <div
        class="font-semibold text-white truncate"
        :class="sublabel ? 'text-[14px] mt-0.5' : 'text-[14px]'"
      >
        {{ label }}
      </div>
    </div>

    <span
      v-if="hasDropdown"
      class="material-symbols-rounded text-lg text-neutral-400 shrink-0 select-none"
    >
      expand_less
    </span>
  </button>
</template>
