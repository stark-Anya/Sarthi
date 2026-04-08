<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>JEE Saarthi Bot — README</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@400;500&family=Nunito:wght@400;600;700&display=swap" rel="stylesheet"/>
<style>
:root {
  --bg:       #0a0d14;
  --surface:  #111520;
  --card:     #161c2d;
  --border:   #1f2a42;
  --accent1:  #5b8dee;
  --accent2:  #a78bfa;
  --accent3:  #34d399;
  --accent4:  #fb923c;
  --text:     #e2e8f0;
  --muted:    #64748b;
  --glow1: rgba(91,141,238,0.18);
  --glow2: rgba(167,139,250,0.12);
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html { scroll-behavior: smooth; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Nunito', sans-serif;
  line-height: 1.7;
  overflow-x: hidden;
}

/* ── NOISE OVERLAY ── */
body::before {
  content: '';
  position: fixed; inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");
  pointer-events: none; z-index: 0; opacity: .4;
}

/* ── ANIMATED GRADIENT BG ── */
.bg-gradient {
  position: fixed; inset: 0; z-index: -1;
  background:
    radial-gradient(ellipse 80% 60% at 20% 10%,  rgba(91,141,238,0.09) 0%, transparent 70%),
    radial-gradient(ellipse 60% 50% at 80% 80%,  rgba(167,139,250,0.07) 0%, transparent 70%),
    radial-gradient(ellipse 50% 40% at 50% 50%,  rgba(52,211,153,0.04) 0%, transparent 60%),
    var(--bg);
  animation: bgPulse 12s ease-in-out infinite alternate;
}
@keyframes bgPulse {
  0%   { opacity: 1; }
  100% { opacity: 0.7; }
}

/* ── SCROLL REVEAL ── */
.reveal {
  opacity: 0;
  transform: translateY(40px);
  transition: opacity 0.7s cubic-bezier(.22,1,.36,1), transform 0.7s cubic-bezier(.22,1,.36,1);
}
.reveal.visible {
  opacity: 1;
  transform: translateY(0);
}
.reveal-left  { transform: translateX(-40px); }
.reveal-right { transform: translateX(40px); }
.reveal-left.visible, .reveal-right.visible { transform: translateX(0); }
.delay-1 { transition-delay: 0.1s; }
.delay-2 { transition-delay: 0.2s; }
.delay-3 { transition-delay: 0.3s; }
.delay-4 { transition-delay: 0.4s; }
.delay-5 { transition-delay: 0.5s; }

/* ── LAYOUT ── */
.container { max-width: 900px; margin: 0 auto; padding: 0 24px; position: relative; z-index: 1; }

/* ── HERO ── */
.hero {
  min-height: 100vh;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  text-align: center; padding: 60px 24px;
  position: relative;
}
.hero::after {
  content: '';
  position: absolute; bottom: 0; left: 50%; transform: translateX(-50%);
  width: 1px; height: 80px;
  background: linear-gradient(to bottom, var(--accent1), transparent);
  animation: lineGrow 1.5s ease-out 1s both;
}
@keyframes lineGrow { from { height: 0; opacity: 0; } to { height: 80px; opacity: 1; } }

.logo-wrap {
  position: relative; margin-bottom: 28px;
  animation: logoFloat 3s ease-in-out infinite;
}
@keyframes logoFloat {
  0%, 100% { transform: translateY(0px); }
  50%       { transform: translateY(-10px); }
}
.logo-ring {
  position: absolute; inset: -12px;
  border-radius: 50%;
  border: 1.5px solid transparent;
  background: linear-gradient(135deg, var(--accent1), var(--accent2)) border-box;
  -webkit-mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: destination-out;
  mask-composite: exclude;
  animation: ringRotate 8s linear infinite;
}
@keyframes ringRotate { to { transform: rotate(360deg); } }
.logo-svg {
  width: 100px; height: 100px;
  background: linear-gradient(135deg, var(--accent1), var(--accent2));
  border-radius: 28px;
  display: flex; align-items: center; justify-content: center;
  font-size: 48px;
  box-shadow: 0 0 40px rgba(91,141,238,0.35), 0 0 80px rgba(167,139,250,0.15);
  position: relative; z-index: 1;
}

.hero-badge {
  display: inline-flex; align-items: center; gap: 8px;
  background: rgba(91,141,238,0.1);
  border: 1px solid rgba(91,141,238,0.25);
  padding: 6px 16px; border-radius: 100px;
  font-family: 'DM Mono', monospace; font-size: 12px;
  color: var(--accent1); margin-bottom: 20px;
  animation: fadeSlide 0.6s ease-out 0.3s both;
}
@keyframes fadeSlide { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }

.hero h1 {
  font-family: 'Syne', sans-serif;
  font-size: clamp(2.8rem, 8vw, 5rem);
  font-weight: 800;
  line-height: 1.05;
  background: linear-gradient(135deg, #fff 0%, var(--accent2) 40%, var(--accent1) 80%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  animation: fadeSlide 0.7s ease-out 0.4s both;
}
.hero-sub {
  font-size: 1.15rem; color: var(--muted);
  max-width: 520px; margin: 16px auto 36px;
  animation: fadeSlide 0.7s ease-out 0.5s both;
}

/* ── BUTTONS CLUSTER ── */
.btn-cluster {
  display: flex; flex-wrap: wrap; gap: 10px;
  justify-content: center; margin-bottom: 12px;
  animation: fadeSlide 0.7s ease-out 0.6s both;
}
.btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 20px; border-radius: 10px;
  font-family: 'Nunito', sans-serif; font-weight: 700;
  font-size: 13px; text-decoration: none;
  transition: all 0.25s ease; cursor: pointer;
  border: none; position: relative; overflow: hidden;
}
.btn::before {
  content: ''; position: absolute; inset: 0;
  background: rgba(255,255,255,0.06);
  opacity: 0; transition: opacity 0.2s;
}
.btn:hover::before { opacity: 1; }
.btn:hover { transform: translateY(-2px); }
.btn:active { transform: translateY(0px); }

.btn-primary {
  background: linear-gradient(135deg, var(--accent1), var(--accent2));
  color: #fff;
  box-shadow: 0 4px 20px rgba(91,141,238,0.35);
}
.btn-primary:hover { box-shadow: 0 6px 28px rgba(91,141,238,0.5); }

.btn-ghost {
  background: rgba(255,255,255,0.05);
  border: 1px solid var(--border);
  color: var(--text);
}
.btn-ghost:hover { border-color: var(--accent1); color: var(--accent1); }

.btn-green {
  background: rgba(52,211,153,0.12);
  border: 1px solid rgba(52,211,153,0.3);
  color: var(--accent3);
}
.btn-green:hover { background: rgba(52,211,153,0.2); }

.btn-orange {
  background: rgba(251,146,60,0.12);
  border: 1px solid rgba(251,146,60,0.3);
  color: var(--accent4);
}
.btn-orange:hover { background: rgba(251,146,60,0.2); }

.btn-purple {
  background: rgba(167,139,250,0.12);
  border: 1px solid rgba(167,139,250,0.3);
  color: var(--accent2);
}
.btn-purple:hover { background: rgba(167,139,250,0.2); }

.btn-icon { font-size: 16px; }

/* ── STATS ROW ── */
.stats-row {
  display: flex; flex-wrap: wrap; gap: 16px;
  justify-content: center; margin: 48px 0 0;
}
.stat-pill {
  display: flex; flex-direction: column; align-items: center;
  background: var(--card); border: 1px solid var(--border);
  padding: 16px 28px; border-radius: 14px;
  min-width: 110px;
}
.stat-num {
  font-family: 'Syne', sans-serif; font-size: 1.8rem; font-weight: 800;
  background: linear-gradient(135deg, var(--accent1), var(--accent2));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.stat-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; }

/* ── SECTION ── */
section { padding: 80px 0; }
.section-tag {
  font-family: 'DM Mono', monospace; font-size: 11px;
  color: var(--accent1); text-transform: uppercase; letter-spacing: 2px;
  margin-bottom: 10px;
}
.section-title {
  font-family: 'Syne', sans-serif; font-size: clamp(1.8rem, 4vw, 2.6rem);
  font-weight: 800; margin-bottom: 14px;
}
.section-desc { color: var(--muted); max-width: 560px; }

/* ── FEATURE GRID ── */
.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px; margin-top: 40px;
}
.feature-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 16px; padding: 24px;
  transition: all 0.3s ease;
  position: relative; overflow: hidden;
}
.feature-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, var(--accent1), var(--accent2));
  transform: scaleX(0); transform-origin: left;
  transition: transform 0.3s ease;
}
.feature-card:hover { border-color: rgba(91,141,238,0.3); transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.3); }
.feature-card:hover::before { transform: scaleX(1); }

