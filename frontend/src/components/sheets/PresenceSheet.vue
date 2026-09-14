<script setup lang="ts">
import SheetModal from '../common/SheetModal.vue'
import StatCard from '../common/StatCard.vue'
import AppIcon from '../common/AppIcon.vue'
import type { PresenceData } from '../../composables/useSmartHome'

defineProps<{
  presence: PresenceData
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()
</script>

<template>
  <SheetModal title="在宅確認" :scrollable="true" @close="emit('close')">
    <!-- 中央メインヒーロー: 在宅/不在ステータス -->
    <div class="my-auto py-6 flex flex-col items-center justify-center text-center select-none shrink-0">
      <div
        class="w-32 h-32 rounded-full flex items-center justify-center mb-4 shadow-inner border transition-colors"
        :class="presence.is_home ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-white/[0.04] border-white/[0.06] text-neutral-400'"
      >
        <AppIcon name="home_pin" :size="64" />
      </div>
      <div class="text-3xl font-bold text-white">
        {{ presence.is_home ? '在宅' : '不在' }}
      </div>
    </div>

    <!-- 下部: デバイス詳細グリッド (2x2) -->
    <div class="grid grid-cols-2 gap-2 pt-1 shrink-0">
      <StatCard label="端末" :value="presence.device_name || 'スマートフォン'" icon="smartphone" iconColor="text-sky-400" />
      <StatCard label="IP アドレス" :value="presence.ip || '192.168.0.30'" icon="wifi" iconColor="text-emerald-400" />
      <StatCard label="MAC アドレス" :value="presence.mac || '72:58:BA:C7:40:FA'" icon="fingerprint" iconColor="text-amber-400" />
      <StatCard label="最終検知" :value="presence.last_seen_str || '--:--:--'" icon="history" iconColor="text-purple-400" />
    </div>
  </SheetModal>
</template>
