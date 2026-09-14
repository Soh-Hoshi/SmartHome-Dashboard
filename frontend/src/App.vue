<script setup lang="ts">
import { ref } from 'vue'
import SheetButton from './components/SheetButton.vue'
import DropupMenu, { type DropupItem } from './components/DropupMenu.vue'

// --- クリーナー状態 ---
const activeCleanerMenu = ref<'action' | 'speed' | null>(null)
const cleanerSpeed = ref('Standard')
const cleanerSpeedItems: DropupItem[] = [
  { id: 'Standard', label: '標準', icon: 'air' },
  { id: 'Boost_IQ', label: 'BoostIQ', icon: 'speed' },
  { id: 'Max', label: '最大', icon: 'rocket_launch' },
]
const cleanerActionItems: DropupItem[] = [
  { id: 'start', label: '開始', icon: 'play_arrow' },
  { id: 'pause', label: '停止', icon: 'pause' },
  { id: 'stop', label: 'ホーム', icon: 'home' },
]

// --- エアコン状態 ---
const activeAcMenu = ref<'mode' | 'fan' | null>(null)
const acMode = ref('cool')
const acFan = ref('auto')
const acModeItems: DropupItem[] = [
  { id: 'cool', label: '冷房', icon: 'ac_unit', iconColor: 'text-[#2196f3]' },
  { id: 'dry', label: '除湿', icon: 'water_drop', iconColor: 'text-[#00bcd4]' },
  { id: 'off', label: 'オフ', icon: 'power_settings_new', iconColor: 'text-neutral-400' },
]
const acFanItems: DropupItem[] = [
  { id: 'auto', label: '自動', icon: 'autorenew' },
  { id: 'low', label: '弱', icon: 'density_small' },
  { id: 'medium', label: '中', icon: 'density_medium' },
  { id: 'high', label: '強', icon: 'density_large' },
]

// --- PC状態 ---
const activePcMenu = ref<'power' | 'os' | null>(null)
const pcOs = ref<'Windows' | 'Bazzite'>('Windows')
const pcPowerItems: DropupItem[] = [
  { id: 'sleep', label: 'スリープ', icon: 'bedtime' },
  { id: 'restart', label: '再起動', icon: 'restart_alt' },
]
const pcOsItems: DropupItem[] = [
  { id: 'Windows', label: 'Windows', icon: 'desktop_windows', iconColor: 'text-[#4a88e8]' },
  { id: 'Bazzite', label: 'Bazzite', icon: 'sports_esports', iconColor: 'text-[#c084fc]' },
]

function toggleCleanerMenu(menu: 'action' | 'speed') {
  activeCleanerMenu.value = activeCleanerMenu.value === menu ? null : menu
}

function selectCleanerSpeed(id: string) {
  cleanerSpeed.value = id
  activeCleanerMenu.value = null
}

function toggleAcMenu(menu: 'mode' | 'fan') {
  activeAcMenu.value = activeAcMenu.value === menu ? null : menu
}

function selectAcMode(id: string) {
  acMode.value = id
  activeAcMenu.value = null
}

function selectAcFan(id: string) {
  acFan.value = id
  activeAcMenu.value = null
}

function togglePcMenu(menu: 'power' | 'os') {
  activePcMenu.value = activePcMenu.value === menu ? null : menu
}

function selectPcOs(id: string) {
  pcOs.value = id as 'Windows' | 'Bazzite'
  activePcMenu.value = null
}
</script>

