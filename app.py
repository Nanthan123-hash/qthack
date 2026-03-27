import streamlit as st

try:
    from modes import show_classical_ui, show_quantum_ui, show_comparison_ui
except ImportError as _modes_err:
    _modes_err_msg = str(_modes_err)

    def show_classical_ui():
        st.error(f"modes.py could not be loaded: {_modes_err_msg}")

    def show_quantum_ui():
        st.error(f"modes.py could not be loaded: {_modes_err_msg}")

    def show_comparison_ui():
        st.error(f"modes.py could not be loaded: {_modes_err_msg}")

st.set_page_config(
    page_title="ADC Analyzer — QtHack04",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

for key, val in [("page","home"),("visited",set()),("classical_tab","standard")]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── DESIGN SYSTEM ─────────────────────────────────────────────────────────────
# Light-first, real CSS variables so dark mode actually works.
# Palette: warm white background, deep teal accent, charcoal text.
# Typography: Syne (geometric display) + DM Mono (code/numbers).
# Feel: research lab notebook — clean, confident, human.
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:ital,wght@0,400;0,500;1,400&family=DM+Sans:wght@400;500&display=swap');

/* ── CSS VARIABLES — light + dark ── */
:root {
  --c-bg:        #f5f4f0;
  --c-surface:   #ffffff;
  --c-surface2:  #f0ede8;
  --c-border:    #ddd9d2;
  --c-border2:   #c9c4bc;
  --c-text:      #1a1a18;
  --c-text2:     #4a4a46;
  --c-text3:     #8a8880;
  --c-teal:      #0d7377;
  --c-teal-lt:   #e6f4f4;
  --c-teal-dk:   #0a5a5e;
  --c-amber:     #c17d11;
  --c-amber-lt:  #fef3e2;
  --c-red:       #c0392b;
  --c-red-lt:    #fdecea;
  --c-green:     #1a7a4a;
  --c-green-lt:  #e8f5ee;
  --c-purple:    #6c3fc1;
  --c-purple-lt: #f0ebfb;
  --c-font-display: 'Syne', sans-serif;
  --c-font-mono:    'DM Mono', monospace;
  --c-font-body:    'DM Sans', sans-serif;
}

@media (prefers-color-scheme: dark) {
  :root {
    --c-bg:        #12120f;
    --c-surface:   #1c1c18;
    --c-surface2:  #252520;
    --c-border:    #2e2e28;
    --c-border2:   #3a3a32;
    --c-text:      #e8e6df;
    --c-text2:     #b0aea6;
    --c-text3:     #6a6860;
    --c-teal:      #14a3a8;
    --c-teal-lt:   #0d3335;
    --c-teal-dk:   #60d4d8;
    --c-amber:     #f0a030;
    --c-amber-lt:  #2a1f00;
    --c-red:       #e05545;
    --c-red-lt:    #2a0f0a;
    --c-green:     #3ab870;
    --c-green-lt:  #0a2018;
    --c-purple:    #a080e8;
    --c-purple-lt: #1a1030;
  }
}

/* ── Force Streamlit dark theme to use our dark variables ── */
[data-theme="dark"],
[data-theme="dark"] :root,
.stApp[data-theme="dark"] {
    --c-bg:        #12120f !important;
    --c-surface:   #1c1c18 !important;
    --c-surface2:  #252520 !important;
    --c-border:    #2e2e28 !important;
    --c-border2:   #3a3a32 !important;
    --c-text:      #e8e6df !important;
    --c-text2:     #b0aea6 !important;
    --c-text3:     #6a6860 !important;
    --c-teal:      #14a3a8 !important;
    --c-teal-lt:   #0d3335 !important;
    --c-amber:     #f0a030 !important;
    --c-green:     #3ab870 !important;
    --c-purple:    #a080e8 !important;
}

/* ── STREAMLIT OVERRIDES — theme-aware ── */
html, body,
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main, .block-container {
    background-color: var(--c-bg) !important;
    color: var(--c-text) !important;
    font-family: var(--c-font-body) !important;
}
[data-testid="stHeader"]   { background: var(--c-bg) !important; }
[data-testid="stSidebar"] > div {
    background: var(--c-surface) !important;
    border-right: 1px solid var(--c-border) !important;
}
[data-testid="stSidebar"] * { color: var(--c-text) !important; }

.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── TOP NAV BAR ── */
.topnav {
    display: flex; align-items: center; justify-content: space-between;
    height: 52px; background: var(--c-surface);
    border-bottom: 1px solid var(--c-border);
    padding: 0 28px;
    position: sticky; top: 0; z-index: 200;
}
.topnav-brand {
    display: flex; align-items: center; gap: 10px;
}
.topnav-logo {
    width: 28px; height: 28px;
    background: var(--c-teal); border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-family: var(--c-font-mono); font-size: 13px; font-weight: 500;
    color: #fff; letter-spacing: 0;
}
.topnav-title {
    font-family: var(--c-font-display);
    font-size: 15px; font-weight: 700;
    color: var(--c-text); letter-spacing: -.02em;
}
.topnav-sub {
    font-family: var(--c-font-mono);
    font-size: 10px; color: var(--c-text3); letter-spacing: .04em;
}
.topnav-right {
    display: flex; align-items: center; gap: 20px;
    font-family: var(--c-font-mono); font-size: 10px;
    color: var(--c-text3); letter-spacing: .04em; text-transform: uppercase;
}
.nav-badge {
    background: var(--c-teal-lt); color: var(--c-teal);
    border: 1px solid var(--c-teal); border-radius: 4px;
    padding: 2px 8px; font-size: 9px; font-weight: 500;
    font-family: var(--c-font-mono); letter-spacing: .06em;
}

/* ── PAGE BODY ── */
.page-body { padding: 28px 32px 40px; }

/* ── HERO SECTION ── */
.hero {
    display: grid;
    grid-template-columns: 1fr 320px;
    gap: 24px;
    margin-bottom: 28px;
    align-items: start;
}
.hero-left {}
.hero-eyebrow {
    font-family: var(--c-font-mono);
    font-size: 10px; letter-spacing: .12em; text-transform: uppercase;
    color: var(--c-teal); margin-bottom: 10px;
    display: flex; align-items: center; gap: 8px;
}
.hero-eyebrow::before {
    content: ''; display: inline-block;
    width: 20px; height: 1px; background: var(--c-teal);
}
.hero-h1 {
    font-family: var(--c-font-display);
    font-size: 38px; font-weight: 800; line-height: 1.1;
    color: var(--c-text); letter-spacing: -.03em;
    margin-bottom: 12px;
}
.hero-h1 em { color: var(--c-teal); font-style: normal; }
.hero-desc {
    font-family: var(--c-font-body);
    font-size: 14px; color: var(--c-text2); line-height: 1.7;
    max-width: 560px; margin-bottom: 20px;
}
.hero-stack {
    display: flex; flex-wrap: wrap; gap: 6px;
}
.stack-pill {
    font-family: var(--c-font-mono); font-size: 10px;
    padding: 4px 10px; border-radius: 4px;
    border: 1px solid var(--c-border2);
    color: var(--c-text2); background: var(--c-surface);
    letter-spacing: .04em;
}

/* ── FORMULA STRIP ── */
.formula-strip {
    background: var(--c-surface);
    border: 1px solid var(--c-border);
    border-left: 3px solid var(--c-teal);
    padding: 14px 18px;
    margin-bottom: 28px;
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 0 20px;
    align-items: center;
}
.fs-label {
    font-family: var(--c-font-mono);
    font-size: 9px; color: var(--c-teal); letter-spacing: .1em;
    text-transform: uppercase; white-space: nowrap;
}
.fs-row {
    display: flex; flex-wrap: wrap; gap: 0;
    overflow-x: auto; scrollbar-width: none;
}
.fs-row::-webkit-scrollbar { display: none; }
.fs-item {
    padding: 0 16px; border-right: 1px solid var(--c-border);
    white-space: nowrap; min-width: fit-content;
}
.fs-name {
    font-family: var(--c-font-mono); font-size: 8px;
    color: var(--c-text3); text-transform: uppercase;
    letter-spacing: .08em; display: block; margin-bottom: 2px;
}
.fs-val {
    font-family: var(--c-font-mono); font-size: 12px;
    color: var(--c-text); font-weight: 500;
}

/* ── 3 MODE CARDS — horizontal layout ── */
.mode-grid {
    display: flex;
    flex-direction: column;
    gap: 14px;
    margin-bottom: 28px;
}
.mode-card {
    background: var(--c-surface);
    border: 1px solid var(--c-border);
    border-radius: 10px;
    padding: 0;
    cursor: pointer;
    transition: border-color .18s, box-shadow .18s, transform .15s;
    position: relative; overflow: hidden;
    display: flex;
    flex-direction: row;
    align-items: stretch;
}
.mode-card:hover {
    border-color: var(--c-teal);
    box-shadow: 0 4px 18px rgba(13,115,119,.12);
    transform: translateY(-1px);
}
.mode-card-accent {
    width: 4px;
    min-height: 100%;
    flex-shrink: 0;
    border-radius: 10px 0 0 10px;
}
.mode-card-icon-col {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 72px;
    flex-shrink: 0;
    background: var(--c-surface2);
    border-right: 1px solid var(--c-border);
}
.mode-card-body {
    flex: 1;
    padding: 16px 20px;
}
.mode-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 6px;
}
.mode-num {
    font-family: var(--c-font-mono); font-size: 9px;
    color: var(--c-text3); letter-spacing: .1em;
    text-transform: uppercase;
    display: flex; align-items: center; gap: 10px;
}
.mode-icon { font-size: 28px; line-height: 1; }
.mode-title {
    font-family: var(--c-font-display);
    font-size: 17px; font-weight: 700;
    color: var(--c-text); letter-spacing: -.02em;
}
.mode-desc {
    font-family: var(--c-font-body);
    font-size: 12px; color: var(--c-text2);
    line-height: 1.6; margin-bottom: 10px;
}
.mode-tags { display: flex; flex-wrap: wrap; gap: 4px; }
.mode-tag {
    font-family: var(--c-font-mono); font-size: 9px;
    padding: 2px 7px; background: var(--c-surface2);
    border: 1px solid var(--c-border);
    color: var(--c-text3); border-radius: 3px;
    letter-spacing: .04em;
}
.mode-visited {
    font-family: var(--c-font-mono); font-size: 8px;
    color: var(--c-green); letter-spacing: .06em;
}
.mode-card-action {
    display: flex;
    align-items: center;
    padding: 0 20px;
    flex-shrink: 0;
    border-left: 1px solid var(--c-border);
    font-family: var(--c-font-mono); font-size: 11px;
    color: var(--c-teal); font-weight: 500;
    white-space: nowrap;
    gap: 6px;
}

