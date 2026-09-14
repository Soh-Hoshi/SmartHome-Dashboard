<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  name?: string
  size?: number | string
  badge?: string | number
  path?: string
  fill?: boolean
  weight?: number
}>(), {
  size: 24,
  fill: false,
  weight: 400
})

// Normalize icon names to Google Material Symbols Rounded
const materialInfo = computed(() => {
  const n = props.name || 'help'
  switch (n) {
    case 'power':
    case 'power_settings_new':
    case 'mode_off':
    case 'mode_off_on':
      return { icon: 'mode_off_on', badge: props.badge }
    case 'vacuum':
    case 'vacuum2':
    case 'vacuum_2':
    case 'robot_vacuum':
    case 'cleaner':
      return { icon: 'vacuum_2', badge: props.badge }
    case 'fan_auto':
    case 'fan-auto':
      return { icon: 'mode_fan', badge: props.badge ?? 'A' }
    case 'fan_speed_1':
    case 'fan-speed-1':
    case 'fan_1':
    case 'fan1':
      return { icon: 'mode_fan', badge: props.badge ?? '1' }
    case 'fan_speed_2':
    case 'fan-speed-2':
    case 'fan_2':
    case 'fan2':
      return { icon: 'mode_fan', badge: props.badge ?? '2' }
    case 'fan_speed_3':
    case 'fan-speed-3':
    case 'fan_3':
    case 'fan3':
      return { icon: 'mode_fan', badge: props.badge ?? '3' }
    case 'play':
      return { icon: 'play_arrow', badge: props.badge }
    case 'windows':
      return { icon: 'desktop_windows', badge: props.badge }
    case 'controller':
      return { icon: 'sports_esports', badge: props.badge }
    case 'sleep':
      return { icon: 'bedtime', badge: props.badge }
    case 'restart':
      return { icon: 'restart_alt', badge: props.badge }
    case 'speed_standard':
      return { icon: 'air', badge: props.badge }
    case 'speed_boost':
      return { icon: 'speed', badge: props.badge }
    case 'speed_max':
      return { icon: 'rocket_launch', badge: props.badge }
    case 'bell_ring':
    case 'volume_up':
      return { icon: 'notifications_active', badge: props.badge }
    default:
      return { icon: n, badge: props.badge }
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
  const isFilled = props.fill || materialInfo.value.icon === 'water_drop' || materialInfo.value.icon === 'bedtime'
  const fillVal = isFilled ? 1 : 0
  return `'FILL' ${fillVal}, 'wght' ${props.weight}, 'GRAD' 0, 'opsz' ${numericSize.value}`
})
</script>

<template>
  <svg
    v-if="path"
    viewBox="0 0 24 24"
    :width="computedSize"
    :height="computedSize"
    class="inline-block shrink-0 fill-current align-middle select-none transition-colors"
    aria-hidden="true"
  >
    <path :d="path" />
  </svg>
  <span
    v-else-if="materialInfo.badge !== undefined && materialInfo.badge !== ''"
    class="relative inline-flex items-center justify-center shrink-0 select-none leading-none align-middle"
    :style="{
      width: computedSize,
      height: computedSize,
      fontSize: computedSize
    }"
    aria-hidden="true"
  >
    <span
      class="material-symbols-rounded select-none inline-flex items-center justify-center shrink-0 leading-none align-middle"
      :style="{
        fontSize: computedSize,
        width: computedSize,
        height: computedSize,
        fontVariationSettings: fontVariation
      }"
    >{{ materialInfo.icon }}</span>
    <span
      class="absolute -bottom-0.5 -right-0.5 min-w-[0.9em] h-[0.9em] px-[0.1em] rounded-full bg-[#181a20] text-[0.42em] font-extrabold font-num flex items-center justify-center leading-none text-current border border-white/20 shadow-sm pointer-events-none"
    >{{ materialInfo.badge }}</span>
  </span>
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
  >{{ materialInfo.icon }}</span>
</template>