<template>
  <div class="min-h-screen bg-[#0d0f12] text-white p-4 sm:p-8 flex flex-col items-center">
    <!-- ヘッダー -->
    <header class="w-full max-w-xl mb-8 flex items-center justify-between">
      <div>
        <div class="flex items-center space-x-2">
          <span class="inline-block w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <h1 class="text-xl font-bold tracking-tight">SmartHome Modern UI</h1>
        </div>
        <p class="text-xs text-neutral-400 mt-0.5">Vite + Vue 3 + Tailwind CSS + TypeScript</p>
      </div>
      <span class="text-xs px-2.5 py-1 rounded-full bg-white/5 text-neutral-300 border border-white/10">
        PoC Preview
      </span>
    </header>

    <!-- デモ用コンポーネントプレビューグリッド -->
    <div class="w-full max-w-xl space-y-6">
      
      <!-- 1. クリーナー シート コントロール -->
      <section class="bg-[#1e2025] border border-white/[0.06] rounded-3xl p-5 shadow-2xl">
        <div class="flex items-center justify-between pb-3 border-b border-white/5 mb-4">
          <div class="flex items-center space-x-2.5">
            <span class="material-symbols-rounded text-xl text-sky-400">cleaning_services</span>
            <h2 class="text-sm font-bold text-neutral-200">ロボット掃除機 コントロール部</h2>
          </div>
          <span class="text-[11px] text-neutral-400 font-num">h-[58px] 厳密統一</span>
        </div>

        <div class="space-y-2.5">
          <!-- 1段目: アクション -->
          <div class="relative">
            <DropupMenu
              :open="activeCleanerMenu === 'action'"
              title="アクション"
              :items="cleanerActionItems"
              @select="activeCleanerMenu = null"
            />
            <SheetButton
              label="アクション"
              icon="play_circle"
              has-dropdown
              @click="toggleCleanerMenu('action')"
            />
          </div>

          <!-- 2段目: 吸引力 & 探す -->
          <div class="grid grid-cols-2 gap-3">
            <div class="relative">
              <DropupMenu
                :open="activeCleanerMenu === 'speed'"
                title="吸引力"
                :items="cleanerSpeedItems.map(i => ({ ...i, active: i.id === cleanerSpeed }))"
                @select="selectCleanerSpeed"
              />
              <SheetButton
                :label="cleanerSpeedItems.find(i => i.id === cleanerSpeed)?.label || '標準'"
                sublabel="吸引力"
                icon="air"
                has-dropdown
                @click="toggleCleanerMenu('speed')"
              />
            </div>

            <SheetButton
              label="探す"
              icon="notifications_active"
              @click="() => {}"
            />
          </div>
        </div>
      </section>

      <!-- 2. エアコン シート コントロール -->
      <section class="bg-[#1e2025] border border-white/[0.06] rounded-3xl p-5 shadow-2xl">
        <div class="flex items-center justify-between pb-3 border-b border-white/5 mb-4">
          <div class="flex items-center space-x-2.5">
            <span class="material-symbols-rounded text-xl text-cyan-400">ac_unit</span>
            <h2 class="text-sm font-bold text-neutral-200">エアコン コントロール部</h2>
          </div>
          <span class="text-[11px] text-neutral-400 font-num">自動ファン行高ズレ解消</span>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <!-- モード -->
          <div class="relative">
            <DropupMenu
              :open="activeAcMenu === 'mode'"
              title="モード"
              :items="acModeItems.map(i => ({ ...i, active: i.id === acMode }))"
              @select="selectAcMode"
            />
            <SheetButton
              :label="acModeItems.find(i => i.id === acMode)?.label || '冷房'"
              sublabel="モード"
              :icon="acModeItems.find(i => i.id === acMode)?.icon"
              :icon-color="acModeItems.find(i => i.id === acMode)?.iconColor"
              has-dropdown
              @click="toggleAcMenu('mode')"
            />
          </div>

          <!-- ファンモード -->
          <div class="relative">
            <DropupMenu
              :open="activeAcMenu === 'fan'"
              title="ファンモード"
              align="right"
              :items="acFanItems.map(i => ({ ...i, active: i.id === acFan }))"
              @select="selectAcFan"
            />
            <SheetButton
              :label="acFanItems.find(i => i.id === acFan)?.label || '自動'"
              sublabel="ファンモード"
              icon="air"
              has-dropdown
              @click="toggleAcMenu('fan')"
            />
          </div>
        </div>
      </section>

      <!-- 3. PC シート コントロール -->
      <section class="bg-[#1e2025] border border-white/[0.06] rounded-3xl p-5 shadow-2xl">
        <div class="flex items-center justify-between pb-3 border-b border-white/5 mb-4">
          <div class="flex items-center space-x-2.5">
            <span class="material-symbols-rounded text-xl text-blue-400">desktop_windows</span>
            <h2 class="text-sm font-bold text-neutral-200">PC コントロール部</h2>
          </div>
          <span class="text-[11px] text-neutral-400 font-num">OS切替・電源オプション</span>
        </div>

        <div class="space-y-2.5">
          <!-- 1段目: 電源オプション -->
          <div class="relative">
            <DropupMenu
              :open="activePcMenu === 'power'"
              title="電源オプション"
              :items="pcPowerItems"
              @select="activePcMenu = null"
            />
            <SheetButton
              label="電源オプション"
              icon="power_settings_new"
              has-dropdown
              @click="togglePcMenu('power')"
            />
          </div>

          <!-- 2段目: 起動OS -->
          <div class="relative">
            <DropupMenu
              :open="activePcMenu === 'os'"
              title="起動OS"
              :items="pcOsItems.map(i => ({ ...i, active: i.id === pcOs }))"
              @select="selectPcOs"
            />
            <SheetButton
              :label="pcOs"
              sublabel="起動OS"
              :icon="pcOs === 'Windows' ? 'desktop_windows' : 'sports_esports'"
              :icon-color="pcOs === 'Windows' ? 'text-[#4a88e8]' : 'text-[#c084fc]'"
              has-dropdown
              @click="togglePcMenu('os')"
            />
          </div>
        </div>
      </section>

    </div>
  </div>
</template>
