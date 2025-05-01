/* Multi-attempt controller with recurring hint + clearer result text */

const layer     = document.getElementById('verify-layer');
const statusTxt = document.getElementById('status-text');
const idleVid   = document.getElementById('idle-loop');
const welcome   = document.getElementById('welcome-video');
const hint      = document.getElementById('hint');

/* ── global key listener ─────────────────────────────────── */
document.addEventListener('keydown', () => {
  if (!layer.classList.contains('active')) verifyOnce();
});

async function verifyOnce () {
  /* 1 ▸ hide hint & mark busy */
  hint.classList.add('hidden');
  layer.classList.add('active');
  layer.classList.remove('hidden');

  setUI('Verifying…', 'verifying');

  /* 2 ▸ ask back-end */
  let res;
  try {
    res = await fetch('/recognize', { method: 'POST' }).then(r => r.json());
  } catch {
    res = { status: 'error' };
  }

  /* 3 ▸ handle outcome */
  if (res.status === 'granted') {
    setUI(`Welcome ${res.name}!`, 'granted');
    setTimeout(() => playWelcome(res.video), 1200);
  } else if (res.status === 'denied') {
    setUI('Access&nbsp;Denied&nbsp;– Please&nbsp;try&nbsp;again', 'denied');
    setTimeout(endCycle, 3000);
  } else {
    setUI('Camera Error', 'denied');
    setTimeout(endCycle, 3000);
  }
}

/* ---------- helpers ---------- */
function setUI (html, state) {
  statusTxt.innerHTML = html;          // allow &nbsp; in denied text
  layer.className = '';                // clear
  layer.classList.add(state, 'active');
}

function endCycle () {
  layer.classList.add('hidden');
  layer.classList.remove('active');
  hint.classList.remove('hidden');     // hint ready for next user
}

function playWelcome (src) {
  endCycle();                          // close overlay first
  idleVid.classList.add('hidden');

  welcome.src          = src;
  welcome.muted        = false;
  welcome.currentTime  = 0;
  welcome.classList.remove('hidden');
  welcome.play().catch(() => {});

  welcome.onended = () => {
    welcome.classList.add('hidden');
    idleVid.classList.remove('hidden');
    hint.classList.remove('hidden');   // hint back after video
  };
}
