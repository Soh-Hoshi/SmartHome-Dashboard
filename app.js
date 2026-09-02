    // 状態管理
    const state = {
      acTemp: 26,           // 22℃ 〜 28℃ (整数値)
      animRatio: (26 - 22) / (28 - 22), // 現在の描画比率 (0.0 〜 1.0)
      acMode: 'cool',       // 'cool' | 'dry' | 'off'
      acFan: 'auto',        // 'auto' | 'low' | 'medium' | 'high'

      heaterTemp: 22,                       // 22℃ 〜 28℃ (整数値)
      heaterAnimRatio: (22 - 22) / (28 - 22),
      heaterMode: 'off',                    // 'heat' | 'off'
      heaterEco: false,                     // true | false
      heaterPower: 2,                       // 1 〜 3 (1: 弱, 2: 中, 3: 強)
      
      lightOn: false,
      lightFull: false,                     // 全灯 (true | false)
      lightNight: false,                    // 常夜灯 (true | false)
      lightBrightness: 3,                   // 明るさレベル (1〜5)

      cleanerStatus: 'charging',            // 'running' | 'standby' | 'charging' | 'sleeping' | 'recharge' | 'completed'
      cleanerPlay: false
    };

    // ファンモード用の統一アイコン
    const fanIcons = {
      auto: `<svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><path d="M12 11a1 1 0 1 0 1 1 1 1 0 0 0-1-1zm0-9a4 4 0 0 0-4 4 1 1 0 0 0 2 0 2 2 0 0 1 4 0c0 1.5-1.5 2.5-2 3.5v.5h1.5c1.5 0 2.5-1.5 3.5-2a4 4 0 0 0-5-6zm-6 9a2 2 0 0 1 0-4 4 4 0 0 0-4 4 1 1 0 0 0 2 0 2 2 0 0 1 2 0zm14.5 4h-1.1l-.4 1.2h-1.3l1.8-5h1.4l1.8 5h-1.3zm-.4-1.2l-.4-1.4-.4 1.4zM12 15a4 4 0 0 0 4-4 1 1 0 0 0-2 0 2 2 0 0 1-4 0c0-1.5 1.5-2.5 2-3.5v-.5h-1.5c-1.5 0-2.5 1.5-3.5 2a4 4 0 0 0 5 6z"/></svg>`,
      low: `<svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="2.5"/><path d="M12 4a3.5 3.5 0 0 0-3.5 3.5 1 1 0 0 0 2 0 1.5 1.5 0 0 1 3 0c0 1-1 1.8-1.5 2.5h1.5c1 0 2-1 2.5-2a3.5 3.5 0 0 0-4-4zm-8 8a3.5 3.5 0 0 0 3.5-3.5 1 1 0 0 0 0 2 1.5 1.5 0 0 1 0 3c-1 0-1.8-1-2.5-1.5v1.5c0 1 1 2 2 2.5a3.5 3.5 0 0 0-3-7.5zm8 8a3.5 3.5 0 0 0 3.5-3.5 1 1 0 0 0-2 0 1.5 1.5 0 0 1-3 0c0-1 1-1.8 1.5-2.5h-1.5c-1 0-2 1-2.5 2a3.5 3.5 0 0 0 4 4z"/><rect x="19" y="16" width="3" height="4" rx="1" fill="#38bdf8"/></svg>`,
      medium: `<svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="2.5"/><path d="M12 4a3.5 3.5 0 0 0-3.5 3.5 1 1 0 0 0 2 0 1.5 1.5 0 0 1 3 0c0 1-1 1.8-1.5 2.5h1.5c1 0 2-1 2.5-2a3.5 3.5 0 0 0-4-4zm-8 8a3.5 3.5 0 0 0 3.5-3.5 1 1 0 0 0 0 2 1.5 1.5 0 0 1 0 3c-1 0-1.8-1-2.5-1.5v1.5c0 1 1 2 2 2.5a3.5 3.5 0 0 0-3-7.5zm8 8a3.5 3.5 0 0 0 3.5-3.5 1 1 0 0 0-2 0 1.5 1.5 0 0 1-3 0c0-1 1-1.8 1.5-2.5h-1.5c-1 0-2 1-2.5 2a3.5 3.5 0 0 0 4 4z"/><rect x="17.5" y="14" width="2.5" height="6" rx="1" fill="#38bdf8"/><rect x="21" y="11" width="2.5" height="9" rx="1" fill="#38bdf8"/></svg>`,
      high: `<svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="2.5"/><path d="M12 4a3.5 3.5 0 0 0-3.5 3.5 1 1 0 0 0 2 0 1.5 1.5 0 0 1 3 0c0 1-1 1.8-1.5 2.5h1.5c1 0 2-1 2.5-2a3.5 3.5 0 0 0-4-4zm-8 8a3.5 3.5 0 0 0 3.5-3.5 1 1 0 0 0 0 2 1.5 1.5 0 0 1 0 3c-1 0-1.8-1-2.5-1.5v1.5c0 1 1 2 2 2.5a3.5 3.5 0 0 0-3-7.5zm8 8a3.5 3.5 0 0 0 3.5-3.5 1 1 0 0 0-2 0 1.5 1.5 0 0 1-3 0c0-1 1-1.8 1.5-2.5h-1.5c-1 0-2 1-2.5 2a3.5 3.5 0 0 0 4 4z"/><rect x="14" y="16" width="2.5" height="4" rx="1" fill="#38bdf8"/><rect x="17.5" y="13" width="2.5" height="7" rx="1" fill="#38bdf8"/><rect x="21" y="9" width="2.5" height="11" rx="1" fill="#38bdf8"/></svg>`
    };

    const modeIcons = {
      cool: `<span class="material-symbols-rounded text-2xl text-sky-400">ac_unit</span>`,
      dry: `<span class="material-symbols-rounded symbol-fill text-2xl text-cyan-400">water_drop</span>`,
      off: `<span class="material-symbols-rounded text-2xl text-neutral-400">power_settings_new</span>`
    };

    let isModalHistoryActive = false;

    /**
     * タブの切り替え (ダッシュボード / オートメーション / シーン / データ)
     * サイドバー(デスクトップ)とボトムナビ(モバイル)の両方を同期更新
     */
    function switchTab(tabId) {
      const tabs = ['dashboard', 'automations', 'scenes'];

      // ビューの表示/非表示切り替え
      tabs.forEach(t => {
        const viewEl = document.getElementById(`view-${t}`);
        if (viewEl) {
          if (t === tabId) {
            viewEl.classList.remove('hidden');
          } else {
            viewEl.classList.add('hidden');
          }
        }

        // デスクトップ用サイドバーボタンのスタイル切り替え (アイコン ＋ ホバー展開ラベル)
        const navBtn = document.getElementById(`nav-${t}`);
        if (navBtn) {
          const iconSpan = navBtn.querySelector('.material-symbols-rounded');
          const labelSpan = navBtn.querySelector('.sidebar-label');
          if (t === tabId) {
            navBtn.className = "nav-tab-btn w-full flex items-center px-2.5 py-2.5 rounded-2xl text-left transition-all duration-200 bg-[#253546] text-[#2196f3] active:scale-98";
            if (iconSpan) iconSpan.classList.add('symbol-fill');
            if (labelSpan) {
              labelSpan.className = "sidebar-label text-sm font-semibold text-[#2196f3] whitespace-nowrap overflow-hidden transition-all duration-200 opacity-0 group-hover/sidebar:opacity-100 max-w-0 group-hover/sidebar:max-w-[140px] group-hover/sidebar:ml-3";
            }
          } else {
            navBtn.className = "nav-tab-btn w-full flex items-center px-2.5 py-2.5 rounded-2xl text-left transition-all duration-200 bg-transparent hover:bg-white/[0.04] text-neutral-400 hover:text-white active:scale-98";
            if (iconSpan) iconSpan.classList.remove('symbol-fill');
            if (labelSpan) {
              labelSpan.className = "sidebar-label text-sm font-medium text-neutral-400 whitespace-nowrap overflow-hidden transition-all duration-200 opacity-0 group-hover/sidebar:opacity-100 max-w-0 group-hover/sidebar:max-w-[140px] group-hover/sidebar:ml-3";
            }
          }
        }

        // モバイル用ボトムナビボタンのスタイル切り替え (Google Homeスタイル)
        const bottomBtn = document.getElementById(`bottom-nav-${t}`);
        if (bottomBtn) {
          const iconWrap = bottomBtn.querySelector('.bottom-nav-icon-wrap');
          const iconSpan = bottomBtn.querySelector('.material-symbols-rounded');
          const labelSpan = bottomBtn.querySelector('.bottom-nav-label');

          if (t === tabId) {
            bottomBtn.className = "bottom-nav-btn flex flex-col items-center justify-center py-1 px-1 rounded-2xl transition-all duration-200 active:scale-95 text-[#2196f3]";
            if (iconWrap) {
              iconWrap.className = "bottom-nav-icon-wrap w-14 h-8 rounded-full flex items-center justify-center transition-all duration-200 bg-[#253546] text-[#2196f3]";
            }
            if (iconSpan) iconSpan.classList.add('symbol-fill');
            if (labelSpan) {
              labelSpan.className = "bottom-nav-label text-[11px] font-semibold mt-1 tracking-tight text-[#2196f3]";
            }
          } else {
            bottomBtn.className = "bottom-nav-btn flex flex-col items-center justify-center py-1 px-1 rounded-2xl transition-all duration-200 active:scale-95 text-neutral-400 hover:text-neutral-200";
            if (iconWrap) {
              iconWrap.className = "bottom-nav-icon-wrap w-14 h-8 rounded-full flex items-center justify-center transition-all duration-200 bg-transparent text-neutral-400";
            }
            if (iconSpan) iconSpan.classList.remove('symbol-fill');
            if (labelSpan) {
              labelSpan.className = "bottom-nav-label text-[11px] font-medium mt-1 tracking-tight text-neutral-400";
            }
          }
        }
      });

      // モバイル時に上部へスムーズスクロール
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    /**
     * ボトムシート開閉
     */
    function openSheet(sheetId) {
      const sheet = document.getElementById(sheetId);
      if (!sheet) return;
      closeAllDropups();
      
      sheet.classList.remove('hidden-sheet');
      sheet.classList.add('visible-sheet');
      document.body.style.overflow = 'hidden';

      // URLハッシュを変更せず、stateのみプッシュ（OSの左右スライドアニメーションを防止）
      if (!isModalHistoryActive) {
        history.pushState({ modalOpen: true, sheetId: sheetId }, '');
        isModalHistoryActive = true;
      }
    }

    /**
     * ✕ボタンや背景タップで閉じる（下へスライドダウンする自然なアニメーション）
     */
    function closeSheet(sheetId) {
      const sheet = document.getElementById(sheetId);
      if (sheet) {
        closeAllDropups();
        sheet.classList.remove('visible-sheet');
        sheet.classList.add('hidden-sheet');
        document.body.style.overflow = '';
      }

      if (isModalHistoryActive) {
        isModalHistoryActive = false;
        history.back();
      }
    }

    /**
     * ブラウザの戻る操作時（✕ボタンと同じく下へスッとスライドダウンして閉じる）
     */
    window.addEventListener('popstate', (e) => {
      closeAllDropups();
      document.querySelectorAll('.sheet-backdrop.visible-sheet').forEach(sheet => {
        sheet.classList.remove('visible-sheet');
        sheet.classList.add('hidden-sheet');
      });
      document.body.style.overflow = '';
      isModalHistoryActive = false;
    });

    // 背景クリックでシートを閉じる
    document.querySelectorAll('.sheet-backdrop').forEach(backdrop => {
      backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) {
          closeSheet(backdrop.id);
        }
      });
    });

    /**
     * ドロップアップの開閉管理
     */
    function toggleDropup(menuId, event) {
      if (event) event.stopPropagation();
      const targetMenu = document.getElementById(menuId);
      const isOpen = targetMenu.classList.contains('open');
      
      closeAllDropups();
      if (!isOpen) {
        targetMenu.classList.remove('closed');
        targetMenu.classList.add('open');
      }
    }

    function closeAllDropups() {
      document.querySelectorAll('.dropup-menu').forEach(menu => {
        menu.classList.remove('open');
        menu.classList.add('closed');
      });
    }

    document.addEventListener('click', (e) => {
      if (!e.target.closest('.dropup-menu') && 
          !e.target.closest('#btn-trigger-mode') && 
          !e.target.closest('#btn-trigger-fan') &&
          !e.target.closest('#btn-trigger-heater-mode') &&
          !e.target.closest('#btn-trigger-cleaner-speed')) {
        closeAllDropups();
      }
    });

    /**
     * 蹄型エアコン温度ゲージの描画
     */
    function renderAcGauge(ratio = state.animRatio) {
      const minTemp = 22;
      const maxTemp = 28;
      const totalArcLength = 494.8;
      
      const clampedRatio = Math.max(0, Math.min(1, ratio));

      const tempDisplay = document.getElementById('detail-ac-temp');
      const tempUnit = document.getElementById('detail-ac-temp-unit');
      const modeText = document.getElementById('detail-ac-mode-text');
      
      if (state.acMode === 'off') {
        if (tempDisplay) {
          tempDisplay.textContent = 'オフ';
          tempDisplay.className = "text-5xl font-bold tracking-tight text-white leading-none translate-y-1.5";
        }
        if (tempUnit) tempUnit.textContent = '';
        if (modeText) modeText.textContent = '';
      } else {
        const displayedTemp = Math.round(minTemp + clampedRatio * (maxTemp - minTemp));
        if (tempDisplay) {
          tempDisplay.textContent = displayedTemp;
          tempDisplay.className = "text-6xl font-bold tracking-tight text-white leading-none font-num translate-y-0";
        }
        if (tempUnit) tempUnit.textContent = '℃';
        const modeLabels = { cool: '冷房', dry: '除湿' };
        if (modeText) modeText.textContent = modeLabels[state.acMode] || '冷房';
      }

      const activePath = document.getElementById('ac-active-path');
      const trackBg = document.getElementById('ac-track-bg');
      const knobGroup = document.getElementById('ac-knob-group');

      if (trackBg) {
        if (state.acMode === 'cool') trackBg.setAttribute('stroke', 'rgba(33, 150, 243, 0.15)');
        else if (state.acMode === 'dry') trackBg.setAttribute('stroke', 'rgba(0, 188, 212, 0.15)');
        else trackBg.setAttribute('stroke', 'rgba(255, 255, 255, 0.05)');
      }

      if (activePath) {
        if (state.acMode === 'off') {
          activePath.style.display = 'none';
          activePath.setAttribute('stroke-dasharray', `0 ${totalArcLength}`);
        } else {
          activePath.style.display = '';
          const visibleLength = totalArcLength * clampedRatio;
          activePath.setAttribute('stroke-dasharray', `${visibleLength} ${totalArcLength}`);
          activePath.setAttribute('stroke-dashoffset', '0');
          
          if (state.acMode === 'cool') activePath.setAttribute('stroke', '#2196f3');
          else if (state.acMode === 'dry') activePath.setAttribute('stroke', '#00bcd4');
        }
      }

      if (knobGroup) {
        knobGroup.style.display = state.acMode === 'off' ? 'none' : '';
      }

      const startAngle = 135;
      const currentAngleDeg = startAngle + clampedRatio * 270;
      const currentAngleRad = currentAngleDeg * (Math.PI / 180);

      const knobX = 140 + 105 * Math.cos(currentAngleRad);
      const knobY = 140 + 105 * Math.sin(currentAngleRad);

      const knob = document.getElementById('ac-knob');
      const knobHit = document.getElementById('ac-knob-hit');
      if (knob) {
        knob.setAttribute('cx', knobX.toFixed(2));
        knob.setAttribute('cy', knobY.toFixed(2));
      }
      if (knobHit) {
        knobHit.setAttribute('cx', knobX.toFixed(2));
        knobHit.setAttribute('cy', knobY.toFixed(2));
      }
    }

    /**
     * 円周に100%沿った滑らかなアニメーション (エアコン)
     */
    let gaugeAnimFrame = null;
    function animateGaugeToRatio(targetRatio, duration = 280) {
      if (gaugeAnimFrame) cancelAnimationFrame(gaugeAnimFrame);
      const startRatio = state.animRatio;
      const diff = targetRatio - startRatio;
      if (Math.abs(diff) < 0.001) {
        state.animRatio = targetRatio;
        renderAcGauge(targetRatio);
        return;
      }

      const startTime = performance.now();

      function step(now) {
        const elapsed = now - startTime;
        const progress = Math.min(1, elapsed / duration);
        const ease = 1 - Math.pow(1 - progress, 3);
        state.animRatio = startRatio + diff * ease;
        renderAcGauge(state.animRatio);

        if (progress < 1) {
          gaugeAnimFrame = requestAnimationFrame(step);
        } else {
          state.animRatio = targetRatio;
          renderAcGauge(state.animRatio);
        }
      }
      gaugeAnimFrame = requestAnimationFrame(step);
    }

    // === SwitchBot バックエンド API 通信 ===
    const apiBasePath = window.location.pathname.startsWith('/dashboard') ? '/dashboard' : '';
    let acSyncTimeout = null;

    function syncAcToBackend() {
      if (acSyncTimeout) clearTimeout(acSyncTimeout);
      acSyncTimeout = setTimeout(() => {
        fetch(`${apiBasePath}/api/ac`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            mode: state.acMode,
            temp: state.acTemp,
            fan_mode: state.acFan
          })
        })
        .then(res => res.json())
        .then(data => console.log('[AC Synced with SwitchBot]', data))
        .catch(err => console.error('[AC Sync Failed]', err));
      }, 350);
    }

    /**
     * エアコン温度変更 (＋ / ー ボタン)
     */
    function changeAcTemp(delta) {
      if (state.acMode === 'off') {
        state.acMode = 'cool';
      }

      const newTemp = Math.min(28, Math.max(22, state.acTemp + delta));
      state.acTemp = newTemp;
      updateAcUi();
      const targetRatio = (newTemp - 22) / (28 - 22);
      animateGaugeToRatio(targetRatio, 260);
      syncAcToBackend();
    }

    /**
     * ノブ & ゲージのドラッグ・タッチ操作 (エアコン)
     */
    const gaugeSvg = document.getElementById('ac-gauge-svg');
    let isDraggingKnob = false;
    let currentDragRatio = (26 - 22) / (28 - 22);

    function handlePointerMove(e) {
      if (!isDraggingKnob) return;
      
      const rect = gaugeSvg.getBoundingClientRect();
      const clientX = e.clientX || (e.touches && e.touches[0].clientX);
      const clientY = e.clientY || (e.touches && e.touches[0].clientY);
      
      const x = ((clientX - rect.left) / rect.width) * 280;
      const y = ((clientY - rect.top) / rect.height) * 280;

      const dx = x - 140;
      const dy = y - 140;
      let angle = Math.atan2(dy, dx) * (180 / Math.PI);
      if (angle < 0) angle += 360;

      let mappedAngle;
      if (angle >= 135) {
        mappedAngle = angle;
      } else if (angle <= 45) {
        mappedAngle = angle + 360;
      } else {
        mappedAngle = angle < 90 ? 405 : 135;
      }

      currentDragRatio = Math.max(0, Math.min(1, (mappedAngle - 135) / 270));

      if (state.acMode === 'off') {
        state.acMode = 'cool';
      }

      state.acTemp = Math.round(22 + currentDragRatio * (28 - 22));
      updateAcTileStatusOnly();
      state.animRatio = currentDragRatio;
      renderAcGauge(currentDragRatio);
    }

    function startDrag(e) {
      if (gaugeAnimFrame) cancelAnimationFrame(gaugeAnimFrame);
      isDraggingKnob = true;
      handlePointerMove(e);
    }

    function stopDrag() {
      if (isDraggingKnob) {
        isDraggingKnob = false;
        const targetTemp = Math.round(22 + currentDragRatio * (28 - 22));
        state.acTemp = Math.min(28, Math.max(22, targetTemp));
        updateAcUi();
        const snapRatio = (state.acTemp - 22) / (28 - 22);
        animateGaugeToRatio(snapRatio, 200);
        syncAcToBackend();
      }
    }

    gaugeSvg.addEventListener('pointerdown', (e) => {
      startDrag(e);
      gaugeSvg.setPointerCapture(e.pointerId);
    });
    gaugeSvg.addEventListener('pointermove', handlePointerMove);
    gaugeSvg.addEventListener('pointerup', (e) => {
      stopDrag();
      try { gaugeSvg.releasePointerCapture(e.pointerId); } catch(err){}
    });
    gaugeSvg.addEventListener('pointercancel', stopDrag);

    /**
     * エアコンのモード選択
     */
    function selectAcMode(mode) {
      state.acMode = mode;
      closeAllDropups();
      updateAcUi();
      syncAcToBackend();
    }

    function setAcModeFromTile(mode, event) {
      if (event) event.stopPropagation();
      state.acMode = mode;
      updateAcUi();
      syncAcToBackend();
    }

    /**
     * タイルアイコンタップでエアコンの冷房 / オフをトグル
     */
    function toggleAcPowerFromTileIcon(event) {
      if (event) event.stopPropagation();
      state.acMode = state.acMode === 'off' ? 'cool' : 'off';
      updateAcUi();
      syncAcToBackend();
    }

    /**
     * ファンモード選択
     */
    function selectFanMode(fanMode) {
      state.acFan = fanMode;
      closeAllDropups();
      
      const fanLabels = { auto: '自動', low: '弱', medium: '中', high: '強' };
      document.getElementById('detail-fan-label').textContent = fanLabels[fanMode] || '自動';

      const fanIconContainer = document.getElementById('detail-fan-icon');
      if (fanIconContainer && fanIcons[fanMode]) {
        fanIconContainer.innerHTML = fanIcons[fanMode];
      }

      ['auto', 'low', 'medium', 'high'].forEach(f => {
        const checkEl = document.getElementById(`check-fan-${f}`);
        if (checkEl) {
          if (f === fanMode) checkEl.classList.remove('hidden');
          else checkEl.classList.add('hidden');
        }
      });
      syncAcToBackend();
    }

    /**
     * タイルステータステキストのみ更新 (エアコン)
     */
    function updateAcTileStatusOnly() {
      const tileStatus = document.getElementById('tile-ac-status');
      if (!tileStatus) return;
      if (state.acMode === 'off') {
        tileStatus.innerHTML = `<span>オフ</span>`;
      } else {
        const modeLabel = state.acMode === 'cool' ? '冷房' : '除湿';
        tileStatus.innerHTML = `<span>${modeLabel}</span><span>・</span><span>${state.acTemp}℃</span>`;
      }
    }

    /**
     * エアコン UI 全体の同期更新
     */
    function updateAcUi() {
      const mode = state.acMode;

      const btnOff = document.getElementById('tile-ac-btn-off');
      const btnDry = document.getElementById('tile-ac-btn-dry');
      const btnCool = document.getElementById('tile-ac-btn-cool');
      const tileIconWrap = document.getElementById('tile-ac-icon-wrap');

      const defaultBtnClass = "h-11 rounded-2xl bg-[#292c34] hover:bg-[#323640] flex items-center justify-center text-neutral-400 hover:text-white transition-all";
      const activeCoolClass = "h-11 rounded-2xl bg-[#253546] hover:bg-[#2e4156] text-[#2196f3] flex items-center justify-center transition-all";
      const activeDryClass  = "h-11 rounded-2xl bg-[#213840] hover:bg-[#284550] text-[#00bcd4] flex items-center justify-center transition-all";
      const activeOffClass  = "h-11 rounded-2xl bg-[#333741] hover:bg-[#3c414d] text-white flex items-center justify-center transition-all";

      btnOff.className = mode === 'off' ? activeOffClass : defaultBtnClass;
      btnDry.className = mode === 'dry' ? activeDryClass : defaultBtnClass;
      btnCool.className = mode === 'cool' ? activeCoolClass : defaultBtnClass;

      updateAcTileStatusOnly();

      if (mode === 'off') {
        tileIconWrap.className = "w-11 h-11 rounded-full bg-[#272a31] text-neutral-400 flex items-center justify-center transition-all duration-300 hover:scale-105 active:scale-95 shrink-0";
      } else if (mode === 'dry') {
        tileIconWrap.className = "w-11 h-11 rounded-full bg-[#213840] text-[#00bcd4] flex items-center justify-center transition-all duration-300 hover:scale-105 active:scale-95 shrink-0";
      } else {
        tileIconWrap.className = "w-11 h-11 rounded-full bg-[#253546] text-[#2196f3] flex items-center justify-center transition-all duration-300 hover:scale-105 active:scale-95 shrink-0";
      }

      const modeLabel = document.getElementById('detail-mode-label');
      const modeIcon = document.getElementById('detail-mode-icon');
      const modeNames = { cool: '冷房', dry: '除湿', off: 'オフ' };
      if (modeLabel) modeLabel.textContent = modeNames[mode] || '冷房';

      if (modeIcon && modeIcons[mode]) {
        modeIcon.innerHTML = modeIcons[mode];
      }

      ['cool', 'dry', 'off'].forEach(m => {
        const checkEl = document.getElementById(`check-mode-${m}`);
        if (checkEl) {
          if (m === mode) checkEl.classList.remove('hidden');
          else checkEl.classList.add('hidden');
        }
      });

      renderAcGauge();
    }

    /* ======================================================================= */
    /* ヒーター（暖房）関連ロジック                                             */
    /* ======================================================================= */

    /**
     * 蹄型ヒーター温度ゲージの描画 (ノブなし・22℃〜28℃)
     */
    function renderHeaterGauge(ratio = state.heaterAnimRatio) {
      const minTemp = 22;
      const maxTemp = 28;
      const totalArcLength = 494.8;
      
      const clampedRatio = Math.max(0, Math.min(1, ratio));

      const tempDisplay = document.getElementById('detail-heater-temp');
      const tempUnit = document.getElementById('detail-heater-temp-unit');
      const modeText = document.getElementById('detail-heater-mode-text');
      
      if (state.heaterMode === 'off') {
        if (tempDisplay) {
          tempDisplay.textContent = 'オフ';
          tempDisplay.className = "text-5xl font-bold tracking-tight text-white leading-none translate-y-1.5";
        }
        if (tempUnit) tempUnit.textContent = '';
        if (modeText) modeText.textContent = '';
      } else {
        const displayedTemp = Math.round(minTemp + clampedRatio * (maxTemp - minTemp));
        if (tempDisplay) {
          tempDisplay.textContent = displayedTemp;
          tempDisplay.className = "text-6xl font-bold tracking-tight text-white leading-none font-num translate-y-0";
        }
        if (tempUnit) tempUnit.textContent = '℃';
        if (modeText) modeText.textContent = '暖房';
      }

      const activePath = document.getElementById('heater-active-path');
      const trackBg = document.getElementById('heater-track-bg');

      if (trackBg) {
        if (state.heaterMode === 'heat') trackBg.setAttribute('stroke', 'rgba(234, 122, 30, 0.15)');
        else trackBg.setAttribute('stroke', 'rgba(255, 255, 255, 0.05)');
      }

      if (activePath) {
        if (state.heaterMode === 'off') {
          activePath.style.display = 'none';
          activePath.setAttribute('stroke-dasharray', `0 ${totalArcLength}`);
        } else {
          activePath.style.display = '';
          const visibleLength = totalArcLength * clampedRatio;
          activePath.setAttribute('stroke-dasharray', `${visibleLength} ${totalArcLength}`);
          activePath.setAttribute('stroke-dashoffset', '0');
          activePath.setAttribute('stroke', '#ea7a1e');
        }
      }
    }

    /**
     * ヒーターゲージのアニメーション伸縮
     */
    let heaterGaugeAnimFrame = null;
    function animateHeaterGaugeToRatio(targetRatio, duration = 260) {
      if (heaterGaugeAnimFrame) cancelAnimationFrame(heaterGaugeAnimFrame);
      const startRatio = state.heaterAnimRatio;
      const diff = targetRatio - startRatio;
      if (Math.abs(diff) < 0.001) {
        state.heaterAnimRatio = targetRatio;
        renderHeaterGauge(targetRatio);
        return;
      }

      const startTime = performance.now();

      function step(now) {
        const elapsed = now - startTime;
        const progress = Math.min(1, elapsed / duration);
        const ease = 1 - Math.pow(1 - progress, 3);
        state.heaterAnimRatio = startRatio + diff * ease;
        renderHeaterGauge(state.heaterAnimRatio);

        if (progress < 1) {
          heaterGaugeAnimFrame = requestAnimationFrame(step);
        } else {
          state.heaterAnimRatio = targetRatio;
          renderHeaterGauge(state.heaterAnimRatio);
        }
      }
      heaterGaugeAnimFrame = requestAnimationFrame(step);
    }

    /**
     * ヒーター SwitchBot バックエンド API 通信
     */
    function sendHeaterCommand(action, extraParams = {}) {
      fetch(`${apiBasePath}/api/heater`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: action, ...extraParams })
      })
      .then(res => res.json())
      .then(data => console.log('[Heater Synced with SwitchBot]', data))
      .catch(err => console.error('[Heater Sync Failed]', err));
    }

    /**
     * ヒーター温度変更 (＋ / ー ボタン)
     */
    function changeHeaterTemp(delta) {
      if (state.heaterMode === 'off') {
        state.heaterMode = 'heat';
        sendHeaterCommand('turnOn');
      }

      const newTemp = Math.min(28, Math.max(22, state.heaterTemp + delta));
      state.heaterTemp = newTemp;
      updateHeaterUi();
      const targetRatio = (newTemp - 22) / (28 - 22);
      animateHeaterGaugeToRatio(targetRatio, 240);
      sendHeaterCommand(delta > 0 ? 'plus' : 'minus');
    }

    /**
     * ヒーターのモード選択
     */
    function selectHeaterMode(mode) {
      const prevMode = state.heaterMode;
      state.heaterMode = mode;
      closeAllDropups();
      updateHeaterUi();
      if (prevMode !== mode) {
        sendHeaterCommand(mode === 'heat' ? 'turnOn' : 'turnOff');
      }
    }

    /**
     * ヒーターエコボタン押下 (SwitchBotの「エコ」コマンドを送信)
     */
    function pressHeaterEco() {
      if (state.heaterMode === 'off') return;
      sendHeaterCommand('eco');
    }

    /**
     * ヒーターパワーボタン押下 (SwitchBotの「パワー」コマンドを送信)
     */
    function pressHeaterPower() {
      if (state.heaterMode === 'off') return;
      sendHeaterCommand('power');
    }

    /**
     * ヒータータイルアイコンからのオン/オフトグル
     */
    function toggleHeaterFromTile(event) {
      if (event) event.stopPropagation();
      state.heaterMode = state.heaterMode === 'off' ? 'heat' : 'off';
      updateHeaterUi();
      sendHeaterCommand(state.heaterMode === 'heat' ? 'turnOn' : 'turnOff');
    }

    /**
     * ヒーター UI 全体の同期更新
     */
    function updateHeaterUi() {
      const mode = state.heaterMode;
      const isOff = mode === 'off';

      // タイル更新
      const tileStatus = document.getElementById('tile-heater-status');
      const tileIconWrap = document.getElementById('tile-heater-icon-wrap');
      if (tileStatus) {
        if (isOff) {
          tileStatus.innerHTML = `<span>オフ</span>`;
        } else {
          tileStatus.innerHTML = `<span>暖房</span><span>・</span><span>${state.heaterTemp}℃</span>`;
        }
      }
      if (tileIconWrap) {
        if (isOff) {
          tileIconWrap.className = "w-11 h-11 rounded-full bg-[#272a31] text-neutral-400 flex items-center justify-center transition-all duration-300 hover:scale-105 active:scale-95 shrink-0";
        } else {
          tileIconWrap.className = "w-11 h-11 rounded-full bg-[#3a2c24] text-[#ea7a1e] flex items-center justify-center transition-all duration-300 hover:scale-105 active:scale-95 shrink-0";
        }
      }

      // 詳細画面: モードアイコン & ラベル & チェック
      const heaterModeIcons = {
        heat: `<span class="material-symbols-rounded text-2xl text-orange-400">mode_heat</span>`,
        off: `<span class="material-symbols-rounded text-2xl text-neutral-400">power_settings_new</span>`
      };
      const heaterModeIcon = document.getElementById('detail-heater-mode-icon');
      if (heaterModeIcon) {
        heaterModeIcon.innerHTML = isOff ? heaterModeIcons.off : heaterModeIcons.heat;
      }

      const modeLabel = document.getElementById('detail-heater-mode-label');
      if (modeLabel) modeLabel.textContent = isOff ? 'オフ' : '暖房';
      
      const checkHeat = document.getElementById('check-heater-heat');
      const checkOff = document.getElementById('check-heater-off');
      if (checkHeat) checkHeat.className = isOff ? 'hidden text-orange-400 flex items-center' : 'text-orange-400 flex items-center';
      if (checkOff) checkOff.className = isOff ? 'text-neutral-400 flex items-center' : 'hidden text-neutral-400 flex items-center';

      // 詳細画面: エコ & パワーボタン（オフ時は無効化）
      const btnEco = document.getElementById('btn-heater-eco');
      const btnPower = document.getElementById('btn-heater-power');
      if (btnEco) btnEco.disabled = isOff;
      if (btnPower) btnPower.disabled = isOff;

      renderHeaterGauge();
    }

    /**
     * ライト SwitchBot バックエンド API 通信
     */
    function sendLightCommand(action) {
      fetch(`${apiBasePath}/api/light`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: action })
      })
      .then(res => res.json())
      .then(data => console.log('[Light Synced with SwitchBot]', data))
      .catch(err => console.error('[Light Sync Failed]', err));
    }

    /**
     * ライトタイルからのオン/オフトグル
     */
    function toggleLightFromTile(event) {
      if (event) event.stopPropagation();
      toggleLightDetail();
    }

    /**
     * 全灯ボタン (単発プッシュ: オンにして全灯コマンド送信)
     */
    function pressLightFull() {
      state.lightOn = true;
      updateLightUi();
      sendLightCommand('full');
    }

    /**
     * 常夜灯ボタン (単発プッシュ: オンにして常夜灯コマンド送信)
     */
    function pressLightNight() {
      state.lightOn = true;
      updateLightUi();
      sendLightCommand('night');
    }

    /**
     * 明るさ変更 (プラス / マイナス)
     */
    function changeLightBrightness(delta) {
      if (!state.lightOn) return;
      state.lightBrightness = Math.min(5, Math.max(1, state.lightBrightness + delta));
      updateLightUi();
      sendLightCommand(delta > 0 ? 'brightnessUp' : 'brightnessDown');
    }

    /**
     * ライト詳細画面の点灯・消灯トグル
     */
    function toggleLightDetail() {
      state.lightOn = !state.lightOn;
      updateLightUi();
      sendLightCommand(state.lightOn ? 'turnOn' : 'turnOff');
    }

    /**
     * ライト UI 全体の同期更新
     */
    function updateLightUi() {
      const isOn = state.lightOn;
      const containerEl = document.getElementById('light-slider-container');
      const blockEl = document.getElementById('light-detail-block');
      const iconWrap = document.getElementById('light-detail-icon-wrap');
      const titleEl = document.getElementById('detail-light-title');

      const tileStatus = document.getElementById('tile-light-status');
      const tileIconWrap = document.getElementById('tile-light-icon-wrap');

      if (isOn) {
        if (titleEl) titleEl.textContent = 'オン';
        if (containerEl) containerEl.style.backgroundColor = '#443717';
        if (blockEl) {
          blockEl.style.transform = 'translateY(-112px)';
          blockEl.style.backgroundColor = '#fbc02d';
          blockEl.style.boxShadow = '0 6px 18px rgba(0, 0, 0, 0.35)';
        }
        
        if (iconWrap) iconWrap.innerHTML = `<span class="material-symbols-rounded text-3xl text-white">power_settings_new</span>`;

        if (tileStatus) tileStatus.textContent = 'オン';
        if (tileIconWrap) {
          tileIconWrap.className = "w-11 h-11 rounded-full bg-[#383226] text-amber-400 flex items-center justify-center transition-all duration-300 hover:scale-105 active:scale-95 shrink-0";
        }
      } else {
        if (titleEl) titleEl.textContent = 'オフ';
        if (containerEl) containerEl.style.backgroundColor = '#282b32';
        if (blockEl) {
          blockEl.style.transform = 'translateY(0)';
          blockEl.style.backgroundColor = '#434752';
          blockEl.style.boxShadow = 'none';
        }
        
        if (iconWrap) iconWrap.innerHTML = `<div class="w-7 h-7 rounded-full border-2 border-neutral-300"></div>`;

        if (tileStatus) tileStatus.textContent = 'オフ';
        if (tileIconWrap) {
          tileIconWrap.className = "w-11 h-11 rounded-full bg-[#272a31] text-neutral-400 flex items-center justify-center transition-all duration-300 hover:scale-105 active:scale-95 shrink-0";
        }
      }

      // 詳細画面: 全灯・常夜灯アイコン
      const fullIcon = document.getElementById('detail-light-full-icon');
      if (fullIcon) {
        fullIcon.className = isOn
          ? "text-amber-400 shrink-0 flex items-center justify-center transition-colors"
          : "text-neutral-400 shrink-0 flex items-center justify-center transition-colors";
      }

      const nightIcon = document.getElementById('detail-light-night-icon');
      if (nightIcon) {
        nightIcon.className = isOn
          ? "text-amber-300 shrink-0 flex items-center justify-center transition-colors"
          : "text-neutral-400 shrink-0 flex items-center justify-center transition-colors";
      }

      // 詳細画面: 明るさカード (オフ時はボタン無効化)
      const brightnessIcon = document.getElementById('detail-light-brightness-icon');
      const btnBrightnessMinus = document.getElementById('btn-light-brightness-minus');
      const btnBrightnessPlus = document.getElementById('btn-light-brightness-plus');

      if (brightnessIcon) {
        brightnessIcon.className = isOn
          ? "material-symbols-rounded text-2xl text-amber-400 shrink-0 transition-colors"
          : "material-symbols-rounded text-2xl text-neutral-400 shrink-0 transition-colors";
      }
      if (btnBrightnessMinus) btnBrightnessMinus.disabled = !isOn;
      if (btnBrightnessPlus) btnBrightnessPlus.disabled = !isOn;
    }

    // クリーナー操作 (タイルから起動/一時停止/停止)
    async function setCleanerModeFromTile(action, event) {
      if (event) event.stopPropagation();

      // 楽観的UI更新
      if (action === 'start') {
        state.cleanerStatus = 'running';
        state.cleanerPlay = true;
      } else if (action === 'pause') {
        state.cleanerStatus = 'standby';
        state.cleanerPlay = false;
      } else if (action === 'stop') {
        state.cleanerStatus = 'recharge';
        state.cleanerPlay = false;
      }
      updateCleanerUi();

      try {
        const res = await fetch(`${apiBasePath}/api/cleaner`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: action })
        });
        if (res.ok) {
          const data = await res.json();
          if (data.state) {
            Object.assign(state, data.state);
            updateCleanerUi();
          }
        }
      } catch (e) {
        console.error('[Cleaner Control Error]', e);
      } finally {
        // 実機が状態変更した後の真のステータスを取得
        setTimeout(syncCleanerStatus, 1500);
      }
    }

    /**
     * クリーナータイル アイコンクリックで開始/停止をトグル
     */
    function toggleCleanerPowerFromTile(event) {
      if (event) event.stopPropagation();
      const status = (state.cleanerStatus || '').toLowerCase();
      const isRunning = status === 'running' && state.cleanerPlay === true;
      if (isRunning) {
        setCleanerModeFromTile('stop', event);
      } else {
        setCleanerModeFromTile('start', event);
      }
    }

    // クリーナーUI更新
    function updateCleanerUi() {
      const tileStatus = document.getElementById('tile-cleaner-status');
      const tileIconWrap = document.getElementById('tile-cleaner-icon-wrap');
      const btnStart = document.getElementById('tile-cleaner-btn-start');
      const btnPause = document.getElementById('tile-cleaner-btn-pause');
      const btnStop = document.getElementById('tile-cleaner-btn-stop');

      const status = (state.cleanerStatus || 'charging').toLowerCase();
      // 清掃中判定: statusが'running' かつ 帰還中(recharge)や充電中(charging)ではないこと
      const isRunning = status === 'running' && state.cleanerPlay === true;
      const isPaused = status === 'standby';
      const isCharging = status === 'charging';
      const isRecharging = status === 'recharge';
      const isCompleted = status === 'completed';

      // ステータス文言
      let statusText = '待機中';
      if (isCharging) {
        statusText = '充電中';
      } else if (isRecharging) {
        statusText = '帰還中';
      } else if (isRunning) {
        statusText = '清掃中';
      } else if (isPaused) {
        statusText = '一時停止中';
      } else if (isCompleted) {
        statusText = '充電完了';
      }

      // タイルステータステキスト
      if (tileStatus) {
        tileStatus.textContent = statusText;
        tileStatus.className = isRunning
          ? "text-xs text-sky-400 font-normal mt-0.5 transition-colors"
          : "text-xs text-neutral-400 font-normal mt-0.5 transition-colors";
      }

      // タイル丸アイコン
      if (tileIconWrap) {
        tileIconWrap.className = isRunning
          ? "w-11 h-11 rounded-full bg-[#253546] text-[#2196f3] flex items-center justify-center transition-all duration-300 hover:scale-105 active:scale-95 shadow-sm shrink-0"
          : "w-11 h-11 rounded-full bg-[#272a31] text-neutral-400 flex items-center justify-center transition-all duration-300 hover:scale-105 active:scale-95 shrink-0";
      }

      // タイル操作ボタン
      const neutralBtnClass = "h-11 rounded-2xl bg-[#292c34] hover:bg-[#323640] flex items-center justify-center text-neutral-400 hover:text-white transition-all active:scale-95";
      const activeStartClass = "h-11 rounded-2xl bg-[#253546] hover:bg-[#2e4156] text-[#2196f3] flex items-center justify-center transition-all active:scale-95";
      const activePauseClass = "h-11 rounded-2xl bg-[#333741] hover:bg-[#3c414d] text-white flex items-center justify-center transition-all active:scale-95";
      const activeStopClass  = "h-11 rounded-2xl bg-[#253546] hover:bg-[#2e4156] text-[#2196f3] flex items-center justify-center transition-all active:scale-95";

      if (btnStart) btnStart.className = isRunning ? activeStartClass : neutralBtnClass;
      if (btnPause) btnPause.className = isPaused ? activePauseClass : neutralBtnClass;
      if (btnStop) btnStop.className = isRecharging ? activeStopClass : neutralBtnClass;

      // 詳細画面 (cleaner-sheet) UI更新
      const detailMainStatus = document.getElementById('detail-cleaner-main-status');
      const detailHeroIcon = document.getElementById('detail-cleaner-hero-icon');
      const detailBatteryIcon = document.getElementById('detail-cleaner-battery-icon');

      if (detailMainStatus) detailMainStatus.textContent = statusText;

      if (detailHeroIcon) {
        if (isRunning) {
          // 清掃中: 水色 + うねうね回転
          detailHeroIcon.className = "relative z-10 text-[#38bdf8] transition-colors duration-300 animate-cleaner-moving";
        } else if (isRecharging) {
          // 帰還中: 通常色(グレー) + うねうね回転 (掃除はしていないので水色にしない)
          detailHeroIcon.className = "relative z-10 text-neutral-400 transition-colors duration-300 animate-cleaner-moving";
        } else {
          // 停止中・充電中・一時停止中: 通常色 + 静止
          detailHeroIcon.className = "relative z-10 text-neutral-400 transition-colors duration-300";
        }
      }

      if (detailBatteryIcon) {
        detailBatteryIcon.textContent = isCharging ? 'battery_charging_full' : 'battery_full';
        detailBatteryIcon.className = isCharging
          ? "material-symbols-rounded text-base text-sky-400"
          : "material-symbols-rounded text-base text-neutral-300";
      }

      // 詳細画面のメトリクス表示 (清掃中/一時停止中のみ数値表示、充電中/待機中は--)
      const timeEl = document.getElementById('detail-cleaner-stat-time');
      const areaEl = document.getElementById('detail-cleaner-stat-area');
      const mopEl = document.getElementById('detail-cleaner-stat-mop');

      if (timeEl) {
        if (isRunning || isPaused) {
          const t = state.cleanerTimeMin !== undefined ? state.cleanerTimeMin : 0;
          timeEl.innerHTML = `${t}<span class="text-[11px] font-normal text-neutral-400 ml-0.5">分</span>`;
        } else {
          timeEl.innerHTML = `--<span class="text-[11px] font-normal text-neutral-400 ml-0.5">分</span>`;
        }
      }

      if (areaEl) {
        if (isRunning || isPaused) {
          const a = state.cleanerArea !== undefined ? state.cleanerArea : 0;
          areaEl.innerHTML = `${a}<span class="text-[11px] font-normal text-neutral-400 ml-0.5">㎡</span>`;
        } else {
          areaEl.innerHTML = `--<span class="text-[11px] font-normal text-neutral-400 ml-0.5">㎡</span>`;
        }
      }
    }

    /**
     * 吸引力選択 (ドロップアップ) ＆ 実機へ送信
     */
    async function selectCleanerSpeed(speed) {
      closeAllDropups();
      state.cleanerSpeed = speed;

      const speedMap = {
        Standard: '標準',
        Boost_IQ: 'BoostIQ',
        Max: '最大'
      };
      const speedLabel = document.getElementById('detail-cleaner-speed-label');
      if (speedLabel) speedLabel.textContent = speedMap[speed] || speed;

      ['standard', 'boostiq', 'max'].forEach(s => {
        const checkEl = document.getElementById(`check-cleaner-speed-${s}`);
        if (checkEl) {
          const match = (s === 'standard' && speed === 'Standard') ||
                        (s === 'boostiq' && speed === 'Boost_IQ') ||
                        (s === 'max' && speed === 'Max');
          if (match) checkEl.classList.remove('hidden');
          else checkEl.classList.add('hidden');
        }
      });

      try {
        await fetch(`${apiBasePath}/api/cleaner`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'speed', speed: speed })
        });
      } catch (e) {
        console.error('[Cleaner Speed Error]', e);
      } finally {
        setTimeout(syncCleanerStatus, 1500);
      }
    }

    /**
     * Find Me ボタン (探す) ＆ 実機へ送信
     */
    async function pressCleanerFindMe() {
      const btn = document.getElementById('btn-cleaner-find-me');
      if (btn) {
        btn.classList.add('scale-95');
        setTimeout(() => btn.classList.remove('scale-95'), 150);
      }

      try {
        await fetch(`${apiBasePath}/api/cleaner`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'find_me' })
        });
      } catch (e) {
        console.error('[Cleaner Find Me Error]', e);
      }
    }

    // クリーナー実機ステータス同期
    async function syncCleanerStatus() {
      try {
        const res = await fetch(`${apiBasePath}/api/cleaner/status`);
        if (res.ok) {
          const data = await res.json();
          if (data.success) {
            state.cleanerStatus = (data.status || 'charging').toLowerCase();
            state.cleanerPlay = data.play || false;
            state.cleanerTimeMin = data.clean_time_min || 0;
            state.cleanerArea = data.clean_area || 0;

            // バッテリー残量
            const batteryEl = document.getElementById('detail-cleaner-battery-text');
            if (batteryEl && data.battery !== undefined) {
              batteryEl.textContent = `${data.battery}%`;
            }

            // モップ
            const mopEl = document.getElementById('detail-cleaner-stat-mop');
            if (mopEl && data.mop_attached !== undefined) {
              mopEl.textContent = data.mop_attached ? '装着中' : '未装着';
              mopEl.className = data.mop_attached ? "text-sm font-bold text-sky-400 mt-0.5" : "text-sm font-bold text-neutral-300 mt-0.5";
            }

            // 吸引力
            const speedEl = document.getElementById('detail-cleaner-speed-label');
            if (speedEl && data.speed) {
              const speedMap = { Standard: '標準', Boost_IQ: 'BoostIQ', Max: '最大', No_suction: '静音' };
              speedEl.textContent = speedMap[data.speed] || data.speed;
            }

            updateCleanerUi();
          }
        }
      } catch (e) {
        // サイレントキャッチ
      }
    }

    // 初期化 & サーバー状態同期
    async function loadInitialState() {
      try {
        const res = await fetch(`${apiBasePath}/api/state`);
        if (res.ok) {
          const data = await res.json();
          if (data.state) {
            Object.assign(state, data.state);
            state.animRatio = (state.acTemp - 22) / (28 - 22);
            state.heaterAnimRatio = (state.heaterTemp - 22) / (28 - 22);
            
            // ファンモードUIも更新
            if (state.acFan) {
              const fanLabels = { auto: '自動', low: '弱', medium: '中', high: '強' };
              const fanLblEl = document.getElementById('detail-fan-label');
              if (fanLblEl) fanLblEl.textContent = fanLabels[state.acFan] || '自動';
              const fanIconContainer = document.getElementById('detail-fan-icon');
              if (fanIconContainer && fanIcons[state.acFan]) {
                fanIconContainer.innerHTML = fanIcons[state.acFan];
              }
              ['auto', 'low', 'medium', 'high'].forEach(f => {
                const checkEl = document.getElementById(`check-fan-${f}`);
                if (checkEl) {
                  if (f === state.acFan) checkEl.classList.remove('hidden');
                  else checkEl.classList.add('hidden');
                }
              });
            }

            renderAcGauge();
            updateAcUi();
            renderHeaterGauge();
            updateHeaterUi();
            updateLightUi();
            updateCleanerUi();
          }
        }
      } catch (e) {
        console.warn('[State Load Warning]', e);
      }
      // クリーナーの実機ステータスを取得
      syncCleanerStatus();
    }

    // =========================================================================
    // AI スマートホーム アシスタント & 音声コマンド連携
    // =========================================================================
    let toastTimeout = null;

    function showAssistantToast(message, icon = 'auto_awesome', isError = false) {
      const toast = document.getElementById('assistant-toast');
      const toastText = document.getElementById('assistant-toast-text');
      const toastIcon = document.getElementById('assistant-toast-icon');
      if (!toast || !toastText) return;

      if (toastTimeout) clearTimeout(toastTimeout);

      toastText.textContent = message;
      if (toastIcon) {
        toastIcon.textContent = icon;
        toastIcon.className = `material-symbols-rounded text-lg ${isError ? 'text-rose-400' : 'text-[#2196f3]'}`;
      }

      toast.classList.remove('hidden');
      requestAnimationFrame(() => {
        toast.classList.remove('opacity-0', 'translate-y-2');
        toast.classList.add('opacity-100', 'translate-y-0');
      });

      toastTimeout = setTimeout(() => {
        toast.classList.remove('opacity-100', 'translate-y-0');
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.classList.add('hidden'), 300);
      }, 4000);
    }

    async function submitAssistantCommand(promptText) {
      if (!promptText || !promptText.trim()) return;
      const inputEl = document.getElementById('command-search-input');
      const sparkleIcon = document.getElementById('assistant-sparkle-icon');

      if (sparkleIcon) sparkleIcon.classList.add('animate-spin');

      try {
        const res = await fetch(`${apiBasePath}/api/assistant`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: promptText.trim() })
        });

        const data = await res.json();
        if (data.message) {
          showAssistantToast(data.message, data.success ? 'auto_awesome' : 'info', !data.success);
        }

        // 状態を画面UIに即座に反映
        if (data.state) {
          Object.assign(state, data.state);
          state.animRatio = (state.acTemp - 22) / (28 - 22);
          state.heaterAnimRatio = (state.heaterTemp - 22) / (28 - 22);
          renderAcGauge();
          updateAcUi();
          renderHeaterGauge();
          updateHeaterUi();
          updateLightUi();
          updateCleanerUi();
        }

        if (inputEl) inputEl.value = '';
      } catch (err) {
        showAssistantToast('コマンドの送信に失敗しました。', 'error', true);
        console.error('[Assistant Error]', err);
      } finally {
        if (sparkleIcon) sparkleIcon.classList.remove('animate-spin');
      }
    }

    // =========================================================================
    // 高速ストリーミング音声認識 (Web Speech API / Google & Apple Engine)
    // =========================================================================
    let recognition = null;
    let isRecording = false;
    let finalTranscript = '';

    function initSpeechRecognition() {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) return null;

      const rec = new SpeechRecognition();
      rec.lang = 'ja-JP';
      rec.interimResults = true; // リアルタイムでストリーミング認識
      rec.maxAlternatives = 1;
      rec.continuous = false;

      rec.onstart = () => {
        isRecording = true;
        finalTranscript = '';
        const micIcon = document.getElementById('voice-mic-icon');
        const micBtn = document.getElementById('btn-voice-command');
        const cmdBar = document.getElementById('command-bar-container');
        const inputEl = document.getElementById('command-search-input');

        if (micBtn) micBtn.classList.add('voice-listening');
        if (micIcon) micIcon.textContent = 'graphic_eq';
        if (cmdBar) cmdBar.classList.add('ring-2', 'ring-rose-500/40', 'border-rose-500/50');
        if (inputEl) inputEl.placeholder = 'Novaがお聞きしています...（例: 電気消して、エアコン24度）';

        showAssistantToast('Novaがお聞きしています...', 'mic', false);
      };

      rec.onresult = (e) => {
        let interimTranscript = '';
        for (let i = e.resultIndex; i < e.results.length; ++i) {
          const res = e.results[i];
          if (res.isFinal) {
            finalTranscript += res[0].transcript;
          } else {
            interimTranscript += res[0].transcript;
          }
        }

        const inputEl = document.getElementById('command-search-input');
        const displayText = finalTranscript || interimTranscript;
        if (inputEl && displayText) {
          inputEl.value = displayText;
        }

        // 最終結果が確定したら即時実行
        if (finalTranscript) {
          stopVoiceRecognition();
          submitAssistantCommand(finalTranscript);
        }
      };

      rec.onerror = (e) => {
        console.warn('[Speech Recognition Error]', e.error);
        if (e.error === 'not-allowed') {
          showAssistantToast('マイクの使用が許可されていません。ブラウザ設定をご確認ください。', 'mic_off', true);
        } else if (e.error !== 'no-speech') {
          showAssistantToast('音声を認識できませんでした。', 'mic_off', true);
        }
        stopVoiceRecognition();
      };

      rec.onend = () => {
        stopVoiceRecognition();
        // 最終確定テキストがあり未送信なら送信
        if (finalTranscript && isRecording) {
          submitAssistantCommand(finalTranscript);
        }
      };

      return rec;
    }

    function toggleVoiceRecognition() {
      if (!recognition) {
        recognition = initSpeechRecognition();
      }
      if (!recognition) {
        showAssistantToast('お使いのブラウザは音声認識に対応していません。テキスト入力をご利用ください。', 'info', true);
        return;
      }

      if (isRecording) {
        recognition.stop();
      } else {
        try {
          recognition.start();
        } catch (err) {
          try {
            recognition.abort();
            setTimeout(() => recognition.start(), 150);
          } catch (e2) {
            stopVoiceRecognition();
          }
        }
      }
    }

    function stopVoiceRecognition() {
      isRecording = false;
      const micIcon = document.getElementById('voice-mic-icon');
      const micBtn = document.getElementById('btn-voice-command');
      const cmdBar = document.getElementById('command-bar-container');
      const inputEl = document.getElementById('command-search-input');

      if (micBtn) micBtn.classList.remove('voice-listening');
      if (micIcon) micIcon.textContent = 'mic';
      if (cmdBar) cmdBar.classList.remove('ring-2', 'ring-rose-500/40', 'border-rose-500/50');
      if (inputEl) inputEl.placeholder = 'Novaに話しかける...';
    }

    async function fetchWeatherData() {
      try {
        const basePath = window.location.pathname.startsWith('/dashboard') ? '/dashboard' : '';
        const res = await fetch(basePath + '/api/weather');
        const data = await res.json();
        if (data.status === 'success' && data.weather) {
          const w = data.weather;
          
          // 1. ダッシュボードの気象タイル更新
          const tileStatus = document.getElementById('tile-weather-status');
          const tileIcon = document.getElementById('tile-weather-icon');
          if (tileStatus) tileStatus.textContent = `${w.weather}・${w.temp}℃`;
          if (tileIcon && w.weather_icon) tileIcon.textContent = w.weather_icon;

          // 2. 気象詳細モーダル更新
          const sheetIcon = document.getElementById('sheet-weather-icon');
          const sheetCond = document.getElementById('sheet-weather-condition');
          const sheetTemp = document.getElementById('sheet-weather-temp');
          const sheetRange = document.getElementById('sheet-weather-range');
          const sheetHum = document.getElementById('sheet-weather-humidity');
          const sheetWind = document.getElementById('sheet-weather-wind');
          const sheetSunset = document.getElementById('sheet-weather-sunset');
          const sheetSunrise = document.getElementById('sheet-weather-sunrise');

          if (sheetIcon && w.weather_icon) sheetIcon.textContent = w.weather_icon;
          if (sheetCond) sheetCond.textContent = w.weather;
          if (sheetTemp) sheetTemp.textContent = w.temp;
          if (sheetRange) {
            sheetRange.textContent = `最高 ${w.temp_max}℃ / 最低 ${w.temp_min}℃ ・ 体感 ${w.feels_like}℃`;
          }
          if (sheetHum) sheetHum.textContent = `${w.humidity}%`;
          if (sheetWind) sheetWind.textContent = `${w.wind_speed} m/s`;
          if (sheetSunset) sheetSunset.textContent = w.sunset;
          if (sheetSunrise) sheetSunrise.textContent = w.sunrise;

          // 3. 時間帯別予報の動的生成
          const hourlyContainer = document.getElementById('sheet-weather-hourly');
          if (hourlyContainer && Array.isArray(w.hourly) && w.hourly.length > 0) {
            hourlyContainer.innerHTML = w.hourly.map(h => `
              <div class="flex flex-col items-center justify-between p-2.5 rounded-2xl bg-[#2a2d36] min-w-[70px] shrink-0 border border-white/[0.03]">
                <span class="text-[11px] font-medium text-neutral-400 font-num">${h.time}</span>
                <span class="material-symbols-rounded text-2xl text-sky-400 my-1">${h.icon}</span>
                <span class="text-xs font-bold text-white font-num">${h.temp}℃</span>
                <span class="text-[10px] font-normal text-sky-300 font-num mt-0.5">${h.pop}%</span>
              </div>
            `).join('');
          }
        }
      } catch (err) {
        console.warn('[Weather Fetch Error]', err);
      }
    }

    async function fetchPresenceData() {
      try {
        const basePath = window.location.pathname.startsWith('/dashboard') ? '/dashboard' : '';
        const res = await fetch(basePath + '/api/presence');
        const data = await res.json();
        if (data.status === 'success' && data.presence) {
          const p = data.presence;
          const isHome = p.is_home;

          // 1. ダッシュボードの在宅タイル更新 (タイトル「在宅確認」、サブテキスト「在宅/不在」)
          const tileStatus = document.getElementById('tile-presence-status');
          const tileIconWrap = document.getElementById('tile-presence-icon-wrap');
          if (tileStatus) {
            tileStatus.textContent = isHome ? '在宅' : '不在';
          }
          if (tileIconWrap) {
            tileIconWrap.className = isHome
              ? "w-11 h-11 rounded-full bg-[#1b332b] text-emerald-400 flex items-center justify-center transition-all duration-300 group-hover:scale-105 shrink-0"
              : "w-11 h-11 rounded-full bg-[#272a31] text-neutral-400 flex items-center justify-center transition-all duration-300 group-hover:scale-105 shrink-0";
          }

          // 2. 在宅詳細モーダル更新 (大型アイコン円 ＆ 説明文なし)
          const sheetStatus = document.getElementById('sheet-presence-status');
          const sheetIconWrap = document.getElementById('sheet-presence-icon-wrap');
          const sheetDevice = document.getElementById('sheet-presence-device');
          const sheetIp = document.getElementById('sheet-presence-ip');
          const sheetMac = document.getElementById('sheet-presence-mac');
          const sheetTime = document.getElementById('sheet-presence-time');

          if (sheetStatus) sheetStatus.textContent = isHome ? '在宅' : '不在';
          if (sheetIconWrap) {
            sheetIconWrap.className = isHome
              ? "w-32 h-32 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-4 shadow-inner"
              : "w-32 h-32 rounded-full bg-white/[0.04] border border-white/[0.06] flex items-center justify-center text-neutral-400 mb-4 shadow-inner";
          }
          if (sheetDevice) sheetDevice.textContent = p.device_name || 'スマートフォン';
          if (sheetIp) sheetIp.textContent = p.ip || '192.168.0.30';
          if (sheetMac) sheetMac.textContent = p.mac || '72:58:BA:C7:40:FA';
          if (sheetTime) sheetTime.textContent = p.last_seen_str || '--:--:--';
        }
      } catch (err) {
        console.warn('[Presence Fetch Error]', err);
      }
    }

    async function fetchTileData() {
      try {
        const basePath = window.location.pathname.startsWith('/dashboard') ? '/dashboard' : '';
        const res = await fetch(basePath + '/api/tile');
        const data = await res.json();
        if (data.status === 'success' && data.tile) {
          const t = data.tile;
          const inHome = t.in_home;

          // 1. ダッシュボードの鍵タイル更新 (タイトル「鍵」、サブテキスト「検知/検知なし」)
          const tileStatus = document.getElementById('tile-key-status');
          const tileIconWrap = document.getElementById('tile-key-icon-wrap');
          const tileIcon = document.getElementById('tile-key-icon');

          if (tileStatus) {
            tileStatus.textContent = inHome ? '検知' : '検知なし';
            tileStatus.className = "text-xs text-neutral-400 font-normal mt-0.5 truncate transition-colors";
          }
          if (tileIconWrap) {
            tileIconWrap.className = inHome
              ? "w-11 h-11 rounded-full bg-[#3d2d1d] text-amber-400 flex items-center justify-center transition-all duration-300 group-hover:scale-105 shrink-0"
              : "w-11 h-11 rounded-full bg-[#272a31] text-neutral-400 flex items-center justify-center transition-all duration-300 group-hover:scale-105 shrink-0";
          }
          if (tileIcon) {
            tileIcon.textContent = inHome ? 'vpn_key_alert' : 'key';
          }

          // 2. 鍵詳細モーダル更新 (大型アイコン円 ＆ 説明文なし)
          const sheetStatus = document.getElementById('sheet-tile-status');
          const sheetIconWrap = document.getElementById('sheet-tile-icon-wrap');
          const sheetIcon = document.getElementById('sheet-tile-icon');
          const sheetDevice = document.getElementById('sheet-tile-device');
          const sheetRssi = document.getElementById('sheet-tile-rssi');
          const sheetMac = document.getElementById('sheet-tile-mac');
          const sheetTime = document.getElementById('sheet-tile-time');

          if (sheetStatus) sheetStatus.textContent = inHome ? '検知' : '検知なし';
          if (sheetIconWrap) {
            sheetIconWrap.className = inHome
              ? "w-32 h-32 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 mb-4 shadow-inner"
              : "w-32 h-32 rounded-full bg-white/[0.04] border border-white/[0.06] flex items-center justify-center text-neutral-400 mb-4 shadow-inner";
          }
          if (sheetIcon) {
            sheetIcon.textContent = inHome ? 'vpn_key_alert' : 'key';
          }
          if (sheetDevice) sheetDevice.textContent = t.device_name || 'Tile (Bluetooth)';
          if (sheetRssi) sheetRssi.textContent = `${t.rssi || '--'} dBm (${inHome ? '室内' : '室外'})`;
          if (sheetMac) sheetMac.textContent = t.mac || '30:F7:75:1F:0E:20';
          if (sheetTime) sheetTime.textContent = t.last_seen_str || '--:--:--';
        }
      } catch (err) {
        console.warn('[Tile Fetch Error]', err);
      }
    }

    /**
     * シーン直接実行 (ワンタップで即時スマート実行)
     */
    function runSceneDirectly(commandText, event) {
      if (event) event.stopPropagation();
      submitAssistantCommand(commandText);
    }

    /**
     * オートメーション直接テスト実行 (即時ローカル通知 ＋ バックエンド実行)
     */
    async function runAutomationDirectly(autoId, event) {
      if (event) event.stopPropagation();
      
      if (autoId === 'away_device_warning') {
        if ('serviceWorker' in navigator && 'Notification' in window) {
          if (Notification.permission === 'granted') {
            try {
              const reg = await navigator.serviceWorker.ready;
              reg.showNotification('お出かけですか？', {
                body: 'リビング照明・エアコン（冷房）が稼働したままです。消灯しますか？',
                tag: 'away-device-warning',
                renotify: true,
                requireInteraction: true,
                actions: [
                  { action: 'run_leaving', title: '🚪 いってきます（全消灯）' },
                  { action: 'dismiss', title: 'そのまま' }
                ],
                data: { url: window.location.pathname, scene: 'leaving' }
              });
            } catch (ne) {
              console.warn('[Local Notification Error]', ne);
            }
          }
        }
      }

      const cmdMap = {
        'weekday_morning_light': 'リビングの電気をつけて',
        'away_device_warning': '消し忘れ通知テスト'
      };
      submitAssistantCommand(cmdMap[autoId] || 'オートメーションを実行');
    }

    /**
     * オートメーションの有効/無効トグル切り替え
     */
    async function toggleAutomation(autoId, isChecked) {
      try {
        const basePath = window.location.pathname.startsWith('/dashboard') ? '/dashboard' : '';
        const res = await fetch(`${basePath}/api/automations/toggle`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: autoId })
        });
        const data = await res.json();
        if (data.status === 'success') {
          showAssistantToast(`オートメーションを${isChecked ? '有効' : '無効'}にしました`, isChecked ? 'toggle_on' : 'toggle_off', false);
        }
      } catch (err) {
        console.error('[Toggle Automation Error]', err);
      }
    }

    window.addEventListener('DOMContentLoaded', () => {
      renderAcGauge();
      updateAcUi();
      renderHeaterGauge();
      updateHeaterUi();
      updateLightUi();
      updateCleanerUi();
      loadInitialState();
      fetchWeatherData();
      fetchPresenceData();
      fetchTileData();

      // クリーナーの定期状態同期 (10秒ごと)
      setInterval(syncCleanerStatus, 10000);
      // 在宅センサーの定期同期 (2秒ごと・リアルタイム帰宅/外出反映)
      setInterval(fetchPresenceData, 2000);
      // 鍵（Tile）センサーの定期同期 (5秒ごと)
      setInterval(fetchTileData, 5000);
      // 天気・気象データの定期同期 (10分ごと)
      setInterval(fetchWeatherData, 600000);

      // コマンド入力バーの Enter キー送信
      const cmdInput = document.getElementById('command-search-input');
      if (cmdInput) {
        cmdInput.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' && !e.isComposing) {
            e.preventDefault();
            submitAssistantCommand(cmdInput.value);
          }
        });
      }

      // 時間別予報の横ホイールスクロール連動
      const hourlyBox = document.getElementById('sheet-weather-hourly');
      if (hourlyBox) {
        hourlyBox.addEventListener('wheel', (e) => {
          if (e.deltaY !== 0) {
            e.preventDefault();
            hourlyBox.scrollLeft += e.deltaY;
          }
        }, { passive: false });
      }

      // 音声認識中にNovaのバー以外をタップ/クリックしたら録音を即座に終了する
      document.addEventListener('pointerdown', (e) => {
        if (isRecording) {
          const cmdBar = document.getElementById('command-bar-container');
          if (cmdBar && !cmdBar.contains(e.target)) {
            if (recognition) {
              try { recognition.abort(); } catch (err) {}
            }
            stopVoiceRecognition();
            showAssistantToast('音声入力をキャンセルしました。', 'mic_off', false);
          }
        }
      });
      // PWA Service Worker 登録 (スコープを /dashboard/ に明示指定) ＆ WebPush 購読
      if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
          const basePath = window.location.pathname.startsWith('/dashboard') ? '/dashboard' : '';
          const swUrl = (basePath || '') + '/sw.js';
          const scopeUrl = (basePath || '') + '/';
          
          // ローカルアクセス時はマニフェストパスを調整
          const manifestEl = document.getElementById('pwa-manifest');
          if (manifestEl && !basePath) {
            manifestEl.setAttribute('href', '/manifest.json');
          }

          navigator.serviceWorker.register(swUrl, { scope: scopeUrl })
            .then(async (reg) => {
              console.log('[PWA] Service Worker registered for scope:', reg.scope);
              
              // WebPush 通知サブスクリプションの自動初期化
              if ('PushManager' in window && 'Notification' in window) {
                try {
                  const initPush = async () => {
                    if (Notification.permission === 'default') {
                      const perm = await Notification.requestPermission();
                      if (perm === 'granted') {
                        await subscribePush(reg, basePath);
                      }
                    } else if (Notification.permission === 'granted') {
                      await subscribePush(reg, basePath);
                    }
                  };

                  if (Notification.permission === 'granted') {
                    initPush();
                  } else {
                    document.addEventListener('click', initPush, { once: true });
                  }
                } catch (pe) {
                  console.warn('[PWA Push Error]', pe);
                }
              }
            })
            .catch((err) => {
              console.warn('[PWA] Service Worker registration failed:', err);
            });
        });
      }

      // WebPush 購読ヘルパー
      async function subscribePush(registration, basePath) {
        try {
          const res = await fetch((basePath || '') + '/api/push/vapid-key');
          const data = await res.json();
          if (!data || !data.public_key) return;

          const padding = '='.repeat((4 - data.public_key.length % 4) % 4);
          const base64 = (data.public_key + padding).replace(/\-/g, '+').replace(/_/g, '/');
          const rawData = window.atob(base64);
          const appServerKey = new Uint8Array(rawData.length);
          for (let i = 0; i < rawData.length; ++i) {
            appServerKey[i] = rawData.charCodeAt(i);
          }

          let sub = await registration.pushManager.getSubscription();
          if (!sub) {
            sub = await registration.pushManager.subscribe({
              userVisibleOnly: true,
              applicationServerKey: appServerKey
            });
          }

          if (sub) {
            await fetch((basePath || '') + '/api/push/subscribe', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(sub)
            });
            console.log('[PWA Push] Registered with server successfully:', sub.endpoint);
          }
        } catch (e) {
          console.warn('[PWA Subscribe Error]', e);
        }
      }

      // Android アシスタントブリッジ連携: URLに ?assist=1 または ?voice=1 が付いている場合は即座に音声起動
      const urlParams = new URLSearchParams(window.location.search);
      if (urlParams.has('assist') || urlParams.has('voice')) {
        setTimeout(() => {
          if (!isRecording) {
            toggleVoiceRecognition();
          }
        }, 300);
      }
    });