.feature-icon {
  font-size: 28px; margin-bottom: 12px;
  display: inline-flex; align-items: center; justify-content: center;
  width: 52px; height: 52px;
  background: rgba(91,141,238,0.1); border-radius: 12px;
}
.feature-title { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 1rem; margin-bottom: 6px; }
.feature-desc { font-size: 13px; color: var(--muted); line-height: 1.6; }

/* ── COMMANDS TABLE ── */
.cmd-table { margin-top: 32px; }
.cmd-row {
  display: flex; align-items: center; gap: 16px;
  padding: 14px 20px; border-radius: 12px;
  border: 1px solid transparent;
  transition: all 0.2s ease;
  margin-bottom: 8px;
}
.cmd-row:hover { background: var(--card); border-color: var(--border); }
.cmd-code {
  font-family: 'DM Mono', monospace; font-size: 14px;
  color: var(--accent3); background: rgba(52,211,153,0.08);
  padding: 4px 12px; border-radius: 6px; min-width: 130px;
  border: 1px solid rgba(52,211,153,0.15);
}
.cmd-desc { color: var(--muted); font-size: 14px; }

/* ── DEPLOY SECTION ── */
.deploy-tabs {
  display: flex; gap: 8px; flex-wrap: wrap; margin: 32px 0 0;
}
.deploy-tab {
  padding: 9px 20px; border-radius: 8px; cursor: pointer;
  font-family: 'Syne', sans-serif; font-weight: 700; font-size: 13px;
  border: 1px solid var(--border); color: var(--muted);
  background: var(--card); transition: all 0.25s ease;
  user-select: none;
}
.deploy-tab:hover { border-color: var(--accent1); color: var(--text); }
.deploy-tab.active { background: linear-gradient(135deg, var(--accent1), var(--accent2)); color: #fff; border-color: transparent; }

.deploy-panels { margin-top: 20px; }
.deploy-panel { display: none; animation: panelIn 0.4s ease; }
.deploy-panel.active { display: block; }
@keyframes panelIn { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }

.deploy-card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 16px; padding: 28px; position: relative; overflow: hidden;
}
.deploy-card::after {
  content: ''; position: absolute; top: -40px; right: -40px;
  width: 160px; height: 160px; border-radius: 50%;
  background: radial-gradient(circle, var(--glow1), transparent 70%);
  pointer-events: none;
}
.deploy-platform {
  display: flex; align-items: center; gap: 12px; margin-bottom: 20px;
}
.platform-icon {
  width: 44px; height: 44px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; background: rgba(255,255,255,0.06);
  border: 1px solid var(--border);
}
.platform-name {
  font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1.2rem;
}
.platform-tag {
  font-size: 11px; color: var(--accent3);
  background: rgba(52,211,153,0.1); padding: 2px 8px;
  border-radius: 100px; border: 1px solid rgba(52,211,153,0.2);
  font-family: 'DM Mono', monospace;
}

