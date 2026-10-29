/* Accessibility: two-level switch scanning + experimental webcam eye tracking. */
(function () {
  const $ = (id) => document.getElementById(id);
  const panel = $('a11y-panel');
  $('a11y-toggle').onclick = () => { panel.style.display = panel.style.display === 'block' ? 'none' : 'block'; };

  /* ---- Switch scanning: groups first, then items inside the chosen group ---- */
  const scanEnable = $('scan-enable'), speedRow = $('scan-speed-row');
  const speed = $('scan-speed'), speedVal = $('scan-speed-val'), selectBtn = $('switch-select-btn');
  let level = 'group', gIdx = -1, iIdx = -1, gEl = null, items = [], timer = null;

  const vis = (el) => el && el.offsetParent !== null;
  const groups = () => [
    $('voice-toggle'), $('lang-toggle'), $('register-toggle'),
    $('emergency-phrases').closest('.section'),
    $('common-phrases').closest('.section'),
    $('text-input').closest('.section'),
  ].filter(vis);
  const itemsOf = (g) => Array.from(g.querySelectorAll('button:not([disabled])')).filter(vis);
  const clear = () => document.querySelectorAll('.scan-group, .scan-highlight')
    .forEach((e) => e.classList.remove('scan-group', 'scan-highlight'));
  const reset = () => { level = 'group'; gIdx = -1; iIdx = -1; gEl = null; clear(); };

  function step() {
    clear();
    if (level === 'group') {
      const gs = groups();
      if (!gs.length) return;
      gIdx = (gIdx + 1) % gs.length;
      gEl = gs[gIdx];
      gEl.classList.add('scan-group');
      gEl.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    } else {
      items = itemsOf(gEl);
      iIdx++;
      if (iIdx >= items.length) { level = 'group'; iIdx = -1; return step(); }  // full pass, no pick: back out
      items[iIdx].classList.add('scan-highlight');
      items[iIdx].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }

  function select() {
    if (level === 'group') {
      if (!gEl) return;
      level = 'item'; iIdx = -1; step();
    } else {
      const el = items[iIdx];
      reset();
      if (el) el.click();
    }
  }

  const save = () => { try { localStorage.setItem('eg_scan', JSON.stringify({ on: scanEnable.checked, speed: speed.value })); } catch (e) {} };
  const stop = () => { if (timer) clearInterval(timer); timer = null; reset(); selectBtn.style.display = 'none'; };
  const start = () => { stop(); timer = setInterval(step, parseFloat(speed.value) * 1000); selectBtn.style.display = 'block'; };

  scanEnable.onchange = () => {
    speedRow.style.display = scanEnable.checked ? 'flex' : 'none';
    if (scanEnable.checked) start(); else stop();
    save();
  };
  speed.oninput = () => { speedVal.textContent = speed.value + 's'; if (scanEnable.checked) start(); save(); };
  selectBtn.onclick = select;
  document.addEventListener('keydown', (e) => {
    if (!scanEnable.checked || !['Space', 'Enter'].includes(e.code)) return;
    if (document.activeElement && document.activeElement.matches('textarea, input[type=text]')) return;
    e.preventDefault();
    select();
  });
  try {   // scanning stays on after a reload, so a switch user isn't locked out
    const s = JSON.parse(localStorage.getItem('eg_scan') || '{}');
    if (s.speed) { speed.value = s.speed; speedVal.textContent = s.speed + 's'; }
    if (s.on) { scanEnable.checked = true; speedRow.style.display = 'flex'; start(); }
  } catch (e) {}

  /* ---- Eye tracking (experimental): WebGazer + dwell-to-click ---- */
  const gazeEnable = $('gaze-enable'), calibBtn = $('gaze-calibrate-btn');
  const gazeDot = $('gaze-dot'), dwellRing = $('dwell-ring');
  const DWELL_MS = 1500, COOLDOWN_MS = 2500;
  let gazeLoaded = false, dwellTarget = null, dwellStart = 0, cooldownUntil = 0;

  function loadGazeLib(cb) {
    if (gazeLoaded) return cb();
    const s = document.createElement('script');
    s.src = 'https://webgazer.cs.brown.edu/webgazer.js';
    s.onload = () => { gazeLoaded = true; cb(); };
    s.onerror = () => {
      status.textContent = 'Could not load the eye-tracking library (needs internet).';
      gazeEnable.checked = false; calibBtn.style.display = 'none';
    };
    document.head.appendChild(s);
  }

  function onGaze(data) {
    if (!data) return;
    gazeDot.style.display = 'block';
    gazeDot.style.left = data.x + 'px';
    gazeDot.style.top = data.y + 'px';
    const el = document.elementFromPoint(data.x, data.y);
    const target = el && el.closest('.toggle-btn, .phrase-btn, .emotion-chip, .speak-btn');
    if (!target || Date.now() < cooldownUntil) { dwellTarget = null; dwellRing.style.display = 'none'; return; }
    if (target !== dwellTarget) { dwellTarget = target; dwellStart = Date.now(); }
    const progress = Math.min((Date.now() - dwellStart) / DWELL_MS, 1);
    dwellRing.style.display = 'block';
    dwellRing.style.left = data.x + 'px';
    dwellRing.style.top = data.y + 'px';
    dwellRing.style.transform = 'translate(-50%,-50%) scale(' + (0.4 + 0.6 * progress) + ')';
    if (progress >= 1) {
      target.click();
      dwellTarget = null; cooldownUntil = Date.now() + COOLDOWN_MS; dwellRing.style.display = 'none';
    }
  }

  gazeEnable.onchange = () => {
    calibBtn.style.display = gazeEnable.checked ? 'block' : 'none';
    if (gazeEnable.checked) {
      loadGazeLib(() => {
        if (webgazer.showPredictionPoints) webgazer.showPredictionPoints(false);
        webgazer.setGazeListener(onGaze).begin();
      });
    } else {
      if (gazeLoaded && window.webgazer) webgazer.end();
      document.querySelectorAll('[id^="webgazer"]').forEach((el) => el.remove());
      gazeDot.style.display = 'none'; dwellRing.style.display = 'none';
    }
  };

  calibBtn.onclick = () => {
    const pts = [[8,8],[50,8],[92,8],[8,50],[50,50],[92,50],[8,92],[50,92],[92,92]];
    let i = 0;
    const next = () => {
      document.querySelectorAll('.calib-dot').forEach((d) => d.remove());
      if (i >= pts.length) { status.textContent = 'Calibration done.'; return; }
      const d = document.createElement('div');
      d.className = 'calib-dot';
      d.style.left = pts[i][0] + 'vw';
      d.style.top = pts[i][1] + 'vh';
      let n = 0;
      d.onclick = () => { if (++n >= 3) { i++; next(); } };
      document.body.appendChild(d);
    };
    status.textContent = 'Look at each dot and click it 3 times.';
    panel.style.display = 'none';
    next();
  };
})();
