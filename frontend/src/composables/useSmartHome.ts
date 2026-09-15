import { ref, reactive, onMounted, onUnmounted } from 'vue'

export interface HourlyForecast {
  time: string
  icon: string
  temp: number | string
  pop: number | string
}

export interface WeatherData {
  weather: string
  weather_icon: string
  temp: string | number
  temp_max: string | number
  temp_min: string | number
  feels_like: string | number
  humidity: string | number
  wind_speed: string | number
  sunset: string
  sunrise: string
  hourly: HourlyForecast[]
}

export interface PresenceData {
  is_home: boolean
  device_name: string
  ip: string
  mac: string
  last_seen_str: string
}

export interface TileData {
  in_home: boolean
  device_name: string
  rssi: string | number
  mac: string
  last_seen_str: string
}

export function useSmartHome() {
  // --- 認証状態 ---
  const needsAuth = ref(false)

  // --- ナビゲーション & モーダル ---
  const activeTab = ref<'dashboard' | 'automations' | 'scenes'>('dashboard')
  const openedSheet = ref<string | null>(null)

  // --- トースト通知 ---
  const toast = reactive({
    visible: false,
    message: '',
    icon: 'auto_awesome',
    isError: false,
  })
  let toastTimer: any = null

  function showToast(message: string, icon = 'auto_awesome', isError = false) {
    if (toastTimer) clearTimeout(toastTimer)
    toast.message = message
    toast.icon = icon
    toast.isError = isError
    toast.visible = true

    toastTimer = setTimeout(() => {
      toast.visible = false
    }, 4000)
  }

  // --- シート開閉 & ブラウザ履歴 (戻るボタン対応) ---
  let isModalHistoryActive = false

  function openSheet(sheetId: string) {
    openedSheet.value = sheetId
    document.body.style.overflow = 'hidden'
    if (!isModalHistoryActive) {
      history.pushState({ modalOpen: true, sheetId }, '')
      isModalHistoryActive = true
    }
  }

  function closeSheet() {
    openedSheet.value = null
    document.body.style.overflow = ''
    if (isModalHistoryActive) {
      isModalHistoryActive = false
      history.back()
    }
  }

  function handlePopState() {
    openedSheet.value = null
    document.body.style.overflow = ''
    isModalHistoryActive = false
  }

  // --- タブ切り替え ---
  function switchTab(tab: 'dashboard' | 'automations' | 'scenes') {
    activeTab.value = tab
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // --- システムバック・戻るボタンハンドラ ---
  function handleBackAction(): boolean {
    if (openedSheet.value) {
      closeSheet()
      return true
    }
    if (activeTab.value !== 'dashboard') {
      switchTab('dashboard')
      return true
    }
    return false
  }

  // --- エアコン状態 ---
  const acTemp = ref(26)
  const acMode = ref<'cool' | 'dry' | 'off'>('cool')
  const acFan = ref<'auto' | 'low' | 'medium' | 'high'>('auto')
  let acSyncTimer: any = null

  function syncAc() {
    if (acSyncTimer) clearTimeout(acSyncTimer)
    acSyncTimer = setTimeout(async () => {
      try {
        await fetch('/api/ac', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'SmartHome-UI' },
          body: JSON.stringify({
            mode: acMode.value,
            temp: acTemp.value,
            fan_mode: acFan.value,
          }),
        })
      } catch (err) {
        console.error('[AC Sync Failed]', err)
      }
    }, 350)
  }

  function changeAcTemp(delta: number) {
    if (acMode.value === 'off') acMode.value = 'cool'
    acTemp.value = Math.min(28, Math.max(22, acTemp.value + delta))
    syncAc()
  }

  function selectAcMode(mode: 'cool' | 'dry' | 'off') {
    acMode.value = mode
    syncAc()
  }

  function selectAcFan(fan: 'auto' | 'low' | 'medium' | 'high') {
    acFan.value = fan
    syncAc()
  }

  function toggleAcPower() {
    acMode.value = acMode.value === 'off' ? 'cool' : 'off'
    syncAc()
  }

  // --- ヒーター状態 ---
  const heaterTemp = ref(22)
  const heaterMode = ref<'heat' | 'off'>('off')
  const heaterEco = ref(false)
  const heaterPower = ref(2)

  async function sendHeaterCommand(action: string, extra = {}) {
    try {
      await fetch('/api/heater', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'SmartHome-UI' },
        body: JSON.stringify({ action, ...extra }),
      })
    } catch (err) {
      console.error('[Heater Sync Failed]', err)
    }
  }

  function changeHeaterTemp(delta: number) {
    if (heaterMode.value === 'off') {
      heaterMode.value = 'heat'
      sendHeaterCommand('turnOn')
    }
    heaterTemp.value = Math.min(28, Math.max(22, heaterTemp.value + delta))
    sendHeaterCommand(delta > 0 ? 'plus' : 'minus')
  }

  function selectHeaterMode(mode: 'heat' | 'off') {
    const prev = heaterMode.value
    heaterMode.value = mode
    if (prev !== mode) {
      sendHeaterCommand(mode === 'heat' ? 'turnOn' : 'turnOff')
    }
  }

  function pressHeaterEco() {
    if (heaterMode.value === 'off') return
    sendHeaterCommand('eco')
  }

  function pressHeaterPower() {
    if (heaterMode.value === 'off') return
    sendHeaterCommand('power')
  }

  function toggleHeaterPower() {
    heaterMode.value = heaterMode.value === 'off' ? 'heat' : 'off'
    sendHeaterCommand(heaterMode.value === 'heat' ? 'turnOn' : 'turnOff')
  }

  // --- ライト状態 ---
  const lightOn = ref(false)
  const lightBrightness = ref(3)

  async function sendLightCommand(action: string) {
    try {
      await fetch('/api/light', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'SmartHome-UI' },
        body: JSON.stringify({ action }),
      })
    } catch (err) {
      console.error('[Light Sync Failed]', err)
    }
  }

  function toggleLight() {
    lightOn.value = !lightOn.value
    sendLightCommand(lightOn.value ? 'turnOn' : 'turnOff')
  }

  function selectLightAction(action: 'full' | 'night') {
    lightOn.value = true
    if (action === 'full') {
      sendLightCommand('full')
      showToast('リビング照明を全灯に設定しました', 'light_mode')
    } else {
      sendLightCommand('night')
      showToast('リビング照明を常夜灯に設定しました', 'bedtime')
    }
  }

  function changeLightBrightness(delta: number) {
    if (!lightOn.value) return
    lightBrightness.value = Math.min(5, Math.max(1, lightBrightness.value + delta))
    sendLightCommand(delta > 0 ? 'brightnessUp' : 'brightnessDown')
  }

  // --- クリーナー状態 ---
  const cleanerStatus = ref('charging')
  const cleanerPlay = ref(false)
  const cleanerTimeMin = ref(0)
  const cleanerArea = ref(0)
  const cleanerBattery = ref(66)
  const cleanerMop = ref(false)
  const cleanerSpeed = ref<'Standard' | 'Boost_IQ' | 'Max'>('Standard')

  async function setCleanerMode(action: 'start' | 'pause' | 'stop') {
    if (action === 'start') {
      cleanerStatus.value = 'running'
      cleanerPlay.value = true
    } else if (action === 'pause') {
      cleanerStatus.value = 'standby'
      cleanerPlay.value = false
    } else if (action === 'stop') {
      cleanerStatus.value = 'recharge'
      cleanerPlay.value = false
    }

    try {
      const res = await fetch('/api/cleaner', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'SmartHome-UI' },
        body: JSON.stringify({ action }),
      })
      if (res.ok) {
        const data = await res.json()
        if (data.state) {
          cleanerStatus.value = (data.state.cleanerStatus || cleanerStatus.value).toLowerCase()
          cleanerPlay.value = !!data.state.cleanerPlay
        }
      }
    } catch (e) {
      console.error('[Cleaner Error]', e)
    } finally {
      setTimeout(syncCleanerStatus, 1500)
    }
  }

  function selectCleanerAction(action: 'start' | 'pause' | 'stop') {
    setCleanerMode(action)
    if (action === 'start') showToast('クリーナーの清掃を開始しました', 'play_arrow')
    else if (action === 'pause') showToast('クリーナーを停止しました', 'pause')
    else if (action === 'stop') showToast('クリーナーをホームへ帰還させます', 'home')
  }

  function toggleCleanerPower() {
    const isRunning = cleanerStatus.value === 'running' && cleanerPlay.value === true
    if (isRunning) {
      setCleanerMode('stop')
    } else {
      setCleanerMode('start')
    }
  }

  async function selectCleanerSpeed(speed: 'Standard' | 'Boost_IQ' | 'Max') {
    cleanerSpeed.value = speed
    try {
      await fetch('/api/cleaner', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'SmartHome-UI' },
        body: JSON.stringify({ action: 'speed', speed }),
      })
    } catch (e) {
      console.error('[Cleaner Speed Error]', e)
    } finally {
      setTimeout(syncCleanerStatus, 1500)
    }
  }

  async function pressCleanerFindMe() {
    try {
      await fetch('/api/cleaner', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'SmartHome-UI' },
        body: JSON.stringify({ action: 'find_me' }),
      })
    } catch (e) {
      console.error('[Cleaner Find Me Error]', e)
    }
  }

  async function syncCleanerStatus() {
    try {
      const res = await fetch('/api/cleaner/status', {
        headers: { 'X-Requested-With': 'SmartHome-UI' },
      })
      if (res.ok) {
        const data = await res.json()
        if (data.success) {
          cleanerStatus.value = (data.status || 'charging').toLowerCase()
          cleanerPlay.value = !!data.play
          cleanerTimeMin.value = data.clean_time_min || 0
          cleanerArea.value = data.clean_area || 0
          if (data.battery !== undefined) cleanerBattery.value = data.battery
          if (data.mop_attached !== undefined) cleanerMop.value = !!data.mop_attached
          if (data.speed) cleanerSpeed.value = data.speed
        }
      }
    } catch (e) {}
  }

  // --- デスクトップPC状態 & USB ---
  const pcOnline = ref(false)
  const pcBooting = ref(false)
  const pcShuttingDown = ref(false)
  const pcOs = ref('オフライン')
  const pcTargetOs = ref<'Windows' | 'Bazzite'>('Windows')
  const usbPower = ref(false)
  let pcActionLockTime = 0

  async function sendPcCommand(action: string, extra = {}) {
    pcActionLockTime = Date.now()
    try {
      const res = await fetch('/api/pc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'SmartHome-UI' },
        body: JSON.stringify({ action, ...extra }),
      })
      const data = await res.json()
      if (data.status === 'success' || data.status === 'info') {
        if (typeof data.online === 'boolean') pcOnline.value = data.online
        pcBooting.value = !!data.booting
        pcShuttingDown.value = !!data.shutting_down
        if (data.os) pcOs.value = data.os
        if (typeof data.usb_power === 'boolean') usbPower.value = data.usb_power
        if (data.target_os) pcTargetOs.value = data.target_os
        if (pcBooting.value || pcShuttingDown.value) {
          setTimeout(syncPcStatus, 2000)
        }
      } else if (data.status === 'error') {
        showToast(data.message || '操作に失敗しました', 'error', true)
        setTimeout(syncPcStatus, 1500)
      }
    } catch (err) {
      showToast('通信エラーが発生しました', 'error', true)
      setTimeout(syncPcStatus, 1500)
    }
  }

  function togglePcPower() {
    if (pcBooting.value) {
      showToast('PCは現在起動処理中です', 'hourglass_top')
      return
    }
    if (pcShuttingDown.value) {
      showToast('PCは現在終了処理中です', 'hourglass_top')
      return
    }

    if (!pcOnline.value) {
      pcOnline.value = true
      pcBooting.value = true
      pcShuttingDown.value = false
      pcOs.value = '起動中'
      showToast('PCへ起動シグナル(WoL)を送信しました', 'power_settings_new')
      sendPcCommand('boot')
    } else {
      pcOnline.value = false
      pcBooting.value = false
      pcShuttingDown.value = true
      pcOs.value = '終了中'
      showToast('PCへ電源オフを指示しました', 'power_settings_new')
      sendPcCommand('shutdown')
    }
  }

  function selectPcPowerOption(action: 'sleep' | 'restart') {
    if (!pcOnline.value || pcBooting.value || pcShuttingDown.value) {
      showToast(action === 'sleep' ? 'PCがオンラインの時のみスリープ可能です' : 'PCがオンラインの時のみ再起動可能です', 'info')
      return
    }
    if (action === 'sleep') {
      pcOnline.value = false
      pcShuttingDown.value = true
      pcOs.value = '終了中'
      showToast('PCへスリープを指示しました', 'bedtime')
      sendPcCommand('sleep')
    } else {
      pcBooting.value = true
      pcOs.value = '起動中'
      showToast('PCへ再起動を指示しました', 'restart_alt')
      sendPcCommand('restart')
    }
  }

  async function selectPcOs(os: 'Windows' | 'Bazzite') {
    pcTargetOs.value = os
    usbPower.value = os === 'Bazzite'
    try {
      const res = await fetch('/api/pc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'SmartHome-UI' },
        body: JSON.stringify({ action: 'set_os', target_os: os }),
      })
      const data = await res.json()
      if (data && data.target_os) pcTargetOs.value = data.target_os
      showToast(`起動OSを ${os} に設定しました (USB: ${os === 'Bazzite' ? 'オン' : 'オフ'})`, os === 'Bazzite' ? 'sports_esports' : 'desktop_windows')
    } catch (err) {
      console.error('[Set OS Failed]', err)
    }
  }

  async function syncPcStatus() {
    if (Date.now() - pcActionLockTime < 5000) return
    try {
      const res = await fetch('/api/pc', {
        headers: { 'X-Requested-With': 'SmartHome-UI' },
      })
      if (res.ok) {
        const data = await res.json()
        if (data.status === 'success') {
          pcOnline.value = !!data.online
          pcBooting.value = !!data.booting
          pcShuttingDown.value = !!data.shutting_down
          pcOs.value = data.os || (pcOnline.value ? '起動中' : 'オフライン')
          if (typeof data.usb_power === 'boolean') usbPower.value = data.usb_power
          if (data.target_os) pcTargetOs.value = data.target_os
          if (pcBooting.value || pcShuttingDown.value) {
            setTimeout(syncPcStatus, 2000)
          }
        }
      }
    } catch (e) {}
  }

  async function syncUsbStatus() {
    try {
      const res = await fetch('/api/usb', {
        headers: { 'X-Requested-With': 'SmartHome-UI' },
      })
      if (res.ok) {
        const data = await res.json()
        if (data.status === 'success') {
          if (typeof data.power === 'boolean') usbPower.value = data.power
          if (data.target_os) pcTargetOs.value = data.target_os
        }
      }
    } catch (e) {}
  }

  // --- 気象情報 ---
  const weather = reactive<WeatherData>({
    weather: '--',
    weather_icon: 'partly_cloudy_day',
    temp: '--',
    temp_max: '--',
    temp_min: '--',
    feels_like: '--',
    humidity: '--',
    wind_speed: '--',
    sunset: '--:--',
    sunrise: '--:--',
    hourly: [],
  })

  async function fetchWeatherData() {
    try {
      const res = await fetch('/api/weather', {
        headers: { 'X-Requested-With': 'SmartHome-UI' },
      })
      const data = await res.json()
      if (data.status === 'success' && data.weather) {
        Object.assign(weather, data.weather)
      }
    } catch (err) {
      console.warn('[Weather Error]', err)
    }
  }

  // --- 在宅センサー ---
  const presence = reactive<PresenceData>({
    is_home: true,
    device_name: 'スマートフォン',
    ip: '192.168.0.30',
    mac: '72:58:BA:C7:40:FA',
    last_seen_str: '--:--:--',
  })

  async function fetchPresenceData() {
    try {
      const res = await fetch('/api/presence', {
        headers: { 'X-Requested-With': 'SmartHome-UI' },
      })
      const data = await res.json()
      if (data.status === 'success' && data.presence) {
        Object.assign(presence, data.presence)
      }
    } catch (err) {
      console.warn('[Presence Error]', err)
    }
  }

  // --- 鍵 (Tile) センサー ---
  const tile = reactive<TileData>({
    in_home: true,
    device_name: 'Tile (Bluetooth)',
    rssi: '-- dBm',
    mac: '30:F7:75:1F:0E:20',
    last_seen_str: '--:--:--',
  })

  async function fetchTileData() {
    try {
      const res = await fetch('/api/tile', {
        headers: { 'X-Requested-With': 'SmartHome-UI' },
      })
      const data = await res.json()
      if (data.status === 'success' && data.tile) {
        Object.assign(tile, data.tile)
      }
    } catch (err) {
      console.warn('[Tile Error]', err)
    }
  }

  // --- Nova AI アシスタント ---
  const isSubmittingAssistant = ref(false)
  async function submitAssistantCommand(promptText: string) {
    if (!promptText || !promptText.trim()) return
    isSubmittingAssistant.value = true
    try {
      const res = await fetch('/api/assistant', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'SmartHome-UI' },
        body: JSON.stringify({ prompt: promptText.trim() }),
      })
      const data = await res.json()
      if (data.message) {
        showToast(data.message, data.success ? 'auto_awesome' : 'info', !data.success)
      }
      if (data.state) {
        if (data.state.acTemp !== undefined) acTemp.value = data.state.acTemp
        if (data.state.acMode !== undefined) acMode.value = data.state.acMode
        if (data.state.acFan !== undefined) acFan.value = data.state.acFan
        if (data.state.heaterTemp !== undefined) heaterTemp.value = data.state.heaterTemp
        if (data.state.heaterMode !== undefined) heaterMode.value = data.state.heaterMode
        if (data.state.lightOn !== undefined) lightOn.value = data.state.lightOn
        if (data.state.cleanerStatus !== undefined) cleanerStatus.value = data.state.cleanerStatus
      }
    } catch (err) {
      showToast('コマンドの送信に失敗しました', 'error', true)
    } finally {
      isSubmittingAssistant.value = false
    }
  }

  // --- 音声認識 (Web Speech API) ---
  const isRecording = ref(false)
  let recognition: any = null

  function initSpeechRecognition() {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognition) return null
    const rec = new SpeechRecognition()
    rec.lang = 'ja-JP'
    rec.interimResults = true
    rec.maxAlternatives = 1
    rec.continuous = false

    rec.onstart = () => {
      isRecording.value = true
      showToast('Novaがお聞きしています...', 'mic')
    }

    rec.onresult = (e: any) => {
      let finalTranscript = ''
      for (let i = e.resultIndex; i < e.results.length; ++i) {
        if (e.results[i].isFinal) {
          finalTranscript += e.results[i][0].transcript
        }
      }
      if (finalTranscript) {
        stopVoiceRecognition()
        submitAssistantCommand(finalTranscript)
      }
    }

    rec.onerror = (e: any) => {
      if (e.error === 'not-allowed') {
        showToast('マイクの使用が許可されていません', 'mic_off', true)
      } else if (e.error !== 'no-speech') {
        showToast('音声を認識できませんでした', 'mic_off', true)
      }
      stopVoiceRecognition()
    }

    rec.onend = () => {
      stopVoiceRecognition()
    }

    return rec
  }

  function toggleVoiceRecognition() {
    if (!recognition) recognition = initSpeechRecognition()
    if (!recognition) {
      showToast('音声認識に対応していません', 'info', true)
      return
    }

    if (isRecording.value) {
      recognition.stop()
    } else {
      try {
        recognition.start()
      } catch (e) {
        try { recognition.abort() } catch (err) {}
        stopVoiceRecognition()
      }
    }
  }

  function stopVoiceRecognition() {
    isRecording.value = false
  }

  // --- オートメーション & シーン ---
  function runScene(name: string) {
    submitAssistantCommand(name)
  }

  function runAutomation(id: string) {
    const map: Record<string, string> = {
      weekday_morning_light: 'リビングの電気をつけて',
      weekday_morning_cleaner: '掃除を開始して',
      away_device_warning: '消し忘れ通知テスト',
    }
    submitAssistantCommand(map[id] || 'オートメーションを実行')
  }

  // --- 全体初期同期 ---
  async function loadInitialState() {
    try {
      const res = await fetch('/api/state', {
        headers: { 'X-Requested-With': 'SmartHome-UI' },
      })
      if (res.status === 401 || res.status === 403) {
        needsAuth.value = true
        return
      }
      if (res.ok) {
        needsAuth.value = false
        const data = await res.json()
        if (data.state) {
          const s = data.state
          if (s.acTemp !== undefined) acTemp.value = s.acTemp
          if (s.acMode !== undefined) acMode.value = s.acMode
          if (s.acFan !== undefined) acFan.value = s.acFan
          if (s.heaterTemp !== undefined) heaterTemp.value = s.heaterTemp
          if (s.heaterMode !== undefined) heaterMode.value = s.heaterMode
          if (s.heaterEco !== undefined) heaterEco.value = s.heaterEco
          if (s.heaterPower !== undefined) heaterPower.value = s.heaterPower
          if (s.lightOn !== undefined) lightOn.value = s.lightOn
          if (s.lightBrightness !== undefined) lightBrightness.value = s.lightBrightness
          if (s.cleanerStatus !== undefined) cleanerStatus.value = s.cleanerStatus
          if (s.cleanerPlay !== undefined) cleanerPlay.value = s.cleanerPlay
          if (s.usbPower !== undefined) usbPower.value = s.usbPower
          if (s.pcTargetOs !== undefined) pcTargetOs.value = s.pcTargetOs
          if (s.pcOnline !== undefined) pcOnline.value = s.pcOnline
          if (s.pcBooting !== undefined) pcBooting.value = s.pcBooting
          if (s.pcShuttingDown !== undefined) pcShuttingDown.value = s.pcShuttingDown
          if (s.pcOs !== undefined) pcOs.value = s.pcOs
        }
      }
    } catch (e) {
      console.warn('[Initial State Warning]', e)
    }

    syncCleanerStatus()
    syncUsbStatus()
    syncPcStatus()
    fetchWeatherData()
    fetchPresenceData()
    fetchTileData()
  }

  let intervals: any[] = []

  onMounted(() => {
    (window as any).handleAndroidBack = handleBackAction
    window.addEventListener('popstate', handlePopState)
    loadInitialState()

    intervals = [
      setInterval(fetchPresenceData, 2000),
      setInterval(fetchTileData, 5000),
      setInterval(syncCleanerStatus, 10000),
      setInterval(syncUsbStatus, 10000),
      setInterval(syncPcStatus, 10000),
      setInterval(fetchWeatherData, 600000),
    ]
  })

  onUnmounted(() => {
    delete (window as any).handleAndroidBack
    window.removeEventListener('popstate', handlePopState)
    intervals.forEach(clearInterval)
  })

  return {
    // Auth
    needsAuth,
    loadInitialState,

    // Nav
    activeTab,
    openedSheet,
    openSheet,
    closeSheet,
    switchTab,
    handleBackAction,

    // Toast
    toast,
    showToast,

    // AC
    acTemp,
    acMode,
    acFan,
    changeAcTemp,
    selectAcMode,
    selectAcFan,
    toggleAcPower,

    // Heater
    heaterTemp,
    heaterMode,
    heaterEco,
    heaterPower,
    changeHeaterTemp,
    selectHeaterMode,
    pressHeaterEco,
    pressHeaterPower,
    toggleHeaterPower,

    // Light
    lightOn,
    lightBrightness,
    toggleLight,
    selectLightAction,
    changeLightBrightness,

    // Cleaner
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

    // PC & USB
    pcOnline,
    pcBooting,
    pcShuttingDown,
    pcOs,
    pcTargetOs,
    usbPower,
    togglePcPower,
    selectPcPowerOption,
    selectPcOs,

    // Weather, Presence, Tile
    weather,
    presence,
    tile,

    // Assistant & Speech
    isSubmittingAssistant,
    isRecording,
    submitAssistantCommand,
    toggleVoiceRecognition,

    // Scenes & Automations
    runScene,
    runAutomation,
  }
}