/* ── CODE BLOCK ── */
.code-block {
  background: #0d1117; border: 1px solid var(--border);
  border-radius: 12px; padding: 20px; margin: 16px 0;
  position: relative; overflow: hidden;
}
.code-block-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 14px; padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}
.code-dots { display: flex; gap: 6px; }
.dot { width: 12px; height: 12px; border-radius: 50%; }
.dot-r { background: #ff5f57; }
.dot-y { background: #ffbd2e; }
.dot-g { background: #28c840; }
.code-lang { font-family: 'DM Mono', monospace; font-size: 11px; color: var(--muted); }
.copy-btn {
  background: rgba(255,255,255,0.06); border: 1px solid var(--border);
  color: var(--muted); padding: 4px 12px; border-radius: 6px;
  font-size: 11px; cursor: pointer; transition: all 0.2s;
  font-family: 'DM Mono', monospace;
}
.copy-btn:hover { color: var(--text); border-color: var(--accent1); }
pre {
  font-family: 'DM Mono', monospace; font-size: 13px;
  color: #e6edf3; line-height: 1.7; overflow-x: auto;
  white-space: pre;
}
.kw { color: #ff7b72; }
.st { color: #a5d6ff; }
.cm { color: #8b949e; font-style: italic; }
.fn { color: #d2a8ff; }
.nm { color: #79c0ff; }
.op { color: #ff7b72; }

/* ── STEP FLOW ── */
.steps { margin-top: 24px; }
.step {
  display: flex; gap: 18px; margin-bottom: 20px;
  align-items: flex-start;
}
.step-num {
  width: 36px; height: 36px; border-radius: 10px; flex-shrink: 0;
  background: linear-gradient(135deg, var(--accent1), var(--accent2));
  display: flex; align-items: center; justify-content: center;
  font-family: 'Syne', sans-serif; font-weight: 800; font-size: 14px;
}
.step-content h4 { font-family: 'Syne', sans-serif; font-weight: 700; margin-bottom: 4px; }
.step-content p { font-size: 14px; color: var(--muted); }

/* ── FILE TREE ── */
.file-tree {
  background: #0d1117; border: 1px solid var(--border);
  border-radius: 12px; padding: 20px;
  font-family: 'DM Mono', monospace; font-size: 13px;
  line-height: 2;
}
.tree-dir { color: var(--accent1); }
.tree-file { color: var(--text); }
.tree-comment { color: var(--muted); }

/* ── DIVIDER ── */
.divider {
  height: 1px; background: linear-gradient(90deg, transparent, var(--border), transparent);
  margin: 0;
}

/* ── AUTHOR SECTION ── */
.author-card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 20px; padding: 36px; margin-top: 40px;
  display: flex; gap: 28px; align-items: center; flex-wrap: wrap;
  position: relative; overflow: hidden;
}
.author-card::before {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(135deg, rgba(91,141,238,0.04), rgba(167,139,250,0.04));
}
.author-avatar {
  width: 80px; height: 80px; border-radius: 20px;
  background: linear-gradient(135deg, var(--accent1), var(--accent2));
  display: flex; align-items: center; justify-content: center;
  font-size: 36px; flex-shrink: 0;
  box-shadow: 0 0 30px rgba(91,141,238,0.3);
  position: relative; z-index: 1;
}
.author-info { flex: 1; position: relative; z-index: 1; }
.author-name {
  font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1.5rem;
  background: linear-gradient(135deg, #fff, var(--accent2));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.author-handle { color: var(--accent1); font-family: 'DM Mono', monospace; font-size: 14px; margin: 4px 0 14px; }
.author-links { display: flex; gap: 10px; flex-wrap: wrap; }

/* ── FOOTER ── */
footer {
  text-align: center; padding: 48px 24px;
  border-top: 1px solid var(--border);
  position: relative; z-index: 1;
}
.footer-logo { font-family: 'Syne', sans-serif; font-size: 1.4rem; font-weight: 800; margin-bottom: 8px; }
.footer-sub { font-size: 13px; color: var(--muted); }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent1); }

/* ── RESPONSIVE ── */
@media (max-width: 600px) {
  .author-card { flex-direction: column; }
  .btn-cluster { gap: 8px; }
  .btn { font-size: 12px; padding: 8px 14px; }
}

/* ── INLINE CODE ── */
code {
  font-family: 'DM Mono', monospace;
  background: rgba(91,141,238,0.1); color: var(--accent1);
  padding: 2px 8px; border-radius: 5px; font-size: 13px;
}

/* ── HIGHLIGHT TAG ── */
.hl { color: var(--accent1); }
.hl2 { color: var(--accent2); }
.hl3 { color: var(--accent3); }

/* progress bar decorative */
.progress-wrap { margin-top: 40px; }
.prog-row { display: flex; align-items: center; gap: 14px; margin-bottom: 14px; }
.prog-label { font-size: 13px; color: var(--muted); min-width: 130px; }
.prog-bar-bg { flex: 1; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
.prog-bar-fill {
  height: 100%; border-radius: 3px;
  background: linear-gradient(90deg, var(--accent1), var(--accent2));
  transform: scaleX(0); transform-origin: left;
  transition: transform 1s cubic-bezier(.22,1,.36,1);
}
.prog-bar-fill.animated { transform: scaleX(1); }
.prog-val { font-family: 'DM Mono', monospace; font-size: 12px; color: var(--accent2); min-width: 40px; text-align: right; }
</style>
</head>
<body>

<div class="bg-gradient"></div>

<!-- ══════════════════════════════════════════════
     HERO
═══════════════════════════════════════════════ -->
<section class="hero">
  <div class="hero-badge">
    <span>🤖</span> Telegram Bot · Python · Open Source
  </div>

  <div class="logo-wrap">
    <div class="logo-ring"></div>
    <div class="logo-svg">🎓</div>
  </div>

  <h1>JEE Saarthi</h1>
  <p class="hero-sub">
    Your AI-powered study companion for JEE & NEET — tasks, memories, formulas, books, PYQs, stats &amp; more. All inside Telegram.
  </p>

  <!-- ── BUTTON CLUSTER ── -->
  <div class="btn-cluster">
    <a href="https://t.me/JeeSarthi_bot" class="btn btn-primary" target="_blank">
      <span class="btn-icon">🚀</span> Try Live Demo
    </a>
    <a href="https://t.me/CarelessxWorld" class="btn btn-ghost" target="_blank">
      <span class="btn-icon">💬</span> Support
    </a>
    <a href="https://t.me/CarelessxCoder" class="btn btn-purple" target="_blank">
      <span class="btn-icon">📢</span> Updates
    </a>
    <a href="https://t.me/Anya_Bots" class="btn btn-green" target="_blank">
      <span class="btn-icon">🤖</span> More Bots
    </a>
    <a href="https://t.me/carelessxowner" class="btn btn-orange" target="_blank">
      <span class="btn-icon">👤</span> Developer
    </a>
  </div>
  <div class="btn-cluster">
    <a href="#features" class="btn btn-ghost" onclick="scrollTo('#features')">
      <span class="btn-icon">✨</span> Features
    </a>
    <a href="#deploy" class="btn btn-ghost">
      <span class="btn-icon">🚀</span> Deploy Guide
    </a>
    <a href="#structure" class="btn btn-ghost">
      <span class="btn-icon">📁</span> File Structure
    </a>
    <a href="#commands" class="btn btn-ghost">
      <span class="btn-icon">⌨️</span> Commands
    </a>
    <a href="#author" class="btn btn-ghost">
      <span class="btn-icon">🧑‍💻</span> About Dev
    </a>
  </div>

  <!-- Stats row -->
  <div class="stats-row">
    <div class="stat-pill reveal delay-1">
      <span class="stat-num">16</span>
      <span class="stat-label">Python Files</span>
    </div>
    <div class="stat-pill reveal delay-2">
      <span class="stat-num">5100+</span>
      <span class="stat-label">Lines of Code</span>
    </div>
    <div class="stat-pill reveal delay-3">
      <span class="stat-num">12</span>
      <span class="stat-label">DB Tables</span>
    </div>
    <div class="stat-pill reveal delay-4">
      <span class="stat-num">50+</span>
      <span class="stat-label">Features</span>
    </div>
    <div class="stat-pill reveal delay-5">
      <span class="stat-num">6</span>
      <span class="stat-label">Scheduled Jobs</span>
    </div>
  </div>
</section>

<div class="divider"></div>

<!-- ══════════════════════════════════════════════
     FEATURES
═══════════════════════════════════════════════ -->
<section id="features">
  <div class="container">
    <p class="section-tag reveal">What's Inside</p>
    <h2 class="section-title reveal">Everything a JEE Aspirant Needs</h2>
    <p class="section-desc reveal">Built from scratch with one goal — make your study life organized, tracked, and motivated.</p>

    <div class="feature-grid">

      <div class="feature-card reveal delay-1">
        <div class="feature-icon">📅</div>
        <div class="feature-title">Today Dashboard</div>
        <div class="feature-desc">Add tasks with subject prefixes, toggle done, focus timer (15/25/50 min), test scores, doubts, revisions — all in one place.</div>
      </div>

      <div class="feature-card reveal delay-2">
        <div class="feature-icon">🧠</div>
        <div class="feature-title">Smart Memories</div>
        <div class="feature-desc">Save Silly mistakes, Errors, Important concepts — with title, content (photo/text), answer, and key points. Browse history anytime.</div>
      </div>

      <div class="feature-card reveal delay-3">
        <div class="feature-icon">📚</div>
        <div class="feature-title">Materials Library</div>
        <div class="feature-desc">Class-wise Books (Class 11/12), Formulas, PYQs (JEE Mains/Adv/NEET), and 11&12 Mix books — all with inline navigation.</div>
      </div>

      <div class="feature-card reveal delay-4">
        <div class="feature-icon">📊</div>
        <div class="feature-title">Progress Stats</div>
        <div class="feature-desc">Weekly, Monthly and All-Time dashboard — study hours, subject breakdown with bars, streak graph, test score trends, and improvement tracking.</div>
      </div>

      <div class="feature-card reveal delay-5">
        <div class="feature-icon">🔄</div>
        <div class="feature-title">Spaced Revision</div>
        <div class="feature-desc">Mark a lecture as watched → auto-schedule revisions at 1 day, 3 days, 7 days, 30 days. Daily reminder at 9 AM.</div>
      </div>

      <div class="feature-card reveal">
        <div class="feature-icon">🎯</div>
        <div class="feature-title">Lecture Manager</div>
        <div class="feature-desc">Save lecture links with alert times, subject, and custom messages. Get pinged at exact time with Open Link, Mark Watched, Snooze buttons.</div>
      </div>

      <div class="feature-card reveal delay-1">
        <div class="feature-icon">🔍</div>
        <div class="feature-title">Universal Search</div>
        <div class="feature-desc"><code>/search query</code> — searches across memories, daily reports, formulas, books, PYQs, mix books all at once. Delete directly from results.</div>
      </div>

      <div class="feature-card reveal delay-2">
        <div class="feature-icon">🛡️</div>
        <div class="feature-title">Admin Panel</div>
        <div class="feature-desc">Password-based access for anyone. Upload formulas, books, PYQs with multiple PDFs. Edit titles, delete content, broadcast, manage users.</div>
      </div>

      <div class="feature-card reveal delay-3">
        <div class="feature-icon">🔔</div>
        <div class="feature-title">Smart Reminders</div>
        <div class="feature-desc">6 AM morning message with streak, 8 PM doubt reminder (if pending 2+ days), 9 AM revision alert, Sunday weekly report, 7 AM formula flash.</div>
      </div>

      <div class="feature-card reveal delay-4">
        <div class="feature-icon">🗄️</div>
        <div class="feature-title">Daily DB Backup</div>
        <div class="feature-desc">Entire SQLite database automatically sent to admin at 11 PM every day. Never lose your data.</div>
      </div>

      <div class="feature-card reveal delay-5">
        <div class="feature-icon">💭</div>
        <div class="feature-title">Thoughts & Motivation</div>
        <div class="feature-desc">Private vaults for random thoughts and motivational quotes/images. Navigate, add, delete — all inline.</div>
      </div>

      <div class="feature-card reveal">
        <div class="feature-icon">📒</div>
        <div class="feature-title">Daily Reports</div>
        <div class="feature-desc">Write today's study report (text or photo). View & update anytime. Browse all past reports with navigation.</div>
      </div>

    </div>

    <!-- Progress bars -->
    <div class="progress-wrap reveal">
      <h3 style="font-family:'Syne',sans-serif; font-weight:700; margin-bottom:20px; font-size:1.1rem;">Tech Stack Coverage</h3>
      <div class="prog-row"><span class="prog-label">Python 3.11+</span><div class="prog-bar-bg"><div class="prog-bar-fill" data-w="1"></div></div><span class="prog-val">100%</span></div>
      <div class="prog-row"><span class="prog-label">python-telegram-bot</span><div class="prog-bar-bg"><div class="prog-bar-fill" data-w="1"></div></div><span class="prog-val">100%</span></div>
      <div class="prog-row"><span class="prog-label">SQLite (WAL)</span><div class="prog-bar-bg"><div class="prog-bar-fill" data-w="1"></div></div><span class="prog-val">100%</span></div>
      <div class="prog-row"><span class="prog-label">APScheduler (IST)</span><div class="prog-bar-bg"><div class="prog-bar-fill" data-w="0.9"></div></div><span class="prog-val">90%</span></div>
      <div class="prog-row"><span class="prog-label">Inline Keyboards</span><div class="prog-bar-bg"><div class="prog-bar-fill" data-w="0.95"></div></div><span class="prog-val">95%</span></div>
    </div>
  </div>
</section>

<div class="divider"></div>

<!-- ══════════════════════════════════════════════
     COMMANDS
═══════════════════════════════════════════════ -->
<section id="commands">
  <div class="container">
    <p class="section-tag reveal">Bot Commands</p>
    <h2 class="section-title reveal">Simple. Powerful.</h2>
    <p class="section-desc reveal">Only a few commands — everything else is inline buttons. Clean and fast.</p>

    <div class="cmd-table">
      <div class="cmd-row reveal delay-1"><span class="cmd-code">/start</span><span class="cmd-desc">Launch the bot, see home screen with streak and date</span></div>
      <div class="cmd-row reveal delay-2"><span class="cmd-code">/stats</span><span class="cmd-desc">Open your personal progress dashboard — weekly, monthly, all-time</span></div>
      <div class="cmd-row reveal delay-3"><span class="cmd-code">/search &lt;query&gt;</span><span class="cmd-desc">Search across all memories, books, formulas, PYQs instantly</span></div>
      <div class="cmd-row reveal delay-4"><span class="cmd-code">/ban &lt;user_id&gt;</span><span class="cmd-desc">Admin — ban a user from the bot</span></div>
      <div class="cmd-row reveal delay-5"><span class="cmd-code">/unban &lt;user_id&gt;</span><span class="cmd-desc">Admin — unban a user and notify them</span></div>
    </div>
  </div>
</section>

<div class="divider"></div>

<!-- ══════════════════════════════════════════════
     FILE STRUCTURE
═══════════════════════════════════════════════ -->
<section id="structure">
  <div class="container">
    <p class="section-tag reveal">Project Structure</p>
    <h2 class="section-title reveal">Clean Architecture</h2>
    <p class="section-desc reveal">Every module has a single responsibility. Easy to extend, easy to debug.</p>

    <div class="file-tree reveal" style="margin-top:32px;">
<pre>
<span class="tree-dir">jee_saarthi/</span>
├── <span class="tree-file">bot.py</span>             <span class="tree-comment"># Entry point — all ConversationHandlers registered</span>
├── <span class="tree-file">config.py</span>          <span class="tree-comment"># BOT_TOKEN, ADMIN_PASS, DB_CLEAR_PASS, TIMEZONE</span>
├── <span class="tree-file">database.py</span>        <span class="tree-comment"># 12 tables, helper functions, init_db()</span>
├── <span class="tree-file">ui.py</span>              <span class="tree-comment"># Centralized keyboard builders</span>
├── <span class="tree-file">scheduler.py</span>       <span class="tree-comment"># 6 APScheduler jobs (IST timezone)</span>
├── <span class="tree-file">requirements.txt</span>
└── <span class="tree-dir">handlers/</span>
    ├── <span class="tree-file">common.py</span>      <span class="tree-comment"># /start, home_callback, ban/unban, check_banned</span>
    ├── <span class="tree-file">today.py</span>       <span class="tree-comment"># Tasks, Lectures, Timer, Scores, Doubts, Revisions</span>
    ├── <span class="tree-file">memories.py</span>    <span class="tree-comment"># Silly / Error / Important + Daily Report</span>
    ├── <span class="tree-file">materials.py</span>   <span class="tree-comment"># Books, Formulas, PYQs, Mix — with pagination</span>
    ├── <span class="tree-file">formulas.py</span>    <span class="tree-comment"># Formula viewer: Class → Subject → Chapter</span>
    ├── <span class="tree-file">motivation.py</span>  <span class="tree-comment"># Motivation + Thoughts vault (add/view/delete)</span>
    ├── <span class="tree-file">thought.py</span>     <span class="tree-comment"># Re-exports from motivation.py</span>
    ├── <span class="tree-file">stats.py</span>       <span class="tree-comment"># /stats — weekly/monthly/alltime dashboard + log</span>
    ├── <span class="tree-file">search.py</span>      <span class="tree-comment"># /search — universal search with delete</span>
    └── <span class="tree-file">admin.py</span>       <span class="tree-comment"># Admin panel: upload/edit/delete/broadcast/stats</span>
</pre>
    </div>
  </div>
</section>

<div class="divider"></div>

<!-- ══════════════════════════════════════════════
     DEPLOY
═══════════════════════════════════════════════ -->
<section id="deploy">
  <div class="container">
    <p class="section-tag reveal">Deployment</p>
    <h2 class="section-title reveal">Deploy in Minutes</h2>
    <p class="section-desc reveal">Choose your preferred platform. All methods work — pick what suits your budget and use case.</p>

    <!-- Setup first -->
    <div class="deploy-card reveal" style="margin-top:32px; margin-bottom:32px;">
      <h3 style="font-family:'Syne',sans-serif; font-weight:800; margin-bottom:16px;">⚙️ First: Configure <code>config.py</code></h3>
      <div class="code-block">
        <div class="code-block-header">
          <div class="code-dots"><div class="dot dot-r"></div><div class="dot dot-y"></div><div class="dot dot-g"></div></div>
          <span class="code-lang">config.py</span>
          <button class="copy-btn" onclick="copyCode(this)">Copy</button>
        </div>
        <pre><span class="nm">BOT_TOKEN</span>      <span class="op">=</span> <span class="st">"your_bot_token_here"</span>       <span class="cm"># From @BotFather</span>
<span class="nm">ADMIN_ID</span>       <span class="op">=</span> <span class="nm">123456789</span>                  <span class="cm"># Your Telegram user ID</span>
<span class="nm">ADMIN_PASS</span>     <span class="op">=</span> <span class="st">"your_admin_password"</span>       <span class="cm"># Admin panel password</span>
<span class="nm">DB_CLEAR_PASS</span>  <span class="op">=</span> <span class="st">"your_db_clear_password"</span>    <span class="cm"># Separate clear DB password</span>
<span class="nm">DB_PATH</span>        <span class="op">=</span> <span class="st">"jee_saarthi.db"</span>
<span class="nm">TIMEZONE</span>       <span class="op">=</span> <span class="st">"Asia/Kolkata"</span></pre>
      </div>
    </div>

    <!-- DEPLOY TABS -->
    <div class="deploy-tabs reveal">
      <div class="deploy-tab active" onclick="switchTab('vps')">🖥️ VPS / Ubuntu</div>
      <div class="deploy-tab" onclick="switchTab('render')">🌐 Render</div>
      <div class="deploy-tab" onclick="switchTab('railway')">🚂 Railway</div>
      <div class="deploy-tab" onclick="switchTab('koyeb')">⚡ Koyeb</div>
      <div class="deploy-tab" onclick="switchTab('heroku')">🟣 Heroku</div>
    </div>

    <div class="deploy-panels">

      <!-- VPS -->
      <div class="deploy-panel active" id="panel-vps">
        <div class="deploy-card">
          <div class="deploy-platform">
            <div class="platform-icon">🖥️</div>
            <div>
              <div class="platform-name">VPS / Ubuntu Server</div>
              <span class="platform-tag">Recommended · Full Control</span>
            </div>
          </div>
          <div class="steps">
            <div class="step">
              <div class="step-num">1</div>
              <div class="step-content">
                <h4>SSH into your server &amp; install dependencies</h4>
                <p>Connect to your VPS and set up Python environment</p>
              </div>
            </div>
          </div>
          <div class="code-block">
            <div class="code-block-header">
              <div class="code-dots"><div class="dot dot-r"></div><div class="dot dot-y"></div><div class="dot dot-g"></div></div>
              <span class="code-lang">bash</span>
              <button class="copy-btn" onclick="copyCode(this)">Copy</button>
            </div>
            <pre><span class="cm"># Update & install Python</span>
<span class="kw">sudo</span> apt update <span class="op">&amp;&amp;</span> <span class="kw">sudo</span> apt install -y python3.11 python3-pip git screen

<span class="cm"># Clone / upload your project</span>
<span class="kw">git</span> clone https://github.com/yourusername/jee-saarthi.git
<span class="kw">cd</span> jee-saarthi

<span class="cm"># Create virtual environment</span>
<span class="kw">python3</span> -m venv myenv
<span class="kw">source</span> myenv/bin/activate

<span class="cm"># Install requirements</span>
<span class="kw">pip</span> install -r requirements.txt

<span class="cm"># Edit config.py with your credentials</span>
<span class="kw">nano</span> config.py</pre>
          </div>
          <div class="steps">
            <div class="step">
              <div class="step-num">2</div>
              <div class="step-content">
                <h4>Run with screen (keeps bot alive after SSH disconnect)</h4>
              </div>
            </div>
          </div>
          <div class="code-block">
            <div class="code-block-header">
              <div class="code-dots"><div class="dot dot-r"></div><div class="dot dot-y"></div><div class="dot dot-g"></div></div>
              <span class="code-lang">bash</span>
              <button class="copy-btn" onclick="copyCode(this)">Copy</button>
            </div>
            <pre><span class="cm"># Start in screen session</span>
<span class="kw">screen</span> -S jeebot
<span class="kw">python</span> bot.py

<span class="cm"># Detach: Ctrl+A then D</span>
<span class="cm"># Reattach later: screen -r jeebot</span></pre>
          </div>
          <div class="steps">
            <div class="step">
              <div class="step-num">3</div>
              <div class="step-content">
                <h4>Optional: systemd service for auto-restart</h4>
              </div>
            </div>
          </div>
          <div class="code-block">
            <div class="code-block-header">
              <div class="code-dots"><div class="dot dot-r"></div><div class="dot dot-y"></div><div class="dot dot-g"></div></div>
              <span class="code-lang">bash</span>
              <button class="copy-btn" onclick="copyCode(this)">Copy</button>
            </div>
            <pre><span class="cm"># Create service file</span>
<span class="kw">sudo</span> nano /etc/systemd/system/jeebot.service

<span class="cm"># Paste this inside:</span>
[Unit]
Description=JEE Saarthi Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/jee-saarthi
ExecStart=/home/ubuntu/jee-saarthi/myenv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

<span class="cm"># Enable & start</span>
<span class="kw">sudo</span> systemctl daemon-reload
<span class="kw">sudo</span> systemctl enable jeebot
<span class="kw">sudo</span> systemctl start jeebot
<span class="kw">sudo</span> systemctl status jeebot</pre>
          </div>
        </div>
      </div>

      <!-- RENDER -->
      <div class="deploy-panel" id="panel-render">
        <div class="deploy-card">
          <div class="deploy-platform">
            <div class="platform-icon">🌐</div>
            <div>
              <div class="platform-name">Render</div>
              <span class="platform-tag">Free Tier Available · Easy Setup</span>
            </div>
          </div>
          <div class="steps">
            <div class="step"><div class="step-num">1</div><div class="step-content"><h4>Create a <code>render.yaml</code> in your project root</h4></div></div>
          </div>
          <div class="code-block">
            <div class="code-block-header">
              <div class="code-dots"><div class="dot dot-r"></div><div class="dot dot-y"></div><div class="dot dot-g"></div></div>
              <span class="code-lang">render.yaml</span>
              <button class="copy-btn" onclick="copyCode(this)">Copy</button>
            </div>
            <pre>services:
  - type: worker
    name: jee-saarthi-bot
    env: python
    buildCommand: <span class="st">"pip install -r requirements.txt"</span>
    startCommand: <span class="st">"python bot.py"</span>
    envVars:
      - key: BOT_TOKEN
        value: your_bot_token_here
      - key: ADMIN_ID
        value: <span class="st">"123456789"</span></pre>
          </div>
          <div class="steps">
            <div class="step"><div class="step-num">2</div><div class="step-content"><h4>Push to GitHub → Connect on Render dashboard → Add Environment Variables → Deploy</h4><p>Go to render.com → New → Background Worker → Connect repo → Set env vars → Create Service</p></div></div>
            <div class="step"><div class="step-num">3</div><div class="step-content"><h4>Add a persistent disk</h4><p>In Render dashboard: Disks → Add → Mount Path: <code>/data</code> → Update <code>DB_PATH = "/data/jee_saarthi.db"</code> in config</p></div></div>
          </div>
        </div>
      </div>

      <!-- RAILWAY -->
      <div class="deploy-panel" id="panel-railway">
        <div class="deploy-card">
          <div class="deploy-platform">
            <div class="platform-icon">🚂</div>
            <div>
              <div class="platform-name">Railway</div>
              <span class="platform-tag">$5/mo · Super Fast Deploy</span>
            </div>
          </div>
          <div class="steps">
            <div class="step"><div class="step-num">1</div><div class="step-content"><h4>Create a <code>Procfile</code> in project root</h4></div></div>
          </div>
          <div class="code-block">
            <div class="code-block-header">
              <div class="code-dots"><div class="dot dot-r"></div><div class="dot dot-y"></div><div class="dot dot-g"></div></div>
              <span class="code-lang">Procfile</span>
              <button class="copy-btn" onclick="copyCode(this)">Copy</button>
            </div>
            <pre>worker: python bot.py</pre>
          </div>
          <div class="steps">
            <div class="step"><div class="step-num">2</div><div class="step-content"><h4>Deploy via Railway CLI or GitHub</h4></div></div>
          </div>
          <div class="code-block">
            <div class="code-block-header">
              <div class="code-dots"><div class="dot dot-r"></div><div class="dot dot-y"></div><div class="dot dot-g"></div></div>
              <span class="code-lang">bash</span>
              <button class="copy-btn" onclick="copyCode(this)">Copy</button>
            </div>
            <pre><span class="cm"># Install Railway CLI</span>
<span class="kw">npm</span> i -g @railway/cli

<span class="cm"># Login & deploy</span>
<span class="kw">railway</span> login
<span class="kw">railway</span> init
<span class="kw">railway</span> up

<span class="cm"># Set environment variables</span>
<span class="kw">railway</span> variables set BOT_TOKEN=your_token
<span class="kw">railway</span> variables set ADMIN_ID=123456789</pre>
          </div>
          <div class="steps">
            <div class="step"><div class="step-num">3</div><div class="step-content"><h4>Add Volume for SQLite persistence</h4><p>Dashboard → Add Volume → Mount at <code>/app/data</code> → Set <code>DB_PATH = "/app/data/jee_saarthi.db"</code></p></div></div>
          </div>
        </div>
      </div>

      <!-- KOYEB -->
      <div class="deploy-panel" id="panel-koyeb">
        <div class="deploy-card">
          <div class="deploy-platform">
            <div class="platform-icon">⚡</div>
            <div>
              <div class="platform-name">Koyeb</div>
              <span class="platform-tag">Free Tier · Global Edge</span>
            </div>
          </div>
          <div class="steps">
            <div class="step"><div class="step-num">1</div><div class="step-content"><h4>Create <code>koyeb.yaml</code> in project root</h4></div></div>
          </div>
          <div class="code-block">
            <div class="code-block-header">
              <div class="code-dots"><div class="dot dot-r"></div><div class="dot dot-y"></div><div class="dot dot-g"></div></div>
              <span class="code-lang">koyeb.yaml</span>
              <button class="copy-btn" onclick="copyCode(this)">Copy</button>
            </div>
            <pre>name: jee-saarthi-bot
services:
  - name: bot
    type: worker
    git:
      repository: github.com/yourusername/jee-saarthi
      branch: main
    build:
      buildpack: python
    run:
      command: python bot.py
    env:
      - key: BOT_TOKEN
        value: your_bot_token
      - key: ADMIN_ID
        value: <span class="st">"123456789"</span></pre>
          </div>
          <div class="steps">
            <div class="step"><div class="step-num">2</div><div class="step-content"><h4>Go to koyeb.com → Create App → Connect GitHub → Select repo → Set env vars → Deploy</h4><p>Koyeb auto-detects Python and installs requirements.txt</p></div></div>
            <div class="step"><div class="step-num">3</div><div class="step-content"><h4>For SQLite persistence, use Koyeb Volumes</h4><p>Add a persistent volume and set <code>DB_PATH = "/mnt/data/jee_saarthi.db"</code></p></div></div>
          </div>
        </div>
      </div>

      <!-- HEROKU -->
      <div class="deploy-panel" id="panel-heroku">
        <div class="deploy-card">
          <div class="deploy-platform">
            <div class="platform-icon">🟣</div>
            <div>
              <div class="platform-name">Heroku</div>
              <span class="platform-tag">$7/mo · Eco Dyno</span>
            </div>
          </div>
          <div class="steps">
            <div class="step"><div class="step-num">1</div><div class="step-content"><h4>Create required files</h4></div></div>
          </div>
          <div class="code-block">
            <div class="code-block-header">
              <div class="code-dots"><div class="dot dot-r"></div><div class="dot dot-y"></div><div class="dot dot-g"></div></div>
              <span class="code-lang">Procfile</span>
              <button class="copy-btn" onclick="copyCode(this)">Copy</button>
            </div>
            <pre>worker: python bot.py</pre>
          </div>
          <div class="code-block">
            <div class="code-block-header">
              <div class="code-dots"><div class="dot dot-r"></div><div class="dot dot-y"></div><div class="dot dot-g"></div></div>
              <span class="code-lang">runtime.txt</span>
              <button class="copy-btn" onclick="copyCode(this)">Copy</button>
            </div>
            <pre>python-3.11.9</pre>
          </div>
          <div class="steps">
            <div class="step"><div class="step-num">2</div><div class="step-content"><h4>Deploy via Heroku CLI</h4></div></div>
          </div>
          <div class="code-block">
            <div class="code-block-header">
              <div class="code-dots"><div class="dot dot-r"></div><div class="dot dot-y"></div><div class="dot dot-g"></div></div>
              <span class="code-lang">bash</span>
              <button class="copy-btn" onclick="copyCode(this)">Copy</button>
            </div>
            <pre><span class="cm"># Login & create app</span>
<span class="kw">heroku</span> login
<span class="kw">heroku</span> create jee-saarthi-bot

<span class="cm"># Set environment variables</span>
<span class="kw">heroku</span> config:set BOT_TOKEN=your_bot_token
<span class="kw">heroku</span> config:set ADMIN_ID=123456789

<span class="cm"># Deploy</span>
<span class="kw">git</span> push heroku main

<span class="cm"># Scale worker dyno (no web dyno needed)</span>
<span class="kw">heroku</span> ps:scale web=0 worker=1

<span class="cm"># Check logs</span>
<span class="kw">heroku</span> logs --tail</pre>
          </div>
          <div class="steps">
            <div class="step"><div class="step-num">3</div><div class="step-content"><h4>⚠️ Important: Heroku has ephemeral filesystem</h4><p>SQLite won't persist between restarts. Use Heroku Postgres addon or backup DB regularly (already done via daily backup job to admin).</p></div></div>
          </div>
        </div>
      </div>

    </div><!-- /deploy-panels -->
  </div>
</section>

<div class="divider"></div>

<!-- ══════════════════════════════════════════════
     AUTHOR
═══════════════════════════════════════════════ -->
<section id="author">
  <div class="container">
    <p class="section-tag reveal">Developer</p>
    <h2 class="section-title reveal">Made with ❤️ by</h2>

    <div class="author-card reveal">
      <div class="author-avatar">🦾</div>
      <div class="author-info">
        <div class="author-name">Mister Stark</div>
        <div class="author-handle">@carelessxowner</div>
        <div class="author-links">
          <a href="https://t.me/carelessxowner" class="btn btn-primary btn-small" target="_blank" style="padding:7px 16px; font-size:12px;">
            <span>💬</span> Telegram
          </a>
          <a href="https://t.me/CarelessxWorld" class="btn btn-ghost btn-small" target="_blank" style="padding:7px 16px; font-size:12px;">
            <span>🌍</span> Support Group
          </a>
          <a href="https://t.me/CarelessxCoder" class="btn btn-purple btn-small" target="_blank" style="padding:7px 16px; font-size:12px;">
            <span>📢</span> Updates Channel
          </a>
          <a href="https://t.me/Anya_Bots" class="btn btn-green btn-small" target="_blank" style="padding:7px 16px; font-size:12px;">
            <span>🤖</span> More Bots
          </a>
          <a href="https://t.me/JeeSarthi_bot" class="btn btn-orange btn-small" target="_blank" style="padding:7px 16px; font-size:12px;">
            <span>🎓</span> Demo Bot
          </a>
        </div>
      </div>
    </div>
  </div>
</section>

<div class="divider"></div>

<!-- FOOTER -->
<footer>
  <div class="footer-logo">🎓 JEE Saarthi</div>
  <p class="footer-sub">Built with Python · python-telegram-bot · SQLite · APScheduler</p>
  <p class="footer-sub" style="margin-top:8px;">Made by <a href="https://t.me/carelessxowner" style="color:var(--accent1); text-decoration:none;">Mister Stark</a> · <a href="https://t.me/CarelessxWorld" style="color:var(--accent1); text-decoration:none;">Support</a> · <a href="https://t.me/Anya_Bots" style="color:var(--accent1); text-decoration:none;">More Bots</a></p>
</footer>

<script>
// ── SCROLL REVEAL ──
const observer = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('visible');
      // Animate progress bars
      e.target.querySelectorAll && e.target.querySelectorAll('.prog-bar-fill').forEach(b => {
        b.classList.add('animated');
      });
      observer.unobserve(e.target);
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

document.querySelectorAll('.reveal, .stat-pill').forEach(el => observer.observe(el));

// Also observe progress bars parent
document.querySelectorAll('.progress-wrap').forEach(el => {
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.querySelectorAll('.prog-bar-fill').forEach(b => {
          b.style.transform = `scaleX(${b.dataset.w || 1})`;
          b.style.transition = 'transform 1.2s cubic-bezier(.22,1,.36,1)';
        });
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.3 });
  io.observe(el);
});

// ── DEPLOY TABS ──
function switchTab(id) {
  document.querySelectorAll('.deploy-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.deploy-panel').forEach(p => p.classList.remove('active'));
  document.querySelector(`#panel-${id}`).classList.add('active');
  event.target.classList.add('active');
  // Smooth scroll to deploy section
  document.getElementById('deploy').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── COPY CODE ──
function copyCode(btn) {
  const pre = btn.closest('.code-block').querySelector('pre');
  const text = pre.innerText;
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.textContent;
    btn.textContent = 'Copied!';
    btn.style.color = 'var(--accent3)';
    setTimeout(() => { btn.textContent = orig; btn.style.color = ''; }, 1800);
  });
}

// ── STAGGER stat-pills on load ──
document.querySelectorAll('.stat-pill').forEach((el, i) => {
  el.style.transitionDelay = `${0.1 + i * 0.1}s`;
});
</script>
</body>
</html>
