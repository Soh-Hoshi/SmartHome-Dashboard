<script setup lang="ts">
import { computed } from 'vue'
import { getIconPath } from '../../icons'

const props = withDefaults(defineProps<{
  name?: string
  path?: string
  size?: number | string
}>(), {
  size: 24
})

const svgPath = computed(() => {
  if (props.path) return props.path
  return getIconPath(props.name)
})

const computedSize = computed(() => {
  if (typeof props.size === 'number') {
    return `${props.size}px`
  }
  return props.size
})
</script>

<template>
  <svg
    viewBox="0 0 24 24"
    :width="computedSize"
    :height="computedSize"
    class="inline-block shrink-0 fill-current align-middle select-none transition-colors"
    aria-hidden="true"
  >
    <path :d="svgPath" />
  </svg>
</template>
