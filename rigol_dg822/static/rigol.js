/* xsphere-daq — Rigol DG822 control page.
 *
 * Parity target is the tkinter GUI (dg822_gui.py): a connection strip, two
 * channel cards, the arbitrary-waveform generator, quick presets. Everything
 * the page knows comes from GET /api/state, polled once a second; every write
 * goes back through the matching /api endpoint and the echoed channel document
 * is adopted, so a second browser — or somebody at the instrument's front
 * panel — converges with this page instead of fighting it.
 *
 * Four rules the rest of the file keeps to:
 *  - the API base is derived from window.location and never hardcoded, so the
 *    same files serve standalone and mounted at /rigol by xsphere_daq.panel;
 *  - a poll NEVER overwrites a field the operator is editing (see watch/fill) —
 *    the cure for a page that eats a half-typed frequency once a second;
 *  - nothing is fetched from another host. The preview is drawn with the Canvas
 *    2D API from /api/ch/{n}/preview samples: no charting library, no images,
 *    no fonts. The rig has no internet;
 *  - failures degrade. A missing instrument, a missing VISA backend or a SCPI
 *    timeout leaves the controls disabled and the reason on screen, never a
 *    blank pane and never an exception in the console.
 *
 * Deliberately absent: a global resetStream(). The shell calls that on every
 * pane switch to suspend and re-arm live media (xsphere_daq/static/shell.js);
 * this page has none, and defining it would hand the shell a no-op to poke.
 */
"use strict";

// API base = wherever this page is mounted (works standalone and under /rigol/).
const BASE = location.pathname.replace(/\/+$/, "");
const API = BASE + "/api";
const $ = id => document.getElementById(id);

const POLL_MS = 1000;          // what the operator is watching change
const PREVIEW_MS = 220;        // debounce: coalesce a burst of keystrokes
const CONFIRM_MS = 3000;       // window for the second click on a destructive button

const FREQ_UNITS = { "Hz": 1, "kHz": 1e3, "MHz": 1e6 };
const PW_UNITS = { "ns": 1e-9, "µs": 1e-6, "ms": 1e-3, "s": 1 };
const DUR_UNITS = { "s": 1, "min": 60, "hour": 3600 };
const ARB_TIME_UNITS = { "µs": 1e-6, "ms": 1e-3, "s": 1 };

const WAVEFORMS = [
  ["sine", "Sine"], ["square", "Square"], ["pulse", "Pulse"], ["ramp", "Ramp"],
  ["noise", "Noise"], ["dc", "DC"], ["arbitrary", "Arbitrary"],
];

// Auto time defaults, as fractions of the shape period, for shapes whose
// /api/arb/shapes descriptor leaves `default` null. The tkinter dialog derives
// them from the period so the shape is sane the moment it is picked; a null
// default is the server asking for the same courtesy.
const AUTO_FRACTIONS = {
  square: [0.5], ramp: [1.0], trapezoid: [0.2, 0.6, 0.2],
  pulse: [0.1, 0.05, 0.05], exponential: [0.2], gaussian: [0.3],
};

// ------------------------------------------------------------------ utils --
async function getJSON(path) {
  let r;
  try { r = await fetch(API + path, { headers: { "Accept": "application/json" } }); }
  catch (e) { return { ok: false, status: 0, j: { detail: "service unreachable" } }; }
  let j = {};
  try { j = await r.json(); } catch (e) { }
  return { ok: r.ok, status: r.status, j: j || {} };
}

async function post(path, body) {
  let r;
  const init = { method: "POST" };
  if (body !== undefined) {
    init.headers = { "Content-Type": "application/json" };
    init.body = JSON.stringify(body);
  }
  try { r = await fetch(API + path, init); }
  catch (e) { return { ok: false, status: 0, j: { detail: "service unreachable" } }; }
  let j = {};
  try { j = await r.json(); } catch (e) { }
  return { ok: r.ok, status: r.status, j: j || {} };
}

// The server side of this is the dock's convention: FastAPI HTTPException
// serialises to {"detail": ...}. Anything else renders as "error <status>"
// rather than the word undefined.
function errOf(r) {
  if (r.j && r.j.detail) return String(r.j.detail);
  return r.status ? "error " + r.status : "no reply from the service";
}

function toast(msg) {
  const t = $("toast");
  t.textContent = msg;
  t.style.display = "block";
  clearTimeout(t._h);
  t._h = setTimeout(() => { t.style.display = "none"; }, 3500);
}
function stat(msg) { $("stat").textContent = msg; }

function line(el, msg, isErr) {
  el.textContent = msg || "";
  el.classList.toggle("err", !!isErr);
}
function connLine(msg, isErr, holdMs) {
  line($("conn-stat"), msg, isErr);
  connHold = Date.now() + (holdMs === undefined ? 4000 : holdMs);
}

// %.6g, minus the trailing zeros JS leaves behind.
function sig(v, d) {
  if (v == null || !isFinite(v)) return "—";
  if (v === 0) return "0";
  let s = Number(v).toPrecision(d || 6);
  if (s.indexOf("e") < 0 && s.indexOf(".") >= 0) s = s.replace(/0+$/, "").replace(/\.$/, "");
  return s;
}
function fmtFreq(hz) {
  if (hz == null || !isFinite(hz)) return "—";
  const a = Math.abs(hz);
  if (a >= 1e6) return sig(hz / 1e6) + " MHz";
  if (a >= 1e3) return sig(hz / 1e3) + " kHz";
  return sig(hz) + " Hz";
}
function fmtTime(s) {
  if (s == null || !isFinite(s)) return "—";
  const a = Math.abs(s);
  if (a >= 1) return s.toFixed(3) + " s";
  if (a >= 1e-3) return (s * 1e3).toFixed(3) + " ms";
  if (a >= 1e-6) return (s * 1e6).toFixed(3) + " µs";
  return (s * 1e9).toFixed(3) + " ns";
}
function fmtDur(s) {
  s = Math.max(0, Math.round(s));
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), ss = s % 60;
  const p = [];
  if (h) p.push(h + "h");
  if (h || m) p.push(m + "m");
  p.push(ss + "s");
  return p.join(" ");
}
function fmtRate(sa) {
  if (sa == null || !isFinite(sa)) return "—";
  if (sa >= 1e6) return sig(sa / 1e6, 4) + " MSa/s";
  if (sa >= 1e3) return sig(sa / 1e3, 4) + " kSa/s";
  return sig(sa, 4) + " Sa/s";
}

// Pick the unit that puts the magnitude in a readable range, so a pulse width
// reads "100 µs" and not "0.0001 s".
function bestUnit(seconds, units) {
  const names = Object.keys(units);
  let best = names[names.length - 1];
  for (const n of names) {
    const v = Math.abs(seconds) / units[n];
    if (v >= 1 && v < 1000) return n;
  }
  // Nothing landed in [1, 1000): use the largest unit that keeps it >= 1.
  for (const n of names) if (Math.abs(seconds) / units[n] >= 1) best = n;
  return best;
}

/* The tkinter GUI accepts an arithmetic expression in the frequency box
   ("1/0.1" -> 10 Hz) by handing it to eval(). A browser page must not do that
   with anything an operator types, so this is a four-operator recursive-descent
   parser over numbers, + - * / and parentheses. It also differs from the GUI on
   purpose: a parse failure is reported, where the GUI silently substitutes
   1000 Hz — a quirk that has no business driving a signal generator. */
