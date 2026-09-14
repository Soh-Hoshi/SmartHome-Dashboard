<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useSmartHome } from './composables/useSmartHome'

import Sidebar from './components/Sidebar.vue'
import BottomNav from './components/BottomNav.vue'
import NovaBar from './components/NovaBar.vue'

import DashboardView from './components/views/DashboardView.vue'
import AutomationsView from './components/views/AutomationsView.vue'
import ScenesView from './components/views/ScenesView.vue'

import AcSheet from './components/sheets/AcSheet.vue'
import LightSheet from './components/sheets/LightSheet.vue'
import HeaterSheet from './components/sheets/HeaterSheet.vue'
import CleanerSheet from './components/sheets/CleanerSheet.vue'
import PcSheet from './components/sheets/PcSheet.vue'
import WeatherSheet from './components/sheets/WeatherSheet.vue'
import PresenceSheet from './components/sheets/PresenceSheet.vue'
import TileSheet from './components/sheets/TileSheet.vue'
import LoginModal from './components/LoginModal.vue'

const {
  needsAuth,
  loadInitialState,
  activeTab,
  openedSheet,
  openSheet,
  closeSheet,
  switchTab,

  toast,

  acTemp,
  acMode,
  acFan,
  changeAcTemp,
  selectAcMode,
  selectAcFan,
  toggleAcPower,

  heaterTemp,
  heaterMode,
  changeHeaterTemp,
  selectHeaterMode,
  pressHeaterEco,
  pressHeaterPower,
  toggleHeaterPower,

  lightOn,
  lightBrightness,
  toggleLight,
  selectLightAction,
  changeLightBrightness,

  cleanerStatus,
  cleanerPlay,
  cleanerTimeMin,
  cleanerArea,
  cleanerBattery,
  cleanerMop,
  cleanerSpeed,
  setCleanerMode,
  selectCleanerAction,
  toggleCleanerPower,
  selectCleanerSpeed,
  pressCleanerFindMe,

  pcOnline,
  pcBooting,
  pcShuttingDown,
  pcOs,
  pcTargetOs,
  togglePcPower,
  selectPcPowerOption,
  selectPcOs,

  weather,
  presence,
  tile,

  isSubmittingAssistant,
  isRecording,
  submitAssistantCommand,
  toggleVoiceRecognition,

  runScene,
  runAutomation,
} = useSmartHome()

// --- スワイプによるタブ切り替え ---
let touchStartX = 0
let touchStartY = 0
let touchStartTime = 0
let isHorizontalSwipe = false
let isVerticalScroll = false

function onTouchStart(e: TouchEvent) {
  if (e.touches.length !== 1 || openedSheet.value) return
  if (['INPUT', 'TEXTAREA', 'SELECT'].includes((e.target as HTMLElement)?.tagName)) return

  const touch = e.touches[0]
  touchStartX = touch.clientX
  touchStartY = touch.clientY
  touchStartTime = Date.now()
  isHorizontalSwipe = false
  isVerticalScroll = false
}

function onTouchMove(e: TouchEvent) {
  if (isVerticalScroll || e.touches.length !== 1 || openedSheet.value) return

  const touch = e.touches[0]
  const dx = touch.clientX - touchStartX
  const dy = touch.clientY - touchStartY

  if (!isHorizontalSwipe && Math.abs(dy) > 10 && Math.abs(dy) > Math.abs(dx)) {
    isVerticalScroll = true
    return
  }

  if (!isVerticalScroll && Math.abs(dx) > 15 && Math.abs(dx) > Math.abs(dy) * 1.5) {
    isHorizontalSwipe = true
  }
}

function onTouchEnd(e: TouchEvent) {
  if (!isHorizontalSwipe || isVerticalScroll || openedSheet.value) return

  const touch = e.changedTouches[0]
  const dx = touch.clientX - touchStartX
  const dy = touch.clientY - touchStartY
  const duration = Date.now() - touchStartTime

  if (Math.abs(dx) >= 45 && Math.abs(dx) > Math.abs(dy) * 1.5 && duration < 500) {
    const tabs: Array<'dashboard' | 'automations' | 'scenes'> = ['dashboard', 'automations', 'scenes']
    const idx = tabs.indexOf(activeTab.value)
    if (dx < 0 && idx < tabs.length - 1) {
      switchTab(tabs[idx + 1])
    } else if (dx > 0 && idx > 0) {
      switchTab(tabs[idx - 1])
    }
  }
}

