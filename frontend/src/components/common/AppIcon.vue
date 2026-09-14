<script setup lang="ts">
import { computed } from 'vue'
import { getIconPath } from '../../icons'

const props = withDefaults(defineProps<{
  name?: string
  size?: number | string
  type?: 'material' | 'mdi' | 'auto'
  path?: string
  fill?: boolean
  weight?: number
}>(), {
  size: 24,
  type: 'auto',
  fill: false,
  weight: 400
})

// MDI by default for power, cleaner, and fan speeds as requested by user
const defaultMdiIcons = new Set([
  'power',
  'power_settings_new',
  'vacuum',
  'robot_vacuum',
  'cleaner',
  'fan_auto',
  'fan_speed_1',
  'fan_speed_2',
  'fan_speed_3',
  'fan-auto',
  'fan-speed-1',
  'fan-speed-2',
  'fan-speed-3',
  'fan1',
  'fan2',
  'fan3'
])

const isMdi = computed(() => {
  if (props.path) return true
  if (props.type === 'mdi') return true
  if (props.type === 'material') return false
  const n = props.name || ''
  if (n.startsWith('mdi:') || n.startsWith('mdi-') || n.startsWith('fan_') || n.startsWith('fan-')) return true
  return defaultMdiIcons.has(n)
})

const mdiSvgPath = computed(() => {
  if (props.path) return props.path
  const n = (props.name || '').replace(/^mdi[:-]/, '')
  return getIconPath(n)
})

// Normalize icon names to Google Material Symbols Rounded
const materialIconName = computed(() => {
  const n = props.name || 'help'
  switch (n) {
    case 'play':
      return 'play_arrow'
    case 'windows':
      return 'desktop_windows'
    case 'controller':
      return 'sports_esports'
    case 'sleep':
      return 'bedtime'
    case 'restart':
      return 'restart_alt'
    case 'speed_standard':
      return 'air'
    case 'speed_boost':
      return 'speed'
    case 'speed_max':
      return 'rocket_launch'
    case 'bell_ring':
    case 'volume_up':
      return 'notifications_active'
    default:
      return n
  }
})

const computedSize = computed(() => {
  if (typeof props.size === 'number') return `${props.size}px`
  return props.size
})

const numericSize = computed(() => {
  if (typeof props.size === 'number') return props.size
  return parseInt(props.size as string, 10) || 24
})

const fontVariation = computed(() => {
  const isFilled = props.fill || materialIconName.value === 'water_drop' || materialIconName.value === 'bedtime'
  const fillVal = isFilled ? 1 : 0
  return `'FILL' ${fillVal}, 'wght' ${props.weight}, 'GRAD' 0, 'opsz' ${numericSize.value}`
})
</script>

<template>
  <svg
    v-if="isMdi"
    viewBox="0 0 24 24"
    :width="computedSize"
    :height="computedSize"
    class="inline-block shrink-0 fill-current align-middle select-none transition-colors"
    aria-hidden="true"
  >
    <path :d="mdiSvgPath" />
  </svg>
  <span
    v-else
    class="material-symbols-rounded select-none inline-flex items-center justify-center shrink-0 leading-none align-middle"
    :style="{
      fontSize: computedSize,
      width: computedSize,
      height: computedSize,
      fontVariationSettings: fontVariation
    }"
    aria-hidden="true"
  >{{ materialIconName }}</span>
</template>
