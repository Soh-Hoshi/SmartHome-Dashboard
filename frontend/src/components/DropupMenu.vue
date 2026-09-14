<script setup lang="ts">
import AppIcon from './common/AppIcon.vue'

export interface DropupItem {
  id: string
  label: string
  icon?: string
  iconColor?: string
  active?: boolean
}

withDefaults(
  defineProps<{
    open: boolean
    title?: string
    items: DropupItem[]
    align?: 'left' | 'right'
  }>(),
  {
    align: 'left',
  }
)

const emit = defineEmits<{
  (e: 'select', id: string): void
  (e: 'close'): void
}>()
</script>

<template>
  <div
    v-show="open"
    class="dropup-menu absolute bottom-full mb-3 w-56 bg-[#262932] border border-white/10 rounded-2xl p-1.5 shadow-2xl z-30 backdrop-blur-xl"
    :class="align === 'right' ? 'right-0' : 'left-0'"
  >
    <div
      v-if="title"
      class="text-[11px] font-semibold text-neutral-400 px-3 py-1.5 uppercase tracking-wider"
    >
      {{ title }}
    </div>

    <div class="space-y-0.5">
      <button
        v-for="item in items"
        :key="item.id"
        type="button"
        class="w-full h-10 flex items-center justify-between px-3 rounded-xl hover:bg-white/10 transition-colors text-left text-sm font-medium"
        @click="emit('select', item.id)"
      >
        <div class="flex items-center space-x-3" :class="item.iconColor || 'text-neutral-300'">
          <AppIcon v-if="item.icon" :name="item.icon" :size="20" />
          <span class="text-white">{{ item.label }}</span>
        </div>

        <span
          v-if="item.active"
          class="shrink-0 w-5 h-5 flex items-center justify-center"
          :class="item.iconColor || 'text-[#2196f3]'"
        >
          <AppIcon name="check" :size="18" />
        </span>
      </button>
    </div>
  </div>
</template>