onMounted(() => {
  window.addEventListener('touchstart', onTouchStart, { passive: true })
  window.addEventListener('touchmove', onTouchMove, { passive: true })
  window.addEventListener('touchend', onTouchEnd, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('touchstart', onTouchStart)
  window.removeEventListener('touchmove', onTouchMove)
  window.removeEventListener('touchend', onTouchEnd)
})
</script>

<template>
  <div class="min-h-screen bg-[#0d0f12] text-white flex flex-col antialiased font-sans">
    <!-- 全体レイアウトコンテナ -->
    <div class="flex-1 w-full flex min-h-screen">
      <!-- デスクトップ用サイドバー -->
      <Sidebar :activeTab="activeTab" @switchTab="switchTab" />

      <!-- メインコンテンツ表示エリア -->
      <div class="flex-1 min-w-0 pt-[calc(env(safe-area-inset-top,0px)+5.5rem)] md:pt-6 pb-28 flex flex-col">
        <div id="tab-viewport" class="tab-viewport relative w-full overflow-x-clip">
          <!-- タブ1: メインダッシュボード -->
          <DashboardView
            v-show="activeTab === 'dashboard'"
            :acTemp="acTemp"
            :acMode="acMode"
            :heaterTemp="heaterTemp"
            :heaterMode="heaterMode"
            :lightOn="lightOn"
            :cleanerStatus="cleanerStatus"
            :cleanerPlay="cleanerPlay"
            :pcOnline="pcOnline"
            :pcBooting="pcBooting"
            :pcShuttingDown="pcShuttingDown"
            :pcOs="pcOs"
            :pcTargetOs="pcTargetOs"
            :weather="weather"
            :presence="presence"
            :tile="tile"
            @openSheet="openSheet"
            @toggleLight="toggleLight"
            @toggleAcPower="toggleAcPower"
            @setAcMode="selectAcMode"
            @toggleHeaterPower="toggleHeaterPower"
            @toggleCleanerPower="toggleCleanerPower"
            @setCleanerMode="setCleanerMode"
            @togglePcPower="togglePcPower"
          />

          <!-- タブ2: オートメーション -->
          <AutomationsView
            v-show="activeTab === 'automations'"
            @runAutomation="runAutomation"
          />

          <!-- タブ3: シーン -->
          <ScenesView
            v-show="activeTab === 'scenes'"
            @runScene="runScene"
          />
        </div>
      </div>
    </div>

    <!-- Nova プロンプトバー (スマホ: 上部固定, PC: 下部フローティング) -->
    <NovaBar
      :toast="toast"
      :isSubmitting="isSubmittingAssistant"
      :isRecording="isRecording"
      @submit="submitAssistantCommand"
      @toggleVoice="toggleVoiceRecognition"
    />

    <!-- モバイル用ボトムナビゲーション -->
    <BottomNav :activeTab="activeTab" @switchTab="switchTab" />

    <!-- ================================================================= -->
    <!-- 詳細操作シート (Bottom Sheet Modals)                                -->
    <!-- ================================================================= -->
    <AcSheet
      v-if="openedSheet === 'ac-sheet'"
      :temp="acTemp"
      :mode="acMode"
      :fan="acFan"
      @close="closeSheet"
      @changeTemp="changeAcTemp"
      @selectMode="selectAcMode"
      @selectFan="selectAcFan"
    />

    <LightSheet
      v-if="openedSheet === 'light-sheet'"
      :lightOn="lightOn"
      :lightBrightness="lightBrightness"
      @close="closeSheet"
      @toggle="toggleLight"
      @selectAction="selectLightAction"
      @changeBrightness="changeLightBrightness"
    />

    <HeaterSheet
      v-if="openedSheet === 'heater-sheet'"
      :temp="heaterTemp"
      :mode="heaterMode"
      @close="closeSheet"
      @changeTemp="changeHeaterTemp"
      @selectMode="selectHeaterMode"
      @pressEco="pressHeaterEco"
      @pressPower="pressHeaterPower"
    />

    <CleanerSheet
      v-if="openedSheet === 'cleaner-sheet'"
      :status="cleanerStatus"
      :play="cleanerPlay"
      :timeMin="cleanerTimeMin"
      :area="cleanerArea"
      :battery="cleanerBattery"
      :mop="cleanerMop"
      :speed="cleanerSpeed"
      @close="closeSheet"
      @selectAction="selectCleanerAction"
      @selectSpeed="selectCleanerSpeed"
      @pressFindMe="pressCleanerFindMe"
    />

    <PcSheet
      v-if="openedSheet === 'pc-sheet'"
      :online="pcOnline"
      :booting="pcBooting"
      :shuttingDown="pcShuttingDown"
      :os="pcOs"
      :targetOs="pcTargetOs"
      @close="closeSheet"
      @togglePower="togglePcPower"
      @selectPowerOption="selectPcPowerOption"
      @selectOs="selectPcOs"
    />

    <WeatherSheet
      v-if="openedSheet === 'weather-sheet'"
      :weather="weather"
      @close="closeSheet"
    />

    <PresenceSheet
      v-if="openedSheet === 'presence-sheet'"
      :presence="presence"
      @close="closeSheet"
    />

    <TileSheet
      v-if="openedSheet === 'tile-sheet'"
      :tile="tile"
      @close="closeSheet"
    />

    <!-- 未認証時ログインモーダル -->
    <LoginModal
      v-if="needsAuth"
      @loginSuccess="loadInitialState"
    />
  </div>
</template>
