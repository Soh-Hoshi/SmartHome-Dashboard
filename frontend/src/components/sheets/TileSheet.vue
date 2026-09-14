<script setup lang="ts">
import SheetModal from '../common/SheetModal.vue'
import StatCard from '../common/StatCard.vue'
import AppIcon from '../common/AppIcon.vue'
import type { TileData } from '../../composables/useSmartHome'

defineProps<{
  tile: TileData
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()
</script>

<template>
  <SheetModal title="鍵" :scrollable="true" @close="emit('close')">
    <!-- 中央メインヒーロー: 室内検知/検知なしステータス -->
    <div class="my-auto py-6 flex flex-col items-center justify-center text-center select-none shrink-0">
      <div
        class="w-32 h-32 rounded-full flex items-center justify-center mb-4 shadow-inner border transition-colors"
        :class="tile.in_home ? 'bg-amber-500/10 border-amber-500/20 text-amber-400' : 'bg-white/[0.04] border-white/[0.06] text-neutral-400'"
      >
        <AppIcon :name="tile.in_home ? 'vpn_key_alert' : 'key'" :size="76" />
      </div>
      <div class="text-3xl font-bold text-white">
        {{ tile.in_home ? '検知' : '検知なし' }}
      </div>
    </div>

    <!-- 下部: トラッカー詳細グリッド (2x2) -->
    <div class="grid grid-cols-2 gap-2 pt-1 shrink-0">
      <StatCard label="タグ種別" :value="tile.device_name || 'Tile (Bluetooth)'" icon="sell" iconColor="text-amber-400" />
      <StatCard label="電波強度 (RSSI)" :value="`${tile.rssi || '--'} dBm (${tile.in_home ? '室内' : '室外'})`" icon="network_ping" iconColor="text-sky-400" />
      <StatCard label="MAC アドレス" :value="tile.mac || '30:F7:75:1F:0E:20'" icon="fingerprint" iconColor="text-purple-400" />
      <StatCard label="最終検知" :value="tile.last_seen_str || '--:--:--'" icon="history" iconColor="text-emerald-400" />
    </div>
  </SheetModal>
</template>