function parseExpr(src) {
  const s = String(src == null ? "" : src);
  let i = 0;
  const skip = () => { while (i < s.length && /\s/.test(s[i])) i++; };

  function primary() {
    skip();
    if (s[i] === "(") {
      i++;
      const v = expr();
      skip();
      if (s[i] !== ")") throw new Error("missing )");
      i++;
      return v;
    }
    if (s[i] === "+") { i++; return primary(); }
    if (s[i] === "-") { i++; return -primary(); }
    const m = /^(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?/.exec(s.slice(i));
    if (!m) throw new Error(s[i] ? "unexpected '" + s[i] + "'" : "expected a number");
    i += m[0].length;
    return parseFloat(m[0]);
  }
  function term() {
    let v = primary();
    for (; ;) {
      skip();
      if (s[i] === "*") { i++; v *= primary(); }
      else if (s[i] === "/") { i++; v /= primary(); }
      else return v;
    }
  }
  function expr() {
    let v = term();
    for (; ;) {
      skip();
      if (s[i] === "+") { i++; v += term(); }
      else if (s[i] === "-") { i++; v -= term(); }
      else return v;
    }
  }
  if (!s.trim()) throw new Error("empty");
  const v = expr();
  skip();
  if (i !== s.length) throw new Error("unexpected '" + s[i] + "'");
  if (!isFinite(v)) throw new Error("not a finite number");
  return v;
}

function need(el, label) {
  const v = parseFloat(el.value);
  if (!isFinite(v)) throw new Error(label + ": \"" + el.value + "\" is not a number");
  return v;
}

// The instrument answers :FUNCtion? with SCPI short forms (SIN, SQU, PULS,
// USER, SEQ); the API may normalise or may pass them through. Accept both.
function normWave(f) {
  const s = String(f == null ? "" : f).trim().toUpperCase();
  if (!s) return "";
  if (s.indexOf("SIN") === 0) return "sine";
  if (s.indexOf("SQU") === 0) return "square";
  if (s.indexOf("PULS") === 0) return "pulse";
  if (s.indexOf("RAMP") === 0) return "ramp";
  if (s.indexOf("NOIS") === 0) return "noise";
  if (s.indexOf("DC") === 0) return "dc";
  if (s.indexOf("ARB") === 0 || s.indexOf("USER") === 0 || s.indexOf("SEQ") === 0) {
    return "arbitrary";
  }
  return s.toLowerCase();
}
function isHighZ(imp) {
  if (imp == null) return true;
  if (typeof imp === "number") return imp >= 1e5;
  return /high|inf/i.test(String(imp));
}
function truthy(v) {
  if (typeof v === "string") return /^(1|on|true|yes|inv|inverted)$/i.test(v.trim());
  return !!v;
}
function normRunMode(m) {
  const s = String(m == null ? "" : m).toLowerCase();
  if (/cyc|burst/.test(s)) return "cycles";
  if (/tim|dur|sec/.test(s)) return "timed";
  return "continuous";
}

// --------------------------------------------- fields the operator owns ----
/* Two guards, both from the dock: a field being edited is never written by a
   poll, and a field the operator has changed but not yet applied stays changed
   until it is applied or explicitly reverted. Without the second one, a value
   typed and left for a second is silently undone by the next /api/state. */
function watch(el) {
  const mark = () => { el.dataset.dirty = "1"; };
  el.addEventListener("input", mark);
  el.addEventListener("change", mark);
}
function clean(el) { delete el.dataset.dirty; }
function fill(el, v) {
  if (!el) return;
  if (el === document.activeElement || el.dataset.dirty) return;
  const s = (v === null || v === undefined) ? "" : String(v);
  if (el.value !== s) el.value = s;
}
function fillCheck(el, on) {
  if (!el || el === document.activeElement || el.dataset.dirty) return;
  el.checked = !!on;
}
function radioValue(name) {
  const el = document.querySelector('input[name="' + name + '"]:checked');
  return el ? el.value : null;
}
function setRadio(name, value) {
  const el = document.querySelector('input[name="' + name + '"][value="' + value + '"]');
  if (el && document.activeElement !== el) el.checked = true;
}
function enableAll(root, on, skip) {
  for (const el of root.querySelectorAll("input, select, button, textarea")) {
    if (skip && skip(el)) continue;
    el.disabled = !on;
  }
}

/* A destructive control asks twice rather than opening a dialog: window.confirm
   traps focus inside the iframe the panel frames this page in, and the operator
   then cannot get back to the rail. Second click within CONFIRM_MS commits. */
function armConfirm(btn, label, run) {
  btn.dataset.armed = "";
  btn.onclick = () => {
    if (btn.dataset.armed) {
      clearTimeout(btn._h);
      btn.dataset.armed = "";
      btn.textContent = label;
      run();
      return;
    }
    btn.dataset.armed = "1";
    btn.textContent = "click again to " + label;
    btn._h = setTimeout(() => {
      btn.dataset.armed = "";
      btn.textContent = label;
    }, CONFIRM_MS);
  };
}

// ------------------------------------------------------------ the plot -----
/* Canvas 2D, auto-scaled on both axes, unit-aware labels. Everything is in CSS
   pixels scaled by devicePixelRatio, or the trace is a blurred two-pixel smear
   on the rig's HiDPI screen. */
function plotSize(cv) {
  const dpr = window.devicePixelRatio || 1;
  const w = Math.max(160, Math.round(cv.clientWidth || 320));
  const h = Math.max(90, Math.round(cv.clientHeight || 172));
  if (cv.width !== Math.round(w * dpr) || cv.height !== Math.round(h * dpr)) {
    cv.width = Math.round(w * dpr);
    cv.height = Math.round(h * dpr);
  }
  const g = cv.getContext("2d");
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  g.clearRect(0, 0, w, h);
  g.fillStyle = "#0e0e0e";
  g.fillRect(0, 0, w, h);
  return { g, w, h };
}

function plotEmpty(cv, msg, isErr) {
  const { g, w, h } = plotSize(cv);
  g.fillStyle = isErr ? "#c77" : "#555";
  g.font = "12px system-ui, sans-serif";
  g.textAlign = "center";
  g.textBaseline = "middle";
  const words = String(msg || "").split(" ");
  const lines = [];
  let cur = "";
  for (const word of words) {
    const t = cur ? cur + " " + word : word;
    if (g.measureText(t).width > w - 24 && cur) { lines.push(cur); cur = word; }
    else cur = t;
  }
  if (cur) lines.push(cur);
  const y0 = h / 2 - (lines.length - 1) * 8;
  lines.forEach((t, k) => g.fillText(t, w / 2, y0 + k * 16));
}

function plot(cv, o) {
  const t = o.t || [], v = o.v || [];
  if (t.length < 2 || v.length < 2) { plotEmpty(cv, o.empty || "no samples"); return; }
  const { g, w, h } = plotSize(cv);
  const L = 52, R = 10, T = 18, B = 24;
  const pw = Math.max(10, w - L - R), ph = Math.max(10, h - T - B);

  let t0 = t[0], t1 = t[0], v0 = v[0], v1 = v[0];
  for (let i = 1; i < t.length; i++) { if (t[i] < t0) t0 = t[i]; if (t[i] > t1) t1 = t[i]; }
  for (let i = 1; i < v.length; i++) { if (v[i] < v0) v0 = v[i]; if (v[i] > v1) v1 = v[i]; }
  if (!(t1 > t0)) t1 = t0 + 1;
  // A DC level is a flat line: the GUI opens the window to +/-1 V so the trace
  // is not pinned to an axis with no idea of the scale. Same here.
  const span = v1 - v0;
  if (span < 1e-9) { v0 -= 1; v1 += 1; }
  else { v0 -= span * 0.1; v1 += span * 0.1; }

  const X = x => L + (x - t0) / (t1 - t0) * pw;
  const Y = y => T + ph - (y - v0) / (v1 - v0) * ph;

  g.strokeStyle = "#242424";
  g.lineWidth = 1;
  g.fillStyle = "#888";
  g.font = "10px ui-monospace, Consolas, monospace";
  g.textBaseline = "middle";
  for (let k = 0; k <= 4; k++) {
    const y = T + ph * k / 4;
    g.beginPath(); g.moveTo(L, y + 0.5); g.lineTo(L + pw, y + 0.5); g.stroke();
    g.textAlign = "right";
    g.fillText(sig(v1 - (v1 - v0) * k / 4, 3), L - 6, y);
  }
  g.textAlign = "center";
  g.textBaseline = "top";
  for (let k = 0; k <= 4; k++) {
    const x = L + pw * k / 4;
    g.beginPath(); g.moveTo(x + 0.5, T); g.lineTo(x + 0.5, T + ph); g.stroke();
    g.fillText(sig(t0 + (t1 - t0) * k / 4, 3), x, T + ph + 5);
  }
  // Zero line, when it is inside the window — the reference the offset moves.
  if (v0 < 0 && v1 > 0) {
    g.strokeStyle = "#3a3a3a";
    g.beginPath(); g.moveTo(L, Y(0) + 0.5); g.lineTo(L + pw, Y(0) + 0.5); g.stroke();
  }
  g.strokeStyle = "#555";
  g.strokeRect(L + 0.5, T + 0.5, pw, ph);

  g.strokeStyle = o.color || "#7cf";
  g.lineWidth = 1.5;
  g.lineJoin = "round";
  g.beginPath();
  const n = Math.min(t.length, v.length);
  for (let i = 0; i < n; i++) {
    const x = X(t[i]), y = Y(v[i]);
    if (i === 0) g.moveTo(x, y); else g.lineTo(x, y);
  }
  g.stroke();

  g.fillStyle = "#9ab";
  g.font = "11px system-ui, sans-serif";
  g.textAlign = "left";
  g.textBaseline = "top";
  g.fillText(o.title || "", L, 3);
  g.fillStyle = "#777";
  g.font = "10px system-ui, sans-serif";
  g.textAlign = "right";
  g.fillText(o.xLabel || "", w - R, 3);
  g.save();
  g.translate(11, T + ph / 2);
  g.rotate(-Math.PI / 2);
  g.textAlign = "center";
  g.textBaseline = "middle";
  g.fillText(o.yLabel || "V", 0, 0);
  g.restore();
}

// ------------------------------------------------------------- app state ---
let S = null;                  // last /api/state
let connected = false;
let pollFails = 0;
// The poll rewrites the connection line every second, which would eat "found 2
// instruments" before it could be read. Anything the operator asked for holds
// the line for a few seconds first (the dock's errUntil, same 4 s).
let connHold = 0;
let stateSeq = 0;              // bumped on every adoption; guards in-flight writes
const CH = {};                 // n -> channel controller

// ------------------------------------------------------------- channels ----
function chanHTML(n) {
  const opts = WAVEFORMS.map(w => '<option value="' + w[0] + '">' + w[1] + '</option>').join("");
  const funits = Object.keys(FREQ_UNITS)
    .map(u => '<option value="' + u + '">' + u + '</option>').join("");
  const punits = Object.keys(PW_UNITS)
    .map(u => '<option value="' + u + '">' + u + '</option>').join("");
  const dunits = Object.keys(DUR_UNITS)
    .map(u => '<option value="' + u + '">' + u + '</option>').join("");
  return '' +
    '<div class="card chan" id="ch' + n + '-card">' +
    '<h3><span class="dot off" id="ch' + n + '-dot"></span> CH' + n +
      '<span class="recpill" id="ch' + n + '-onpill" hidden>' +
        '<span class="reclabel">output on</span></span>' +
      '<span class="spacer"></span>' +
      '<span class="val" id="ch' + n + '-head"></span></h3>' +

    '<canvas class="preview" id="ch' + n + '-cv" role="img" ' +
      'aria-label="CH' + n + ' waveform preview"></canvas>' +
    '<div class="warnbox limitwarn" id="ch' + n + '-limwarn" hidden></div>' +
    '<div class="warnbox" id="ch' + n + '-pvwarn" hidden></div>' +

    '<div class="row">' +
      '<label class="fixed" for="ch' + n + '-wave">Waveform</label>' +
      '<select id="ch' + n + '-wave">' + opts + '</select>' +
      '<span class="spacer"></span>' +
      '<button class="ghost tiny" id="ch' + n + '-revert" ' +
        'title="discard unapplied edits and show what the instrument reports">revert</button>' +
    '</div>' +

    '<div class="row" id="ch' + n + '-freqrow">' +
      '<label class="fixed" for="ch' + n + '-freq">Frequency</label>' +
      '<input type="text" id="ch' + n + '-freq" class="num" autocomplete="off" ' +
        'spellcheck="false" value="1000">' +
      '<select id="ch' + n + '-frequnit" aria-label="CH' + n + ' frequency unit">' +
        funits + '</select>' +
      '<span class="val" id="ch' + n + '-freqhz"></span>' +
    '</div>' +
    '<div class="hint" id="ch' + n + '-freqhint">expressions accepted: 1/0.1 = 10</div>' +

    '<div class="row">' +
      '<label class="fixed" for="ch' + n + '-amp">Amplitude</label>' +
      '<input type="text" id="ch' + n + '-amp" class="num" autocomplete="off" value="5">' +
      '<span class="unit">Vpp</span>' +
      '<label for="ch' + n + '-off">offset</label>' +
      '<input type="text" id="ch' + n + '-off" class="num s" autocomplete="off" value="0">' +
      '<span class="unit">V</span>' +
    '</div>' +
    '<div class="row" id="ch' + n + '-phaserow">' +
      '<label class="fixed" for="ch' + n + '-phase">Phase</label>' +
      '<input type="text" id="ch' + n + '-phase" class="num" autocomplete="off" value="0">' +
      '<span class="unit">degrees</span>' +
    '</div>' +

    '<div class="row" id="ch' + n + '-dutyrow" hidden>' +
      '<label class="fixed" for="ch' + n + '-duty">Duty cycle</label>' +
      '<input type="text" id="ch' + n + '-duty" class="num" autocomplete="off" value="50">' +
      '<span class="unit">%</span>' +
    '</div>' +
    '<div class="row" id="ch' + n + '-symmrow" hidden>' +
      '<label class="fixed" for="ch' + n + '-symm">Symmetry</label>' +
      '<input type="text" id="ch' + n + '-symm" class="num" autocomplete="off" value="50">' +
      '<span class="unit">% (0 falling, 50 triangle, 100 rising)</span>' +
    '</div>' +
    '<div class="row" id="ch' + n + '-pwrow" hidden>' +
      '<label class="fixed" for="ch' + n + '-pw">Pulse width</label>' +
      '<input type="text" id="ch' + n + '-pw" class="num" autocomplete="off" value="100">' +
      '<select id="ch' + n + '-pwunit" aria-label="CH' + n + ' pulse width unit">' +
        punits + '</select>' +
      '<span class="val" id="ch' + n + '-pwinfo"></span>' +
    '</div>' +

    '<div class="row" role="group" aria-label="CH' + n + ' load impedance">' +
      '<span class="lbl fixed">Load</span>' +
      '<label class="chk"><input type="radio" name="ch' + n + '-load" value="high-z" checked> High-Z</label>' +
      '<label class="chk"><input type="radio" name="ch' + n + '-load" value="50"> 50 Ω</label>' +
      '<span class="spacer"></span>' +
      '<label class="chk"><input type="checkbox" id="ch' + n + '-inv"> inverted</label>' +
      '<label class="chk"><input type="checkbox" id="ch' + n + '-sync"> sync out</label>' +
    '</div>' +

    '<div class="row">' +
      '<label class="fixed" for="ch' + n + '-run">Run</label>' +
      '<select id="ch' + n + '-run">' +
        '<option value="continuous">continuous</option>' +
        '<option value="cycles">N cycles</option>' +
        '<option value="timed">timed</option></select>' +
      '<span id="ch' + n + '-cyclesbox" hidden>' +
        '<label for="ch' + n + '-cycles">cycles</label> ' +
        '<input type="text" id="ch' + n + '-cycles" class="num s" value="100"></span>' +
      '<span id="ch' + n + '-durbox" hidden>' +
        '<label for="ch' + n + '-dur">for</label> ' +
        '<input type="text" id="ch' + n + '-dur" class="num s" value="10"> ' +
        '<select id="ch' + n + '-durunit" aria-label="CH' + n + ' run duration unit">' +
          dunits + '</select></span>' +
    '</div>' +

    '<div class="bar">' +
      '<button id="ch' + n + '-apply">apply</button>' +
      '<button id="ch' + n + '-out" class="warn">output on</button>' +
      '<span class="val" id="ch' + n + '-count"></span>' +
    '</div>' +
    '<div class="statusline" id="ch' + n + '-stat"></div>' +
    '<div class="detail" id="ch' + n + '-detail"></div>' +
    '<div class="notice" id="ch' + n + '-notice" hidden></div>' +
    '</div>';
}

function makeChannel(n) {
  const c = {
    n: n,
    card: $("ch" + n + "-card"),
    wave: $("ch" + n + "-wave"),
    freq: $("ch" + n + "-freq"),
    frequnit: $("ch" + n + "-frequnit"),
    freqhz: $("ch" + n + "-freqhz"),
    amp: $("ch" + n + "-amp"),
    off: $("ch" + n + "-off"),
    phase: $("ch" + n + "-phase"),
    duty: $("ch" + n + "-duty"),
    symm: $("ch" + n + "-symm"),
    pw: $("ch" + n + "-pw"),
    pwunit: $("ch" + n + "-pwunit"),
    pwinfo: $("ch" + n + "-pwinfo"),
    inv: $("ch" + n + "-inv"),
    sync: $("ch" + n + "-sync"),
    run: $("ch" + n + "-run"),
    cycles: $("ch" + n + "-cycles"),
    dur: $("ch" + n + "-dur"),
    durunit: $("ch" + n + "-durunit"),
    applyBtn: $("ch" + n + "-apply"),
    outBtn: $("ch" + n + "-out"),
    count: $("ch" + n + "-count"),
    dot: $("ch" + n + "-dot"),
    pill: $("ch" + n + "-onpill"),
    head: $("ch" + n + "-head"),
    statLine: $("ch" + n + "-stat"),
    detail: $("ch" + n + "-detail"),
    notice: $("ch" + n + "-notice"),
    cv: $("ch" + n + "-cv"),
    pvwarn: $("ch" + n + "-pvwarn"),
    limwarn: $("ch" + n + "-limwarn"),
    last: null,          // last CH document from the server
    offAt: null,         // unix seconds, or null
    pvTimer: null,
    pvSeq: 0,
    holdUntil: 0,        // hold an error on screen long enough to read
  };

  const editable = [c.wave, c.freq, c.frequnit, c.amp, c.off, c.phase,
                    c.duty, c.symm, c.pw, c.pwunit, c.run, c.cycles,
                    c.dur, c.durunit];
  editable.forEach(watch);

  c.waveform = () => c.wave.value;

  c.freqHz = () => parseExpr(c.freq.value) * FREQ_UNITS[c.frequnit.value];

  c.pwSeconds = () => need(c.pw, "pulse width") * PW_UNITS[c.pwunit.value];

  // The evaluated Hz is shown next to the box because "1/0.1" is unreadable as
  // a frequency, and because a typo that the GUI would swallow must be visible.
  c.showFreq = () => {
    let hz = null;
    try { hz = c.freqHz(); } catch (e) {
      c.freqhz.textContent = "— " + e.message;
      c.freqhz.style.color = "#c77";
      return null;
    }
    c.freqhz.textContent = "= " + fmtFreq(hz);
    c.freqhz.style.color = "";
    return hz;
  };

  c.showPulse = () => {
    let hz, wsec;
    try { hz = c.freqHz(); wsec = c.pwSeconds(); } catch (e) { return; }
    if (!(hz > 0)) return;
    const period = 1 / hz;
    const duty = wsec / period * 100;
    c.pwinfo.textContent = "period " + fmtTime(period) + " · duty " +
      (duty > 100 ? ">100%!" : duty.toFixed(1) + "%");
    c.pwinfo.style.color = duty > 100 ? "#fb3" : "";
  };

  // Which extras exist is a property of the waveform, so hide the rest rather
  // than leaving dead boxes on a card that is already tall.
  c.showExtras = () => {
    const w = c.waveform();
    $("ch" + n + "-dutyrow").hidden = w !== "square";
    $("ch" + n + "-symmrow").hidden = w !== "ramp";
    $("ch" + n + "-pwrow").hidden = w !== "pulse";
    const noTime = (w === "noise" || w === "dc");
    $("ch" + n + "-freqrow").hidden = noTime;
    $("ch" + n + "-freqhint").hidden = noTime;
    $("ch" + n + "-phaserow").hidden = noTime;
    let hint = "";
    if (w === "noise") hint = "noise ignores frequency and phase";
    else if (w === "dc") hint = "DC uses the offset as the level; amplitude, frequency and phase are ignored";
    else if (w === "arbitrary") hint = "the waveform in the channel's arbitrary memory; generate or load one below";
    else if (w === "pulse") hint = "one pulse per period, centred; use N cycles for a pulse count";
    if (Date.now() >= c.holdUntil) line(c.statLine, hint, false);
    if (w === "pulse") c.showPulse();
  };

  c.showRun = () => {
    const m = c.run.value;
    $("ch" + n + "-cyclesbox").hidden = m !== "cycles";
    $("ch" + n + "-durbox").hidden = m !== "timed";
  };

  // ---- preview -----------------------------------------------------------
  c.schedulePreview = () => {
    clearTimeout(c.pvTimer);
    c.pvTimer = setTimeout(c.preview, PREVIEW_MS);
  };

  c.preview = async () => {
    const w = c.waveform();
    const q = new URLSearchParams();
    q.set("waveform", w);
    let hz = 1000;
    try { hz = c.freqHz(); } catch (e) {
      plotEmpty(c.cv, "frequency: " + e.message, true);
      return;
    }
    q.set("frequency", String(hz));
    q.set("amplitude", String(parseFloat(c.amp.value) || 0));
    q.set("offset", String(parseFloat(c.off.value) || 0));
    q.set("phase", String(parseFloat(c.phase.value) || 0));
    if (w === "square") q.set("duty_cycle", String(parseFloat(c.duty.value) || 0));
    if (w === "ramp") q.set("symmetry", String(parseFloat(c.symm.value) || 0));
    if (w === "pulse") {
      const sec = parseFloat(c.pw.value) * PW_UNITS[c.pwunit.value];
      if (isFinite(sec)) q.set("pulse_width", String(sec));
    }
    q.set("points", String(Math.min(2000, Math.max(400,
      Math.round((c.cv.clientWidth || 400) * 2)))));

    const seq = ++c.pvSeq;
    const r = await getJSON("/ch/" + n + "/preview?" + q.toString());
    if (seq !== c.pvSeq) return;      // a newer preview already landed
    if (!r.ok) {
      plotEmpty(c.cv, "preview unavailable — " + errOf(r), true);
      c.pvwarn.hidden = true;
      return;
    }
    const j = r.j;
    const scale = (typeof j.t_scale === "number" && j.t_scale) ? j.t_scale : 1;
    const t = (j.t || []).map(x => x * scale);
    plot(c.cv, {
      t: t, v: j.v || [],
      color: n === 1 ? "#7cf" : "#fb3",
      title: j.title || ("CH" + n + " — " + w),
      xLabel: "t (" + (j.t_unit || "s") + ")",
      yLabel: "V",
      empty: "no samples",
    });
    const warn = (j.warnings || []).filter(Boolean);
    c.pvwarn.textContent = warn.join("\n\n");
    c.pvwarn.hidden = warn.length === 0;
  };

  // ---- writes ------------------------------------------------------------
  c.adopt = (ch) => {
    if (!ch) return;
    c.last = ch;
    editable.forEach(clean);
    c.paint(ch, true);
    c.schedulePreview();
  };

  c.hold = (msg) => {
    line(c.statLine, msg, true);
    c.holdUntil = Date.now() + 4000;   // hold the message across refreshes
  };

  c.applyAll = async () => {
    if (c.applyBtn.disabled) return;
    let body;
    try {
      const w = c.waveform();
      body = {
        waveform: w,
        frequency: c.freqHz(),
        amplitude: need(c.amp, "amplitude"),
        offset: need(c.off, "offset"),
        phase: need(c.phase, "phase"),
      };
      if (w === "square") body.duty_cycle = need(c.duty, "duty cycle");
      if (w === "ramp") body.symmetry = need(c.symm, "symmetry");
      if (w === "pulse") body.pulse_width = c.pwSeconds();
    } catch (e) {
      c.hold(e.message);
      return;
    }
    c.applyBtn.disabled = true;
    try {
      const r = await post("/ch/" + n + "/apply", body);
      if (!r.ok) { c.hold("apply: " + errOf(r)); return; }
      c.adopt(r.j);
      line(c.statLine, "applied · " + fmtFreq(body.frequency) + " · " +
        sig(body.amplitude, 4) + " Vpp", false);
    } finally { c.applyBtn.disabled = false; }
  };

  // Enter applies the focused field on its own: the operator asked for that one
  // change, and pushing the whole card would carry along edits still in flight
  // in the other boxes.
  c.setOne = async (param, value, label) => {
    const body = {};
    body[param] = value;
    const r = await post("/ch/" + n + "/set", body);
    if (!r.ok) { c.hold(label + ": " + errOf(r)); return; }
    c.adopt(r.j);
    line(c.statLine, label + " → " + (param === "frequency"
      ? fmtFreq(value) : sig(value, 6)), false);
  };

  c.toggleOutput = async () => {
    if (c.outBtn.disabled) return;
    const on = !(c.last && truthy(c.last.output));
    const body = { on: on };
    if (on) {
      try {
        if (c.run.value === "cycles") {
          const k = parseInt(c.cycles.value, 10);
          if (!isFinite(k) || k <= 0) throw new Error("cycles must be a positive whole number");
          body.cycles = k;
        } else if (c.run.value === "timed") {
          const d = need(c.dur, "duration") * DUR_UNITS[c.durunit.value];
          if (!(d > 0)) throw new Error("duration must be greater than zero");
          body.seconds = d;
        }
      } catch (e) { c.hold(e.message); return; }
    }
    c.outBtn.disabled = true;
    try {
      const r = await post("/ch/" + n + "/output", body);
      if (!r.ok) { c.hold("output: " + errOf(r)); return; }
      c.adopt(r.j);
      line(c.statLine, on ? "output on" : "output off", false);
    } finally { c.outBtn.disabled = false; }
  };

  // ---- painting ----------------------------------------------------------
  c.paint = (ch, force) => {
    if (!ch) return;
    c.last = ch;
    // Server-derived limit warnings: what the DG822 cannot honour about this
    // channel's CURRENT settings. Painted unconditionally, never behind a dirty
    // flag or a focus guard -- an over-rail level is a live condition, not a
    // transient reply to one request, and the instrument clamps it without
    // telling anyone. A toast would scroll away; this stays until it is fixed.
    const lw = (ch.warnings || []).filter(Boolean);
    c.limwarn.textContent = lw.join("\n\n");
    c.limwarn.hidden = lw.length === 0;
    const w = normWave(ch.function);
    if (w && (force || (c.wave !== document.activeElement && !c.wave.dataset.dirty))) {
      // Guard the operator's arb work: the instrument reports USER/SEQ for a
      // freshly uploaded waveform, and re-selecting it would rebuild the card's
      // extras out from under an upload that is mid-flight.
      if (c.wave.value !== w && WAVEFORMS.some(x => x[0] === w)) c.wave.value = w;
    }
    if (typeof ch.frequency === "number" &&
        c.freq !== document.activeElement && !c.freq.dataset.dirty &&
        !c.frequnit.dataset.dirty) {
      const u = Math.abs(ch.frequency) >= 1e6 ? "MHz"
        : Math.abs(ch.frequency) >= 1e3 ? "kHz" : "Hz";
      c.frequnit.value = u;
      c.freq.value = sig(ch.frequency / FREQ_UNITS[u], 6);
    }
    fill(c.amp, ch.amplitude == null ? "" : sig(ch.amplitude, 6));
    fill(c.off, ch.offset == null ? "" : sig(ch.offset, 6));
    fill(c.phase, ch.phase == null ? "" : sig(ch.phase, 6));
    fill(c.duty, ch.duty_cycle == null ? "" : sig(ch.duty_cycle, 6));
    fill(c.symm, ch.symmetry == null ? "" : sig(ch.symmetry, 6));
    if (typeof ch.pulse_width === "number" &&
        c.pw !== document.activeElement && !c.pw.dataset.dirty &&
        !c.pwunit.dataset.dirty) {
      const u = bestUnit(ch.pulse_width, PW_UNITS);
      c.pwunit.value = u;
      c.pw.value = sig(ch.pulse_width / PW_UNITS[u], 6);
    }
    setRadio("ch" + n + "-load", isHighZ(ch.impedance) ? "high-z" : "50");
    fillCheck(c.inv, truthy(ch.polarity));
    fillCheck(c.sync, truthy(ch.sync));

    const on = truthy(ch.output);
    c.card.classList.toggle("on", on);
    c.pill.hidden = !on;
    c.outBtn.classList.toggle("on", on);
    c.outBtn.textContent = on ? "output off" : "output on";
    c.dot.className = "dot" + (!connected ? " off" : on ? " rec" : "");

    // The run mode the instrument reports wins while a run is actually in
    // flight; otherwise it is the operator's choice for the next output-on.
    const rm = normRunMode(ch.run_mode);
    if (on && rm && !c.run.dataset.dirty && c.run !== document.activeElement) {
      c.run.value = rm;
    }
    c.showRun();

    c.offAt = (typeof ch.off_at === "number") ? ch.off_at : null;
    // A scheduled run keeps the parameters it started with, so freeze just the
    // run-mode boxes while one is counting down (the dock freezes a running
    // timelapse the same way). Frequency and amplitude stay live on purpose —
    // trimming a live output is the whole point of a generator.
    const timed = c.offAt != null;
    for (const el of [c.run, c.cycles, c.dur, c.durunit]) {
      el.disabled = !connected || timed;
    }

    const head = [];
    if (ch.arb_name) head.push(String(ch.arb_name));
    if (ch.sample_rate) head.push(fmtRate(ch.sample_rate));
    if (ch.points) head.push(ch.points + " pts");
    c.head.textContent = head.join(" · ");

    const det = [];
    det.push("out " + (on ? "ON" : "off") +
      " · " + (isHighZ(ch.impedance) ? "High-Z" : sig(ch.impedance, 6) + " Ω") +
      (truthy(ch.polarity) ? " · inverted" : "") +
      (truthy(ch.sync) ? " · sync" : ""));
    if (typeof ch.frequency === "number") {
      det.push(fmtFreq(ch.frequency) + " · " + sig(ch.amplitude, 5) + " Vpp · " +
        sig(ch.offset, 5) + " V · " + sig(ch.phase, 5) + "°");
    }
    c.detail.innerHTML = det.map(t =>
      '<span>' + t.replace(/&/g, "&amp;").replace(/</g, "&lt;") + '</span>').join("");
    c.tick();
  };

  c.tick = () => {
    if (c.offAt == null) { c.count.textContent = ""; return; }
    // off_at is the server's unix clock. Panel and browser are the same machine
    // in the normal deployment; a remote browser with a skewed clock sees a
    // countdown that is off by the skew, never a wrong output state — the
    // authority for that is the polled `output` field.
    const left = c.offAt - Date.now() / 1000;
    c.count.textContent = left > 0
      ? "off in " + fmtDur(left)
      : "switching off…";
  };

  c.setEnabled = (on) => {
    enableAll(c.card, on);
    if (on) c.showRun();
    c.notice.hidden = on;
    if (!on) c.dot.className = "dot off";
  };

  // ---- bindings ----------------------------------------------------------
  c.wave.onchange = () => { c.showExtras(); c.schedulePreview(); };
  c.run.onchange = c.showRun;

  const live = [c.freq, c.frequnit, c.amp, c.off, c.phase, c.duty, c.symm,
                c.pw, c.pwunit];
  for (const el of live) {
    el.addEventListener("input", () => {
      c.showFreq();
      if (c.waveform() === "pulse") c.showPulse();
      c.schedulePreview();
    });
    el.addEventListener("change", () => {
      c.showFreq();
      if (c.waveform() === "pulse") c.showPulse();
      c.schedulePreview();
    });
  }

  // Enter applies the focused field. No form, no page reload, no dialog.
  const enterMap = [
    [c.freq, "frequency", () => c.freqHz(), "frequency"],
    [c.amp, "amplitude", () => need(c.amp, "amplitude"), "amplitude"],
    [c.off, "offset", () => need(c.off, "offset"), "offset"],
    [c.phase, "phase", () => need(c.phase, "phase"), "phase"],
    [c.duty, "duty_cycle", () => need(c.duty, "duty cycle"), "duty cycle"],
    [c.symm, "symmetry", () => need(c.symm, "symmetry"), "symmetry"],
    [c.pw, "pulse_width", () => c.pwSeconds(), "pulse width"],
  ];
  for (const [el, param, read, label] of enterMap) {
    el.addEventListener("keydown", ev => {
      if (ev.key !== "Enter" || el.disabled) return;
      ev.preventDefault();
      let v;
      try { v = read(); } catch (e) { c.hold(e.message); return; }
      c.setOne(param, v, label);
    });
  }
  for (const el of [c.cycles, c.dur]) {
    el.addEventListener("keydown", ev => {
      if (ev.key === "Enter") { ev.preventDefault(); c.toggleOutput(); }
    });
  }

  c.applyBtn.onclick = c.applyAll;
  c.outBtn.onclick = c.toggleOutput;
  $("ch" + n + "-revert").onclick = () => {
    editable.forEach(clean);
    if (c.last) c.paint(c.last, true);
    c.showExtras();
    c.showFreq();
    c.schedulePreview();
    line(c.statLine, "showing the instrument's values", false);
  };

  for (const el of document.querySelectorAll('input[name="ch' + n + '-load"]')) {
    el.addEventListener("change", async () => {
      const v = el.value === "50" ? 50 : "high-z";
      const r = await post("/ch/" + n + "/load", { impedance: v });
      if (!r.ok) { c.hold("load: " + errOf(r)); return; }
      c.adopt(r.j);
      line(c.statLine, "load → " + (v === 50 ? "50 Ω" : "High-Z"), false);
    });
  }
  c.inv.onchange = async () => {
    const r = await post("/ch/" + n + "/polarity", { inverted: c.inv.checked });
    if (!r.ok) { c.hold("polarity: " + errOf(r)); c.inv.checked = !c.inv.checked; return; }
    c.adopt(r.j);
  };
  c.sync.onchange = async () => {
    const r = await post("/ch/" + n + "/sync", { on: c.sync.checked });
    if (!r.ok) { c.hold("sync: " + errOf(r)); c.sync.checked = !c.sync.checked; return; }
    c.adopt(r.j);
  };

  c.notice.textContent =
    "CH" + n + " is not connected — the controls above are disabled until " +
    "the generator is connected.";
  c.showExtras();
  c.showFreq();
  c.showRun();
  plotEmpty(c.cv, "preview loads when the page connects");
  return c;
}

// ------------------------------------------------------------ connection ---
async function scan() {
  const btn = $("scan");
  btn.disabled = true;
  // A USB scan queries every candidate with a 2 s VISA timeout, so hold the
  // line well past the poll's one-second rewrite or it reads as a no-op.
  connLine("scanning for instruments…", false, 30000);
  try {
    const r = await getJSON("/devices");
    if (!r.ok) { connLine("scan: " + errOf(r), true); return; }
    const devs = r.j.devices || [];
    const sel = $("devsel");
    const keep = sel.value;
    sel.innerHTML = devs.length
      ? devs.map(d => '<option value="' + esc(d.resource) + '">' +
          esc((d.idn || d.resource) + (d.sim ? "  [SIMULATED]" : "") +
              " (" + d.resource + ")") + '</option>').join("")
      : '<option value="">(no instruments found)</option>';
    if (keep && devs.some(d => d.resource === keep)) sel.value = keep;
    else if (devs.length && !$("visa").value) $("visa").value = devs[0].resource;
    connLine(devs.length
      ? "found " + devs.length + " instrument" + (devs.length === 1 ? "" : "s")
      : "no instruments found" + (r.j.reason ? " — " + r.j.reason : ""),
      devs.length === 0);
  } finally { btn.disabled = false; }
}

function esc(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function doConnect() {
  const btn = $("connect");
  btn.disabled = true;
  const body = {};
  if ($("simchk").checked) body.sim = true;
  else {
    const res = ($("visa").value || "").trim() || $("devsel").value;
    if (!res) {
      connLine("pick a device from the list, type a VISA address, " +
        "or tick the simulated box", true);
      btn.disabled = false;
      return;
    }
    body.resource = res;
  }
  // Opening a VISA session and asking *IDN? takes seconds on a slow hub.
  connLine("connecting…", false, 30000);
  try {
    const r = await post("/connect", body);
    if (!r.ok) { connLine("connect: " + errOf(r), true); return; }
    adopt(r.j);
    connLine(connected ? "connected" : whyNot(r.j), !connected);
  } finally { btn.disabled = false; }
}

async function doDisconnect() {
  const btn = $("disconnect");
  btn.disabled = true;
  connLine("disconnecting…", false, 30000);
  try {
    const r = await post("/disconnect");
    if (!r.ok) { connLine("disconnect: " + errOf(r), true); return; }
    adopt(r.j);
    connLine("disconnected — the outputs keep whatever state they were left in", false);
  } finally { btn.disabled = false; }
}

function whyNot(st) {
  if (!st) return "no reply from the DG822 service — is the panel still running?";
  if (st.error) return String(st.error);
  if (st.backend_reason) return String(st.backend_reason);
  return "not connected — scan and pick an instrument, type a VISA address, " +
    "or tick the simulated box, then press connect.";
}

// ------------------------------------------------------------- arb block ---
let shapes = [];               // /api/arb/shapes
let arb = null;                // last /api/arb/generate result
let arbParamEls = [];          // [{spec, input, unit}]

function shapeSpec() {
  return shapes.find(s => s.name === $("arb-shape").value) || null;
}
function isComb() {
  const s = shapeSpec();
  return !!s && s.name === "frequency_comb";
}
function arbDrive() { return radioValue("arb-drive") || "frequency"; }
function arbPolarity() { return radioValue("arb-pol") || "unipolar"; }

// Frequency mode types a frequency; time mode types a period — and in bipolar
// time mode the shape occupies half the output period, so the box is the HALF
// period. That is the tkinter dialog's rule and the label says which one it is.
function arbOutputHz() {
  const v = parseExpr($("arb-freq").value);
  const u = $("arb-frequnit").value;
  if (arbDrive() === "frequency") return v * (FREQ_UNITS[u] || 1);
  const period = v * (ARB_TIME_UNITS[u] || 1);
  if (!(period > 0)) throw new Error("period must be greater than zero");
  return arbPolarity() === "bipolar" ? 1 / (2 * period) : 1 / period;
}

function arbFreqControls() {
  const sel = $("arb-frequnit");
  const time = arbDrive() === "time";
  const units = time ? Object.keys(ARB_TIME_UNITS) : Object.keys(FREQ_UNITS);
  const keep = sel.value;
  sel.innerHTML = units.map(u => '<option value="' + u + '">' + u + '</option>').join("");
  sel.value = units.indexOf(keep) >= 0 ? keep : (time ? "ms" : "Hz");
  $("arb-freqlabel").textContent = time
    ? (arbPolarity() === "bipolar" ? "Half period" : "Period")
    : "Frequency";
  arbShowFreq();
}

function arbShowFreq() {
  try {
    const hz = arbOutputHz();
    $("arb-freqout").textContent = "output " + fmtFreq(hz) +
      " · period " + fmtTime(1 / hz);
    $("arb-freqout").style.color = "";
  } catch (e) {
    $("arb-freqout").textContent = "— " + e.message;
    $("arb-freqout").style.color = "#c77";
  }
}

async function loadShapes() {
  const r = await getJSON("/arb/shapes");
  if (!r.ok || !Array.isArray(r.j)) {
    line($("arb-stat"), "shapes: " + errOf(r), true);
    return;
  }
  shapes = r.j;
  const sel = $("arb-shape");
  sel.innerHTML = shapes.map(s =>
    '<option value="' + esc(s.name) + '">' + esc(s.label || s.name) + '</option>').join("");
  renderShape();
}

function renderShape() {
  const s = shapeSpec();
  const comb = isComb();
  $("arb-comb").hidden = !comb;
  $("arb-waverow").hidden = comb;
  $("arb-freqrow").hidden = comb;
  $("arb-params").hidden = comb;
  arbParamEls = [];
  const host = $("arb-params");
  host.innerHTML = "";
  if (!s || comb) { arbInfo(); return; }

  let period = 1e-3;
  try { period = 1 / arbOutputHz(); } catch (e) { }
  if (arbPolarity() === "bipolar") period /= 2;
  const fr = AUTO_FRACTIONS[s.name] || [];
  let timeIdx = 0;

  for (const p of (s.params || [])) {
    const id = "arbp-" + p.name;
    const timed = !!p.unit && Object.prototype.hasOwnProperty.call(ARB_TIME_UNITS, p.unit);
    const row = document.createElement("div");
    row.className = "row";
    let def = p.default;
    let unit = p.unit || "";
    if (timed) {
      // A null default means "derive it from the period" — the dialog's auto
      // time defaults, so a freshly picked shape is already sensible.
      let secs = (def == null) ? (fr[timeIdx] == null ? period * 0.5 : fr[timeIdx] * period)
                               : Number(def);
      timeIdx += 1;
      unit = bestUnit(secs, ARB_TIME_UNITS);
      def = sig(secs / ARB_TIME_UNITS[unit], 6);
    } else if (def == null) {
      def = "0";
    }
    row.innerHTML =
      '<label class="fixed" for="' + esc(id) + '">' + esc(p.label || p.name) + '</label>' +
      '<input type="text" class="num" id="' + esc(id) + '" autocomplete="off" value="' +
        esc(def) + '">' +
      (timed
        ? '<select id="' + esc(id) + '-u" aria-label="' + esc(p.label || p.name) + ' unit">' +
          Object.keys(ARB_TIME_UNITS).map(u =>
            '<option value="' + u + '"' + (u === unit ? " selected" : "") + '>' + u +
            '</option>').join("") + '</select>'
        : (p.unit ? '<span class="unit">' + esc(p.unit) + '</span>' : "")) +
      (p.min != null || p.max != null
        ? '<span class="hint">' +
          (p.min != null ? "min " + esc(p.min) : "") +
          (p.min != null && p.max != null ? " · " : "") +
          (p.max != null ? "max " + esc(p.max) : "") + '</span>'
        : "");
    host.appendChild(row);
    const input = $(id);
    const usel = timed ? $(id + "-u") : null;
    input.addEventListener("input", arbInfo);
    if (usel) usel.addEventListener("change", arbInfo);
    arbParamEls.push({ spec: p, input: input, unit: usel, timed: timed });
  }
  arbInfo();
}

function arbParams() {
  const out = {};
  for (const p of arbParamEls) {
    const v = parseFloat(p.input.value);
    if (!isFinite(v)) throw new Error((p.spec.label || p.spec.name) + ": not a number");
    out[p.spec.name] = p.timed ? v * ARB_TIME_UNITS[p.unit.value] : v;
  }
  return out;
}

function combBody() {
  const mode = radioValue("arb-combmode") || "range";
  const body = {
    mode: mode,
    phases: radioValue("arb-phase") || "random",
    iterations: parseInt($("arb-iters").value, 10) || 1,
  };
  if (mode === "range") {
    body.start = need($("arb-cstart"), "start");
    body.stop = need($("arb-cstop"), "stop");
    body.step = need($("arb-cstep"), "step");
    body.list = [];
  } else {
    const list = ($("arb-clist").value || "").split(",")
      .map(x => parseFloat(x.trim())).filter(x => isFinite(x));
    if (!list.length) throw new Error("no frequencies in the list");
    body.list = list;
    body.start = body.stop = body.step = null;
  }
  return body;
}

// The sizing panel is recomputed locally between generates so the operator sees
// the consequences of a parameter before spending a Monte Carlo run on it. The
// numbers that matter (points, sample rate, warnings) still come from the
// server on generate — this is a preview of the shape, not a second model.
function arbInfo() {
  arbShowFreq();
  const parts = [];
  if (isComb()) {
    parts.push("frequency comb · phases " + (radioValue("arb-phase") || "random"));
  } else {
    try {
      const hz = arbOutputHz();
      parts.push("polarity " + arbPolarity() + " · drive " + arbDrive());
      parts.push("output " + fmtFreq(hz) + " · period " + fmtTime(1 / hz));
    } catch (e) { parts.push("cannot size: " + e.message); }
  }
  if (arb) {
    parts.push("generated: " + (arb.name || "?") + " · " + arb.points + " pts · " +
      fmtRate(arb.sample_rate) + " · f0 " + fmtFreq(arb.output_frequency));
    for (const [k, v] of Object.entries(arb.info || {})) {
      if (k === "token" || k === "warning") continue;
      parts.push("  " + k + " = " + (typeof v === "number" ? sig(v, 6) : String(v)));
    }
  }
  $("arb-info").innerHTML = parts.map(t => '<span>' + esc(t) + '</span>').join("");
}

function arbWarn(list) {
  const w = (list || []).filter(Boolean).map(String);
  $("arb-warn").textContent = w.join("\n\n");
  $("arb-warn").hidden = w.length === 0;
}

function drawArb() {
  if (!arb || !arb.data || !arb.data.length) {
    plotEmpty($("arb-cv"), "generate or load a waveform to see it here");
    return;
  }
  const d = arb.data;
  const t = new Array(d.length);
  for (let i = 0; i < d.length; i++) t[i] = i;
  plot($("arb-cv"), {
    t: t, v: d, color: "#8fd6b0",
    title: (arb.name || "arb") + " · " + arb.points + " pts",
    xLabel: "sample (of " + arb.points + ")",
    yLabel: "normalised",
  });
}

function adoptArb(j) {
  arb = j;
  arbWarn(j.warnings);
  arbInfo();
  drawArb();
  $("arb-name").textContent = (j.name || "") + " · " + j.points + " pts";
  if (!$("arb-upname").dataset.dirty) {
    $("arb-upname").value = String(j.name || "CUSTOM").slice(0, 7);
  }
}

async function arbGenerate() {
  const btn = $("arb-gen");
  if (btn.disabled) return;
  let body;
  try {
    const s = shapeSpec();
    if (!s) throw new Error("no shape selected");
    body = {
      shape: s.name,
      polarity: arbPolarity(),
      drive_mode: arbDrive(),
      params: isComb() ? {} : arbParams(),
    };
    const pts = parseInt($("arb-points").value, 10);
    if (isFinite(pts) && pts > 0) body.points = pts;
    if (isComb()) {
      body.comb = combBody();
      body.frequency = null;
    } else if (arbDrive() === "time") {
      body.period = parseExpr($("arb-freq").value) *
        (ARB_TIME_UNITS[$("arb-frequnit").value] || 1);
    } else {
      body.frequency = parseExpr($("arb-freq").value) *
        (FREQ_UNITS[$("arb-frequnit").value] || 1);
    }
  } catch (e) {
    line($("arb-stat"), e.message, true);
    return;
  }
  btn.disabled = true;
  // A Monte Carlo comb takes seconds on the server; say so rather than looking
  // wedged (the tkinter dialog retitles its window for the same reason).
  line($("arb-stat"), isComb() && (radioValue("arb-phase") === "random")
    ? "generating — Monte Carlo phase optimisation…" : "generating…", false);
  try {
    const r = await post("/arb/generate", body);
    if (!r.ok) { line($("arb-stat"), "generate: " + errOf(r), true); return; }
    adoptArb(r.j);
    line($("arb-stat"), "generated " + (r.j.name || "") + " · " + r.j.points +
      " points · " + fmtRate(r.j.sample_rate), false);
  } finally { btn.disabled = false; }
}

function arbSource() {
  // The full buffer stays on the server under info.token; the page only ever
  // holds the decimated preview, so upload/save must reference the token and
  // fall back to the samples it does have.
  if (!arb) return null;
  const tok = arb.info && arb.info.token;
  return tok ? { token: tok } : { data: arb.data };
}

async function arbUpload() {
  const btn = $("arb-upload");
  if (btn.disabled) return;
  if (!arb) { line($("arb-stat"), "generate or load a waveform first", true); return; }
  let body;
  try {
    body = Object.assign({
      channel: parseInt($("arb-upch").value, 10),
      name: ($("arb-upname").value || "CUSTOM").slice(0, 7),
      save_raf: $("arb-saveraf").checked,
      amplitude: need($("arb-upamp"), "amplitude"),
      offset: need($("arb-upoff"), "offset"),
    }, arbSource());
  } catch (e) { line($("arb-stat"), e.message, true); return; }
  btn.disabled = true;
  line($("arb-stat"), "uploading " + arb.points + " points to CH" + body.channel + "…", false);
  try {
    const r = await post("/arb/upload", body);
    if (!r.ok) { line($("arb-stat"), "upload: " + errOf(r), true); return; }
    const c = CH[body.channel];
    if (c) c.adopt(r.j);
    line($("arb-stat"), "uploaded " + body.name + " to CH" + body.channel +
      (body.save_raf ? " and stored " + body.name + ".RAF" : ""), false);
    refreshFiles();
  } finally { btn.disabled = false; }
}

async function arbSaveCsv() {
  if (!arb) { line($("arb-stat"), "generate or load a waveform first", true); return; }
  let body;
  try {
    body = Object.assign({
      name: ($("arb-upname").value || arb.name || "CUSTOM"),
      amplitude: need($("arb-upamp"), "amplitude"),
    }, arbSource());
  } catch (e) { line($("arb-stat"), e.message, true); return; }
  const r = await post("/arb/save-csv", body);
  if (!r.ok) { line($("arb-stat"), "save CSV: " + errOf(r), true); return; }
  stat("waveform saved → " + (r.j.path || "?"));
  line($("arb-stat"), "saved " + (r.j.path || ""), false);
  refreshFiles();
}

async function arbLoadCsv() {
  const name = $("arb-csvlist").value;
  if (!name) { line($("arb-stat"), "no CSV selected", true); return; }
  const r = await post("/arb/load-csv", { name: name });
  if (!r.ok) { line($("arb-stat"), "load CSV: " + errOf(r), true); return; }
  adoptArb(r.j);
  line($("arb-stat"), "loaded " + name + " · " + r.j.points + " points", false);
}

async function arbStoreRaf() {
  const name = ($("arb-upname").value || "").slice(0, 7);
  if (!name) { line($("arb-stat"), "give the waveform a name (7 characters)", true); return; }
  const r = await post("/arb/store-raf", { name: name });
  if (!r.ok) { line($("arb-stat"), "store .RAF: " + errOf(r), true); return; }
  line($("arb-stat"), "stored " + name + ".RAF on the instrument", false);
  refreshFiles();
}

async function arbLoadRaf() {
  const name = $("arb-raflist").value;
  if (!name) { line($("arb-stat"), "no instrument waveform selected", true); return; }
  const ch = parseInt($("arb-rafch").value, 10);
  const r = await post("/arb/load-raf", { name: name, channel: ch });
  if (!r.ok) { line($("arb-stat"), "load .RAF: " + errOf(r), true); return; }
  if (CH[ch]) CH[ch].adopt(r.j);
  line($("arb-stat"), "loaded " + name + " into CH" + ch, false);
}

async function refreshFiles() {
  const r = await getJSON("/arb/files");
  if (!r.ok) return;                      // a failed list is not news
  const fillList = (sel, names, empty) => {
    const keep = sel.value;
    const list = names || [];
    sel.innerHTML = list.length
      ? list.map(nm => '<option value="' + esc(nm) + '">' + esc(nm) + '</option>').join("")
      : '<option value="">' + esc(empty) + '</option>';
    if (keep && list.indexOf(keep) >= 0) sel.value = keep;   // keep the selection
  };
  fillList($("arb-csvlist"), r.j.local, "(no saved CSV files)");
  fillList($("arb-raflist"), r.j.instrument, "(none stored on the instrument)");
  $("arb-dir").textContent = r.j.dir ? "waveform folder: " + r.j.dir : "";
}

// -------------------------------------------------------------- presets ----
async function loadPresets() {
  const r = await getJSON("/presets");
  if (!r.ok || !Array.isArray(r.j)) {
    line($("preset-stat"), "presets: " + errOf(r), true);
    return;
  }
  const host = $("preset-list");
  host.innerHTML = "";
  for (const p of r.j) {
    const b = document.createElement("button");
    b.className = "ghost";
    b.textContent = p.label || p.id;
    if (p.description) b.title = p.description;
    b.onclick = async () => {
      if (b.disabled) return;
      b.disabled = true;
      try {
        const target = radioValue("preset-ch") || "1";
        const chans = target === "both" ? [1, 2] : [parseInt(target, 10)];
        for (const n of chans) {
          const rr = await post("/presets/apply", { id: p.id, channel: n });
          if (!rr.ok) { line($("preset-stat"), "preset: " + errOf(rr), true); return; }
          if (CH[n]) CH[n].adopt(rr.j);
        }
        line($("preset-stat"), (p.label || p.id) + " → " +
          (target === "both" ? "CH1 and CH2" : "CH" + target), false);
      } finally { b.disabled = false; }
    };
    host.appendChild(b);
  }
  if (!r.j.length) host.innerHTML = '<span class="muted">no presets defined</span>';
}

// ----------------------------------------------------------------- state ---
function adopt(st) {
  if (!st) return;
  S = st;
  stateSeq += 1;
  connected = !!st.connected;
  const sim = !!st.sim;

  document.body.classList.toggle("sim", sim && connected);
  $("simbadge").hidden = !(sim && connected);

  const info = $("info");
  if (connected) {
    info.textContent = (sim ? "SIMULATED · " : "") + (st.resource || "connected");
    info.className = "status " + (sim ? "" : "ok");
  } else {
    info.textContent = "not connected";
    info.className = "status err";
  }

  const det = [];
  if (st.idn) det.push(String(st.idn));
  if (st.resource) det.push(String(st.resource));
  if (sim) det.push("SIMULATED INSTRUMENT — no hardware is being driven");
  $("conn-detail").innerHTML = det.map(t =>
    '<span' + (sim && /SIMULATED/.test(t) ? ' class="warn"' : "") + '>' +
    esc(t) + '</span>').join("");

  // Remember what we are (or were) talking to, so disconnect -> connect does
  // not leave the operator with an empty address box and a refusal. Only ever
  // into an empty field: the address is something they may be editing.
  if (st.resource && !st.sim && !$("visa").value && document.activeElement !== $("visa")) {
    $("visa").value = st.resource;
  }
  if (st.sim) fillCheck($("simchk"), true);

  $("connect").textContent = connected ? "reconnect" : "connect";
  $("disconnect").disabled = !connected;
  for (const id of ["beep", "syncph", "reset"]) $(id).disabled = !connected;

  if (Date.now() >= connHold) {
    if (!connected) line($("conn-stat"), whyNot(st), true);
    else if ($("conn-stat").classList.contains("err")) line($("conn-stat"), "connected", false);
  }

  const chans = st.channels || {};
  for (const n of [1, 2]) {
    const c = CH[n];
    if (!c) continue;
    c.setEnabled(connected);
    const doc = chans[String(n)] || chans[n];
    if (doc) c.paint(doc, false);
  }

  // The arb block's maths and files do not touch the instrument, so they stay
  // live while disconnected; only the paths that write to it are stopped.
  const upDisabled = !connected;
  for (const id of ["arb-upload", "arb-storeraf", "arb-loadraf", "arb-upch",
                    "arb-rafch", "arb-raflist", "arb-saveraf"]) {
    $(id).disabled = upDisabled;
  }
  $("arb-notice").hidden = connected;
  $("arb-notice").textContent =
    "not connected — shapes, previews and CSV files still work; " +
    "upload and .RAF storage need the instrument.";
  // The target radios are a page-local choice, not an instrument write, so they
  // stay usable while disconnected — only the preset buttons are stopped.
  enableAll($("presetcard"), connected, el => el.type === "radio");
  $("preset-notice").hidden = connected;
  $("preset-notice").textContent =
    "not connected — a preset writes straight to the instrument, " +
    "so there is nothing to apply to yet.";
}

async function poll() {
  const r = await getJSON("/state");
  if (r.ok && r.j && typeof r.j === "object") {
    // A single failed poll is not news; three in a row is. Same threshold the
    // shell uses before it calls the dock stale.
    pollFails = 0;
    document.body.classList.remove("stale");
    adopt(r.j);
  } else {
    pollFails += 1;
    if (pollFails >= 3) {
      document.body.classList.add("stale");
      $("info").textContent = "lost contact with the DG822 service";
      $("info").className = "status err";
      line($("conn-stat"),
        "no reply from " + API + "/state — the values below are last known. " +
        (errOf(r)), true);
    }
  }
  // setTimeout at the end of the body, never setInterval: a slow reply must not
  // let requests stack up on a busy VISA session.
  setTimeout(poll, POLL_MS);
}

// ------------------------------------------------------------------ boot ---
function boot() {
  const host = $("channels");
  host.innerHTML = chanHTML(1) + chanHTML(2);
  CH[1] = makeChannel(1);
  CH[2] = makeChannel(2);

  $("scan").onclick = scan;
  $("connect").onclick = doConnect;
  $("disconnect").onclick = doDisconnect;
  $("visa").addEventListener("keydown", ev => {
    if (ev.key === "Enter") { ev.preventDefault(); doConnect(); }
  });
  $("devsel").onchange = () => {
    // Picking from the list is the same act as typing the address; show it, so
    // what will be opened is never ambiguous.
    if ($("devsel").value) $("visa").value = $("devsel").value;
  };
  $("beep").onclick = async () => {
    const r = await post("/beep");
    toast(r.ok ? "beep" : "beep: " + errOf(r));
  };
  $("syncph").onclick = async () => {
    const r = await post("/sync-phases");
    toast(r.ok ? "CH1 and CH2 phases synchronised" : "sync: " + errOf(r));
  };
  // Ticking the box is a decision the poll must not undo (see adopt): a sim
  // state that unticks itself would send the next connect at real hardware.
  watch($("simchk"));
  armConfirm($("reset"), "reset", async () => {
    const r = await post("/reset");
    if (!r.ok) { connLine("reset: " + errOf(r), true); return; }
    adopt(r.j);
    toast("instrument reset (*RST)");
  });

  $("arb-shape").onchange = renderShape;
  $("arb-gen").onclick = arbGenerate;
  $("arb-upload").onclick = arbUpload;
  $("arb-savecsv").onclick = arbSaveCsv;
  $("arb-loadcsv").onclick = arbLoadCsv;
  $("arb-storeraf").onclick = arbStoreRaf;
  $("arb-loadraf").onclick = arbLoadRaf;
  $("arb-files").onclick = refreshFiles;
  $("arb-freq").addEventListener("input", arbInfo);
  $("arb-frequnit").addEventListener("change", arbInfo);
  $("arb-points").addEventListener("input", arbInfo);
  $("arb-iters").addEventListener("input", arbInfo);
  watch($("arb-upname"));
  for (const el of document.querySelectorAll('input[name="arb-drive"]')) {
    el.addEventListener("change", () => { arbFreqControls(); renderShape(); });
  }
  for (const el of document.querySelectorAll('input[name="arb-pol"]')) {
    el.addEventListener("change", () => { arbFreqControls(); renderShape(); });
  }
  for (const el of document.querySelectorAll('input[name="arb-combmode"]')) {
    el.addEventListener("change", () => {
      const range = radioValue("arb-combmode") === "range";
      $("arb-combrange").hidden = !range;
      $("arb-comblist").hidden = range;
      arbInfo();
    });
  }
  for (const el of document.querySelectorAll('input[name="arb-phase"]')) {
    el.addEventListener("change", arbInfo);
  }
  $("arb-freq").addEventListener("keydown", ev => {
    if (ev.key === "Enter") { ev.preventDefault(); arbGenerate(); }
  });

  arbFreqControls();
  plotEmpty($("arb-cv"), "generate or load a waveform to see it here");

  // A pane the shell hid and re-showed, or a panel resized by dragging the
  // window, changes the canvas' CSS size — and a canvas does not reflow, it
  // stretches. Redraw on resize or the trace ends up interpolated.
  let rzTimer = null;
  const redraw = () => {
    clearTimeout(rzTimer);
    rzTimer = setTimeout(() => {
      for (const n of [1, 2]) if (CH[n]) CH[n].preview();
      drawArb();
    }, 150);
  };
  window.addEventListener("resize", redraw);

  // One ticker for both countdowns: two timers would drift apart on screen.
  setInterval(() => { for (const n of [1, 2]) if (CH[n]) CH[n].tick(); }, 250);

  // Server-owned state means a reload rediscovers what the instrument is doing,
  // rather than pushing this page's defaults at it.
  poll();
  loadShapes();
  loadPresets();
  refreshFiles();
  for (const n of [1, 2]) CH[n].schedulePreview();
}

boot();
