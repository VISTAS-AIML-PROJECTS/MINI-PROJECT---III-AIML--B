/* Offline support: real-recording phrases (emergency + common) play from a
   service-worker cache, so they keep working with no network. */
(function () {
  const badge = document.createElement('div');
  badge.textContent = '\u{1F4F4} Offline \u2014 emergency & common phrases still work';
  badge.style.cssText = 'display:none;position:fixed;top:10px;left:50%;transform:translateX(-50%);z-index:90;padding:5px 12px;border-radius:20px;background:#2a1f0f;border:1px solid #4a3418;color:#ffb84d;font-size:11px;font-weight:700;white-space:nowrap';
  document.body.appendChild(badge);
  const refreshBadge = () => { badge.style.display = navigator.onLine ? 'none' : 'block'; };
  window.addEventListener('online', refreshBadge);
  window.addEventListener('offline', refreshBadge);
  refreshBadge();

  const isRecording = (id) => /^(\d|C\d)/.test(id);

  function audioUrl(id) {
    let u = '/quick_phrase_audio/' + id + '?voice=' + currentVoice + '&language=' + currentLang;
    if (currentLang === 'ta') u += '&register=' + currentRegister;
    return u;
  }

  // Direct playback bypasses /speak, so tell the server about the press
  // (keeps the caregiver feed and emergency alerts working).
  function logPress(text) {
    const fd = new FormData();
    fd.append('text', text);
    fd.append('voice', currentVoice);
    fd.append('language', currentLang);
    if (currentLang === 'ta') fd.append('register', currentRegister);
    fetch('/activity/log', { method: 'POST', body: fd }).catch(() => {});
  }

  async function play(p, btn) {
    logPress(p.text);
    try {
      const res = await fetch(audioUrl(p.id));
      if (!res.ok || !(res.headers.get('content-type') || '').includes('audio')) throw new Error('bad response');
      player.src = URL.createObjectURL(await res.blob());
      player.style.display = 'block';
      player.play();
      status.textContent = navigator.onLine ? 'Done.' : 'Played from offline cache.';
    } catch (err) {
      status.textContent = navigator.onLine ? 'Could not play that phrase.' : 'Not cached yet \u2014 open it once while online.';
    }
    btn.disabled = false;
  }

  const original = renderPhraseGrid;
  renderPhraseGrid = function (containerId, phrases, btnClass) {
    original(containerId, phrases, btnClass);
    const buttons = document.getElementById(containerId).querySelectorAll('.phrase-btn');
    phrases.forEach((p, i) => {
      const btn = buttons[i];
      if (!btn || !isRecording(p.id)) return;
      btn.onclick = () => { btn.disabled = true; status.textContent = 'Playing...'; play(p, btn); };
      fetch(audioUrl(p.id)).catch(() => {});   // warms the service-worker cache
    });
  };

  loadPhrases();   // re-render once so the first paint also uses the wrapper
})();