/* ── REFERENCES + INFO COLUMNS ── */
.info-grid {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 16px; margin-bottom: 28px;
}
.info-box {
    background: var(--c-surface);
    border: 1px solid var(--c-border);
    border-radius: 8px; padding: 20px;
}
.info-box-title {
    font-family: var(--c-font-display);
    font-size: 13px; font-weight: 700;
    color: var(--c-text); margin-bottom: 14px;
    padding-bottom: 8px; border-bottom: 1px solid var(--c-border);
    letter-spacing: -.01em;
}
.ref-item {
    display: flex; gap: 10px; margin-bottom: 10px;
    align-items: flex-start;
}
.ref-num {
    font-family: var(--c-font-mono); font-size: 9px;
    color: var(--c-teal); min-width: 20px; padding-top: 1px;
}
.ref-text {
    font-family: var(--c-font-body); font-size: 11px;
    color: var(--c-text2); line-height: 1.5;
}
.ref-text strong { color: var(--c-text); font-weight: 500; }
.stat-row { display: flex; gap: 0; margin-bottom: 0; }
.stat-cell {
    flex: 1; padding: 10px 14px;
    border-right: 1px solid var(--c-border);
    text-align: center;
}
.stat-cell:last-child { border-right: none; }
.stat-val {
    font-family: var(--c-font-mono); font-size: 22px;
    font-weight: 500; color: var(--c-teal);
    display: block; margin-bottom: 3px;
}
.stat-lbl {
    font-family: var(--c-font-mono); font-size: 9px;
    color: var(--c-text3); text-transform: uppercase; letter-spacing: .08em;
}

