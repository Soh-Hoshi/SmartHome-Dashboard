<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  name?: string
  size?: number | string
  fill?: boolean
  weight?: number
}>(), {
  size: 24,
  fill: false,
  weight: 400
})

// Normalize icon names to Google Material Symbols Rounded
const iconName = computed(() => {
  const n = props.name || 'help'
  switch (n) {
    case 'power':
      return 'power_settings_new'
    case 'play':
      return 'play_arrow'
    case 'robot_vacuum':
      return 'vacuum'
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

const numericSize = computed(() => {
  if (typeof props.size === 'number') return props.size
  return parseInt(props.size as string, 10) || 24
})

const computedSize = computed(() => {
  if (typeof props.size === 'number') return `${props.size}px`
  return props.size
})

// Optical size & weight adjustment for power_settings_new:
// In Material Symbols, power_settings_new has a large outer circle that fills 100% of the box.
// Scaling it down 2-3px and softening weight to 350 makes it visually match adjacent icons like water_drop / ac_unit.
const fontSize = computed(() => {
  if (iconName.value === 'power_settings_new') {
    const s = numericSize.value
    if (s <= 20) return `${s - 2}px`
    if (s <= 24) return `${s - 2}px`
    return `${s - 4}px`
  }
  return computedSize.value
})

const fontVariation = computed(() => {
  const isFilled = props.fill || iconName.value === 'water_drop' || iconName.value === 'bedtime'
  const fillVal = isFilled ? 1 : 0
  if (iconName.value === 'power_settings_new') {
    return `'FILL' 0, 'wght' 350, 'GRAD' 0, 'opsz' 20`
  }
  return `'FILL' ${fillVal}, 'wght' ${props.weight}, 'GRAD' 0, 'opsz' ${numericSize.value}`
})
</script>

<template>
  <span
    class="material-symbols-rounded select-none inline-flex items-center justify-center shrink-0 leading-none align-middle"
    :style="{
      fontSize: fontSize,
      width: computedSize,
      height: computedSize,
      fontVariationSettings: fontVariation
    }"
    aria-hidden="true"
  >{{ iconName }}</span>
</template>