/* ── GRAPH HEADING ── */
.graph-heading {
    background: var(--c-surface2);
    border: 1px solid var(--c-border);
    border-bottom: none;
    padding: 8px 14px;
    display: flex; align-items: center; justify-content: space-between;
}
.graph-heading-title {
    font-family: var(--c-font-mono); font-size: 11px;
    font-weight: 500; color: var(--c-text);
    letter-spacing: .02em;
}
.graph-heading-meta {
    font-family: var(--c-font-mono); font-size: 10px;
    color: var(--c-text3);
}
.graph-wrap {
    border: 1px solid var(--c-border);
    border-radius: 0 0 6px 6px;
    overflow: hidden;
    margin-bottom: 12px;
}

/* ── MODE PAGE ── */
.modepage-header {
    background: var(--c-surface);
    border-bottom: 1px solid var(--c-border);
    padding: 14px 28px 0;
}
.modepage-breadcrumb {
    font-family: var(--c-font-mono); font-size: 10px;
    color: var(--c-text3); letter-spacing: .04em;
    margin-bottom: 6px;
}
.modepage-title {
    font-family: var(--c-font-display);
    font-size: 24px; font-weight: 800;
    color: var(--c-text); letter-spacing: -.03em;
    margin-bottom: 10px;
}
.modepage-tab-strip {
    display: flex; gap: 0;
}

/* ── STREAMLIT WIDGETS — theme-aware ── */
[data-testid="stMetricValue"] {
    font-family: var(--c-font-mono) !important;
    font-size: 1.35rem !important;
    font-weight: 500 !important;
    color: var(--c-teal) !important;
}
[data-testid="stMetricLabel"] {
    font-family: var(--c-font-mono) !important;
    font-size: .68rem !important;
    color: var(--c-text3) !important;
    letter-spacing: .08em !important;
    text-transform: uppercase !important;
}
[data-testid="stTabs"] [role="tablist"] {
    background: var(--c-surface) !important;
    border-bottom: 1px solid var(--c-border) !important;
    gap: 0 !important;
}
[data-testid="stTabs"] button {
    font-family: var(--c-font-mono) !important;
    font-size: 10px !important;
    letter-spacing: .06em !important; text-transform: uppercase !important;
    color: var(--c-text3) !important;
    background: var(--c-surface) !important;
    border-right: 1px solid var(--c-border) !important;
    border-radius: 0 !important; padding: 10px 18px !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--c-teal) !important;
    background: var(--c-bg) !important;
    border-bottom: 2px solid var(--c-teal) !important;
    font-weight: 500 !important;
}
[data-testid="stTabs"] button:hover {
    color: var(--c-text) !important;
    background: var(--c-surface2) !important;
}
[data-testid="stExpander"] {
    background: var(--c-surface) !important;
    border: 1px solid var(--c-border) !important;
    border-radius: 6px !important;
}
[data-testid="stExpander"] summary {
    font-family: var(--c-font-mono) !important;
    font-size: 10px !important; color: var(--c-text2) !important;
    letter-spacing: .06em !important; text-transform: uppercase !important;
    background: var(--c-surface) !important; padding: 10px 14px !important;
}
[data-testid="stExpander"] summary:hover { color: var(--c-teal) !important; }
[data-testid="stButton"] > button {
    background: var(--c-surface) !important;
    border: 1px solid var(--c-border) !important;
    color: var(--c-text2) !important; border-radius: 6px !important;
    font-family: var(--c-font-mono) !important;
    font-size: 10px !important; letter-spacing: .06em !important;
    text-transform: uppercase !important; padding: 7px 14px !important;
    transition: all .15s !important;
}
[data-testid="stButton"] > button:hover {
    background: var(--c-teal) !important;
    border-color: var(--c-teal) !important;
    color: #fff !important;
}
[data-testid="stSelectbox"] > div > div,
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {
    background: var(--c-surface) !important;
    border: 1px solid var(--c-border) !important;
    border-radius: 6px !important; color: var(--c-text) !important;
    font-family: var(--c-font-mono) !important; font-size: 12px !important;
}
[data-testid="stSlider"] > div > div > div > div {
    background: var(--c-teal) !important;
}
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    color: var(--c-text2) !important;
    font-size: 13px !important; line-height: 1.65 !important;
}
[data-testid="stMarkdownContainer"] code {
    background: var(--c-surface2) !important;
    color: var(--c-teal) !important;
    border: 1px solid var(--c-border) !important;
    border-radius: 3px !important;
    font-size: 11px !important; padding: 1px 5px !important;
    font-family: var(--c-font-mono) !important;
}
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4 {
    color: var(--c-text) !important;
    font-family: var(--c-font-display) !important;
    letter-spacing: -.02em !important;
}
[data-testid="stAlert"] {
    border-radius: 6px !important; border-left-width: 3px !important;
    background: var(--c-surface) !important;
    font-family: var(--c-font-body) !important; font-size: 12px !important;
}
[data-testid="stCaptionContainer"] {
    color: var(--c-text3) !important; font-size: 11px !important;
    font-family: var(--c-font-mono) !important;
}
[data-testid="stSidebar"] label {
    font-family: var(--c-font-mono) !important; font-size: 10px !important;
    color: var(--c-text3) !important; letter-spacing: .06em !important;
    text-transform: uppercase !important;
}
hr { border-color: var(--c-border) !important; }

/* ── Plotly subplot titles — theme-aware ── */
.plotly .gtitle, .plotly .g-gtitle text,
.plotly .infolayer text {
    fill: var(--c-text) !important;
}
</style>

<script>
/* Sync Streamlit's built-in theme to our CSS variables */
(function() {
  function applyTheme() {
    var bg = window.getComputedStyle(document.body).backgroundColor;
    var rgb = bg.match(/\d+/g);
    if (rgb) {
      var luminance = (0.299*parseInt(rgb[0]) + 0.587*parseInt(rgb[1]) + 0.114*parseInt(rgb[2]));
      var root = document.documentElement;
      if (luminance < 100) {
        root.setAttribute('data-theme', 'dark');
        root.style.setProperty('--c-bg', '#12120f');
        root.style.setProperty('--c-surface', '#1c1c18');
        root.style.setProperty('--c-surface2', '#252520');
        root.style.setProperty('--c-border', '#2e2e28');
        root.style.setProperty('--c-border2', '#3a3a32');
        root.style.setProperty('--c-text', '#e8e6df');
        root.style.setProperty('--c-text2', '#b0aea6');
        root.style.setProperty('--c-text3', '#6a6860');
        root.style.setProperty('--c-teal', '#14a3a8');
        root.style.setProperty('--c-teal-lt', '#0d3335');
        root.style.setProperty('--c-green', '#3ab870');
      } else {
        root.setAttribute('data-theme', 'light');
        root.style.setProperty('--c-bg', '#f5f4f0');
        root.style.setProperty('--c-surface', '#ffffff');
        root.style.setProperty('--c-surface2', '#f0ede8');
        root.style.setProperty('--c-border', '#ddd9d2');
        root.style.setProperty('--c-border2', '#c9c4bc');
        root.style.setProperty('--c-text', '#1a1a18');
        root.style.setProperty('--c-text2', '#4a4a46');
        root.style.setProperty('--c-text3', '#8a8880');
        root.style.setProperty('--c-teal', '#0d7377');
        root.style.setProperty('--c-teal-lt', '#e6f4f4');
        root.style.setProperty('--c-green', '#1a7a4a');
      }
    }
  }
  setTimeout(applyTheme, 300);
  setTimeout(applyTheme, 1000);
  var obs = new MutationObserver(applyTheme);
  obs.observe(document.body, {attributes: true, attributeFilter: ['class', 'data-theme']});
})();
</script>
""", unsafe_allow_html=True)


# ── MODE REGISTRY ─────────────────────────────────────────────────────────────
MODES = [
    {
        "id": "classical", "icon": "⚡", "num": "01",
        "title": "Classical ADC",
        "color": "#0d7377",
        "fn": show_classical_ui,
        "desc": "Complete classical ADC analysis. Standard ADC pipeline, oversampling, aliasing, real-world noise, TPDF dithering, live animation, and industrial-grade characterization.",
        "tags": ["SNR","ENOB","THD","SINAD","OSR","DNL","INL","TPDF","Nyquist","FFT","PSD"],
        "sub": "7 sub-modes inside",
    },
    {
        "id": "quantum", "icon": "⚛️", "num": "02",
        "title": "Quantum Readout",
        "color": "#6c3fc1",
        "fn": show_quantum_ui,
        "desc": "ADC resolution determines qubit fidelity. IQ scatter plot, shot noise, erfc readout model, Standard Quantum Limit, Qiskit simulation, T1/T2 tradeoff.",
        "tags": ["Qubit","IQ scatter","erfc","Shot noise","Qiskit","SQL","T1/T2","Fidelity"],
        "sub": "Circuit diagram included",
    },
    {
        "id": "comparison", "icon": "📊", "num": "03",
        "title": "Comparison",
        "color": "#c17d11",
        "fn": show_comparison_ui,
        "desc": "Side-by-side ADC performance. Bit depth: 4-bit vs 16-bit. Oversampling: 1× vs 64×. See the quality delta instantly across time domain and FFT.",
        "tags": ["Bit depth","OSR","Side-by-side","Delta","FFT","Time domain"],
        "sub": "Instant visual diff",
    },
]
MODE_BY_ID = {m["id"]: m for m in MODES}

REFS = [
    ("[1]", "W. R. Bennett", "Spectra of Quantized Signals", "Bell System Tech. J., 1948 — Source of SQNR = 6.02·N + 1.76 dB"),
    ("[2]", "IEEE Std 1241-2010", "ADC Testing Standard", "Defines THD, SINAD, DNL, INL, ENOB for ADC characterization"),
    ("[3]", "Krantz et al.", "A Quantum Engineer's Guide to Superconducting Qubits", "Appl. Phys. Rev. 6, 2019 — Source of erfc readout error model"),
    ("[4]", "ICARUS-Q Collaboration", "Scalable Quantum Computing Architecture", "AIP Conf. Proc., 2022 — Quantum ADC readout chain"),
    ("[5]", "LIGO O4 Collaboration", "Gravitational Wave Detector", "2024 — Real use of TPDF dithering in precision instrumentation"),
    ("[6]", "Analog Devices MT-008", "Aperture Time, Aperture Jitter", "ENOB vs frequency, jitter-limited bandwidth model"),
]


# ─────────────────────────────────────────────────────────────────────────────
# HOME
# ─────────────────────────────────────────────────────────────────────────────
def show_home():
    visited = st.session_state.visited

    # Top nav
    st.markdown(f"""
<div class="topnav">
  <div class="topnav-brand">
    <div class="topnav-logo">ADC</div>
    <div>
      <div class="topnav-title">ADC Analyzer Pro</div>
      <div class="topnav-sub">QtHack04 · SRMIST · Track 04 · Problem #19</div>
    </div>
  </div>
  <div class="topnav-right">
    <span>{len(visited)}/3 modes visited</span>
    <span class="nav-badge">v23.0</span>
    <span class="nav-badge" style="background:var(--c-teal-lt);color:var(--c-teal);border-color:var(--c-teal)">47 tests passing</span>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown('<div class="page-body">', unsafe_allow_html=True)

    # Hero
    st.markdown("""
<div class="hero">
  <div class="hero-left">
    <div class="hero-eyebrow">ADC Resolution &amp; Noise Simulator</div>
    <div class="hero-h1">Designing <em>Perfect</em><br>ADCs — from<br>Bits to Qubits</div>
    <div class="hero-desc">
      An interactive simulator covering the complete ADC signal chain — quantization noise,
      Nyquist sampling, oversampling, dithering — and extending to quantum readout, where
      ADC resolution directly determines qubit fidelity.
      Built for QtHack04, Track 04: Quantum Systems.
    </div>
    <div class="hero-stack">
      <span class="stack-pill">Python</span>
      <span class="stack-pill">Streamlit</span>
      <span class="stack-pill">Plotly</span>
      <span class="stack-pill">NumPy / SciPy</span>
      <span class="stack-pill">Qiskit</span>
      <span class="stack-pill">IEEE 1241-2010</span>
    </div>
  </div>
  <div>
    <div class="info-box" style="margin-bottom:0">
      <div class="info-box-title">Quick stats</div>
      <div class="stat-row" style="border:1px solid var(--c-border);border-radius:6px;overflow:hidden;margin-bottom:12px">
        <div class="stat-cell"><span class="stat-val">9</span><span class="stat-lbl">Modes</span></div>
        <div class="stat-cell"><span class="stat-val">47</span><span class="stat-lbl">Tests</span></div>
        <div class="stat-cell"><span class="stat-val">6.02</span><span class="stat-lbl">dB/bit</span></div>
      </div>
      <div style="font-family:'DM Mono',monospace;font-size:11px;color:var(--c-text2);line-height:2">
        SQNR = 6.02·N + 1.76 dB<br>
        ENOB = (SNR − 1.76) / 6.02<br>
        OSR gain = 10·log₁₀(M) / 2 dB<br>
        Readout err = ½·erfc(√(SNR/2))<br>
        Shot SNR = 5·log₁₀(N<sub>photons</sub>)
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # Formula strip
    st.markdown("""
<div class="formula-strip">
  <span class="fs-label">Formula register</span>
  <div class="fs-row">
    <div class="fs-item"><span class="fs-name">SQNR</span><span class="fs-val">6.02 × N + 1.76 dB</span></div>
    <div class="fs-item"><span class="fs-name">ENOB</span><span class="fs-val">(SNR − 1.76) / 6.02</span></div>
    <div class="fs-item"><span class="fs-name">THD</span><span class="fs-val">20·log₁₀(√ΣVₙ²/V₁)</span></div>
    <div class="fs-item"><span class="fs-name">OSR gain</span><span class="fs-val">10·log₁₀(M) / 2 dB</span></div>
    <div class="fs-item"><span class="fs-name">Step (1 LSB)</span><span class="fs-val">(V_max − V_min) / 2^N</span></div>
    <div class="fs-item"><span class="fs-name">Q-noise rms</span><span class="fs-val">Δ / √12</span></div>
    <div class="fs-item"><span class="fs-name">Readout err</span><span class="fs-val">½·erfc(√(SNR/2))</span></div>
    <div class="fs-item"><span class="fs-name">Shot SNR</span><span class="fs-val">5·log₁₀(N_photons)</span></div>
    <div class="fs-item"><span class="fs-name">Alias freq</span><span class="fs-val">f mod fs → fold at fs/2</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

    # 3 mode cards (HTML for styling, buttons for interaction)
    st.markdown('<div class="mode-grid">', unsafe_allow_html=True)
    for mode in MODES:
        tags_html = "".join(f'<span class="mode-tag">{t}</span>' for t in mode["tags"])
        vis = '<span class="mode-visited">✓ visited</span>' if mode["id"] in visited else ""
        st.markdown(f"""
<div class="mode-card">
  <div class="mode-card-accent" style="background:{mode['color']}"></div>
  <div class="mode-card-icon-col">
    <span class="mode-icon">{mode['icon']}</span>
  </div>
  <div class="mode-card-body">
    <div class="mode-card-header">
      <div class="mode-title">{mode['title']}</div>
      <div class="mode-num">{mode['num']} / 03 &nbsp; {vis}</div>
    </div>
    <div class="mode-desc">{mode['desc']}</div>
    <div class="mode-tags">{tags_html}</div>
  </div>
  <div class="mode-card-action">Open →</div>
</div>
""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)  # close mode-grid

    # Open buttons — one per row, full width, matching horizontal card layout
    for mode in MODES:
        if st.button(f"Open {mode['title']}  →", key=f"open_{mode['id']}", use_container_width=True):
            st.session_state.visited.add(mode["id"])
            st.session_state.page = mode["id"]
            st.rerun()

    # Info grid — references + technical standards
    st.markdown('<div class="info-grid">', unsafe_allow_html=True)

    # References
    refs_html = ""
    for num, author, title, note in REFS:
        refs_html += f"""
<div class="ref-item">
  <span class="ref-num">{num}</span>
  <span class="ref-text"><strong>{author}</strong> — {title}. <span style="color:var(--c-text3)">{note}</span></span>
</div>"""
    st.markdown(f'<div class="info-box"><div class="info-box-title">References</div>{refs_html}</div>', unsafe_allow_html=True)

    # Technical notes
    st.markdown("""
<div class="info-box">
  <div class="info-box-title">Technical implementation notes</div>
  <div class="ref-item">
    <span class="ref-num">→</span>
    <span class="ref-text"><strong>Oversampling decimation</strong> — Uses averaging decimation (CIC-equivalent), not <code>resample_poly</code>. The latter smooths the staircase and artificially overstates SNR gain.</span>
  </div>
  <div class="ref-item">
    <span class="ref-num">→</span>
    <span class="ref-text"><strong>FFT normalization</strong> — Hann window, sum-normalized: mag = |rfft(x·w)| × 2 / Σw. Full-scale sine reads 0.000 dBFS exactly.</span>
  </div>
  <div class="ref-item">
    <span class="ref-num">→</span>
    <span class="ref-text"><strong>erfc readout model</strong> — Derived from Gaussian IQ blob overlap integral, not a heuristic. Validated against Krantz et al. (2019).</span>
  </div>
  <div class="ref-item">
    <span class="ref-num">→</span>
    <span class="ref-text"><strong>TPDF dither</strong> — Two uniform distributions summed = triangular PDF. Exactly as used in CD audio mastering and LIGO O4.</span>
  </div>
  <div class="ref-item">
    <span class="ref-num">→</span>
    <span class="ref-text"><strong>Test suite</strong> — 47 unit tests, all passing. Run: <code>python3 tests/test_adc.py</code></span>
  </div>
</div>
""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)  # info-grid

    # Footer
    st.markdown("""
<div style="border-top:1px solid var(--c-border);padding:16px 0;margin-top:8px;
    font-family:'DM Mono',monospace;font-size:10px;color:var(--c-text3);
    display:flex;justify-content:space-between;align-items:center">
  <span>Team Nyquist Nexus — Jayananda S · Nandana · Dennis Abraham</span>
  <span>SRMIST Kattankulathur · QtHack04 · March 30–31 2026</span>
</div>
""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # page-body


# ─────────────────────────────────────────────────────────────────────────────
# MODE PAGE
# ─────────────────────────────────────────────────────────────────────────────
def show_mode(mode_id: str):
    mode = MODE_BY_ID[mode_id]
    idx  = [m["id"] for m in MODES].index(mode_id)

    # Top nav
    st.markdown(f"""
<div class="topnav">
  <div class="topnav-brand">
    <div class="topnav-logo">ADC</div>
    <div>
      <div class="topnav-title">ADC Analyzer Pro</div>
      <div class="topnav-sub" style="color:var(--c-teal)">{mode['icon']} {mode['title']}</div>
    </div>
  </div>
  <div class="topnav-right">
    <span class="nav-badge" style="background:var(--c-teal-lt);color:var(--c-teal);border-color:var(--c-teal)">
      {mode['num']} / 03
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

    # Navigation row
    col_home, col_prev, col_next, _ = st.columns([1, 1, 1, 6])
    with col_home:
        if st.button("← Home", use_container_width=True):
            st.session_state.page = "home"; st.rerun()
    with col_prev:
        if idx > 0:
            p = MODES[idx-1]
            if st.button(f"← {p['title']}", use_container_width=True, help=p["title"]):
                st.session_state.visited.add(p["id"])
                st.session_state.page = p["id"]; st.rerun()
    with col_next:
        if idx < len(MODES)-1:
            n = MODES[idx+1]
            if st.button(f"{n['title']} →", use_container_width=True, help=n["title"]):
                st.session_state.visited.add(n["id"])
                st.session_state.page = n["id"]; st.rerun()

    # Accent line
    st.markdown(
        f'<div style="height:3px;background:{mode["color"]};margin:0 0 0"></div>',
        unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown(f"""
<div style="padding:12px 4px 8px;border-bottom:1px solid var(--c-border);margin-bottom:8px">
  <div style="font-family:'Syne',sans-serif;font-size:14px;font-weight:700;color:var(--c-teal);margin-bottom:2px">{mode['icon']} {mode['title']}</div>
  <div style="font-family:'DM Mono',monospace;font-size:9px;color:var(--c-text3);letter-spacing:.06em">Mode {mode['num']} of 03</div>
</div>
""", unsafe_allow_html=True)
        if st.button("← Back to Home", use_container_width=True, key="sb_home"):
            st.session_state.page = "home"; st.rerun()
        st.markdown("---")
        with st.expander("Switch mode"):
            for m in MODES:
                if m["id"] != mode_id:
                    lbl = f"{'✓ ' if m['id'] in st.session_state.visited else ''}{m['icon']} {m['title']}"
                    if st.button(lbl, key=f"sw_{m['id']}", use_container_width=True):
                        st.session_state.visited.add(m["id"])
                        st.session_state.page = m["id"]; st.rerun()
        with st.expander("Formula reference", expanded=False):
            st.code("SQNR = 6.02·N + 1.76 dB\nENOB = (SNR − 1.76) / 6.02\nOSR  = 10·log₁₀(M)/2 dB\nerr  = ½·erfc(√(SNR/2))\nTHD  = 20·log₁₀(√ΣVₙ²/V₁)", language=None)

    mode["fn"]()


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────
page = st.session_state.page
if page == "home":
    show_home()
elif page in MODE_BY_ID:
    show_mode(page)
else:
    st.session_state.page = "home"; st.rerun()
