# app.py — Punto de entrada

import os
import sys
from pathlib import Path
from datetime import date

ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

st.set_page_config(
    page_title="RRSS Analytics | Kabat One & SYM",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS estructural (sin colores — los inyecta el bloque de tema)
css_file = ROOT / "styles" / "custom.css"
if css_file.exists():
    st.markdown(f"<style>{css_file.read_text()}</style>", unsafe_allow_html=True)

_DARK_CSS = """
/* ══ TEMA OSCURO ══════════════════════════════════════════════════════ */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #111318 !important;
    color: #dde3ee !important;
}
/* Textura circuitos digitales */
[data-testid="stAppViewContainer"]::before {
    content:''; position:fixed; inset:0; pointer-events:none; z-index:0;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='80'%3E%3Ccircle cx='40' cy='40' r='4' fill='none' stroke='%231e90ff' stroke-opacity='0.07' stroke-width='1.2'/%3E%3Ccircle cx='40' cy='40' r='1.5' fill='%231e90ff' fill-opacity='0.09'/%3E%3Cline x1='0' y1='40' x2='34' y2='40' stroke='%231e90ff' stroke-opacity='0.05' stroke-width='1'/%3E%3Cline x1='46' y1='40' x2='80' y2='40' stroke='%231e90ff' stroke-opacity='0.05' stroke-width='1'/%3E%3Cline x1='40' y1='0' x2='40' y2='34' stroke='%231e90ff' stroke-opacity='0.05' stroke-width='1'/%3E%3Cline x1='40' y1='46' x2='40' y2='80' stroke='%231e90ff' stroke-opacity='0.05' stroke-width='1'/%3E%3Cline x1='62' y1='0' x2='62' y2='18' stroke='%231e90ff' stroke-opacity='0.06' stroke-width='1'/%3E%3Cline x1='62' y1='18' x2='80' y2='18' stroke='%231e90ff' stroke-opacity='0.06' stroke-width='1'/%3E%3Ccircle cx='62' cy='18' r='2.5' fill='none' stroke='%231e90ff' stroke-opacity='0.08' stroke-width='1'/%3E%3Ccircle cx='62' cy='18' r='1' fill='%231e90ff' fill-opacity='0.1'/%3E%3Cline x1='0' y1='62' x2='18' y2='62' stroke='%231e90ff' stroke-opacity='0.06' stroke-width='1'/%3E%3Cline x1='18' y1='62' x2='18' y2='80' stroke='%231e90ff' stroke-opacity='0.06' stroke-width='1'/%3E%3Ccircle cx='18' cy='62' r='2.5' fill='none' stroke='%231e90ff' stroke-opacity='0.08' stroke-width='1'/%3E%3Ccircle cx='18' cy='62' r='1' fill='%231e90ff' fill-opacity='0.1'/%3E%3Cline x1='0' y1='18' x2='12' y2='18' stroke='%231e90ff' stroke-opacity='0.04' stroke-width='1'/%3E%3Cline x1='62' y1='60' x2='80' y2='60' stroke='%231e90ff' stroke-opacity='0.04' stroke-width='1'/%3E%3Ccircle cx='0' cy='0' r='2' fill='%231e90ff' fill-opacity='0.07'/%3E%3Ccircle cx='80' cy='0' r='2' fill='%231e90ff' fill-opacity='0.07'/%3E%3Ccircle cx='0' cy='80' r='2' fill='%231e90ff' fill-opacity='0.07'/%3E%3Ccircle cx='80' cy='80' r='2' fill='%231e90ff' fill-opacity='0.07'/%3E%3C/svg%3E");
    background-size: 80px 80px;
}
[data-testid="stSidebar"] {
    background: #191c24 !important;
    border-right: 1px solid #2d3147 !important;
}
h1,h2,h3,h4,h5,h6 { color: #dde3ee !important; }

[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #4da6ff !important; }
[data-testid="metric-container"] [data-testid="stMetricLabel"] { color: #8892a4 !important; }

[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] [data-baseweb="select"] {
    background: #1e2130 !important;
    border: 1px solid #2d3147 !important;
    color: #dde3ee !important;
}
[data-testid="baseButton-secondary"] {
    background: rgba(30,144,255,.1) !important;
    border: 1px solid #2d3147 !important;
    color: #8892a4 !important;
}
[data-testid="baseButton-secondary"]:hover {
    background: rgba(30,144,255,.18) !important;
    color: #dde3ee !important;
}
[data-testid="stDataFrame"] { border: 1px solid #2d3147 !important; }
[data-testid="stDataFrame"] thead th {
    background: #1e2130 !important;
    color: #8892a4 !important;
}
[data-testid="stDataFrame"] tbody tr:hover td { background: rgba(30,144,255,.06) !important; }
[data-testid="stPlotlyChart"]  { border: 1px solid #2d3147 !important; }
[data-testid="stFileUploader"] {
    background: rgba(30,144,255,.04) !important;
    border: 1px dashed #2d3147 !important;
}
hr { border-color: #2d3147 !important; }
code {
    background: rgba(30,144,255,.12) !important;
    color: #00bfff !important;
    border: 1px solid rgba(30,144,255,.25) !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label { color: #8892a4 !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(30,144,255,.1) !important; color: #4da6ff !important;
}
[data-testid="stCheckbox"] label  { color: #dde3ee !important; }
[data-testid="stCaptionContainer"] { color: #8892a4 !important; }
"""

_LIGHT_CSS = """
/* ══ TEMA DÍA ════════════════════════════════════════════════════════ */

/* ── Textura circuitos ───────────────────────────────────────────── */
[data-testid="stAppViewContainer"]::before {
    content:''; position:fixed; inset:0; pointer-events:none; z-index:0;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='80'%3E%3Ccircle cx='40' cy='40' r='4' fill='none' stroke='%231e90ff' stroke-opacity='0.14' stroke-width='1.2'/%3E%3Ccircle cx='40' cy='40' r='1.5' fill='%231e90ff' fill-opacity='0.18'/%3E%3Cline x1='0' y1='40' x2='34' y2='40' stroke='%231e90ff' stroke-opacity='0.09' stroke-width='1'/%3E%3Cline x1='46' y1='40' x2='80' y2='40' stroke='%231e90ff' stroke-opacity='0.09' stroke-width='1'/%3E%3Cline x1='40' y1='0' x2='40' y2='34' stroke='%231e90ff' stroke-opacity='0.09' stroke-width='1'/%3E%3Cline x1='40' y1='46' x2='40' y2='80' stroke='%231e90ff' stroke-opacity='0.09' stroke-width='1'/%3E%3Cline x1='62' y1='0' x2='62' y2='18' stroke='%231e90ff' stroke-opacity='0.11' stroke-width='1'/%3E%3Cline x1='62' y1='18' x2='80' y2='18' stroke='%231e90ff' stroke-opacity='0.11' stroke-width='1'/%3E%3Ccircle cx='62' cy='18' r='2.5' fill='none' stroke='%231e90ff' stroke-opacity='0.18' stroke-width='1'/%3E%3Ccircle cx='62' cy='18' r='1' fill='%231e90ff' fill-opacity='0.2'/%3E%3Cline x1='0' y1='62' x2='18' y2='62' stroke='%231e90ff' stroke-opacity='0.11' stroke-width='1'/%3E%3Cline x1='18' y1='62' x2='18' y2='80' stroke='%231e90ff' stroke-opacity='0.11' stroke-width='1'/%3E%3Ccircle cx='18' cy='62' r='2.5' fill='none' stroke='%231e90ff' stroke-opacity='0.18' stroke-width='1'/%3E%3Ccircle cx='18' cy='62' r='1' fill='%231e90ff' fill-opacity='0.2'/%3E%3Cline x1='0' y1='18' x2='12' y2='18' stroke='%231e90ff' stroke-opacity='0.08' stroke-width='1'/%3E%3Cline x1='62' y1='60' x2='80' y2='60' stroke='%231e90ff' stroke-opacity='0.08' stroke-width='1'/%3E%3Ccircle cx='0' cy='0' r='2' fill='%231e90ff' fill-opacity='0.15'/%3E%3Ccircle cx='80' cy='0' r='2' fill='%231e90ff' fill-opacity='0.15'/%3E%3Ccircle cx='0' cy='80' r='2' fill='%231e90ff' fill-opacity='0.15'/%3E%3Ccircle cx='80' cy='80' r='2' fill='%231e90ff' fill-opacity='0.15'/%3E%3C/svg%3E");
    background-size: 80px 80px;
}

/* ── Fondo y texto base ──────────────────────────────────────────── */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
[data-testid="stMain"],
[data-testid="block-container"],
[data-testid="stVerticalBlock"] {
    background-color: #f0f5fb !important;
    color: #1a2d42 !important;
}
h1,h2,h3,h4,h5,h6 { color: #1a2d42 !important; }
.stMarkdown p, .stMarkdown li { color: #1a2d42 !important; }
[data-testid="stText"] { color: #1a2d42 !important; }
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] * { color: #456080 !important; }

/* ── Sidebar ─────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #f7fafd !important;
    border-right: 1px solid #ccd9e8 !important;
}
[data-testid="stSidebar"] * { color: #2a4060 !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    color: #2a4060 !important; padding: 6px 10px; border-radius: 7px;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(30,144,255,.1) !important; color: #0d5bcc !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] [data-baseweb="radio"] > div:first-child {
    display: none !important;
}
[data-testid="stSidebar"] button,
[data-testid="stSidebar"] [data-testid="baseButton-secondary"],
[data-testid="stSidebar"] [data-testid="baseButton-secondary"] p {
    background: #ddeaf7 !important; border: 1px solid #90b8d8 !important;
    color: #1a4a72 !important; font-weight: 600 !important;
}
[data-testid="stSidebar"] button:hover { background: #c6d9ef !important; color: #0d3a6b !important; }
[data-testid="stSidebar"] [data-testid="baseButton-primary"],
[data-testid="stSidebar"] [data-testid="baseButton-primary"] p {
    background: linear-gradient(135deg,#1e90ff,#0052cc) !important;
    color: #ffffff !important; border: none !important;
}

/* ── Botones generales ───────────────────────────────────────────── */
[data-testid="baseButton-secondary"] {
    background: #ddeaf7 !important; border: 1px solid #90b8d8 !important;
    color: #1a4a72 !important; font-weight: 600 !important;
}
[data-testid="baseButton-secondary"]:hover {
    background: #c6d9ef !important; border-color: #1e90ff !important; color: #0d3a6b !important;
}

/* ── Métricas (st.metric) ────────────────────────────────────────── */
[data-testid="metric-container"] {
    background: #ffffff !important; border: 1px solid #ccd9e8 !important;
    border-radius: 10px !important; padding: 14px 18px !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"],
[data-testid="metric-container"] [data-testid="stMetricValue"] div,
[data-testid="metric-container"] [data-testid="stMetricValue"] span { color: #1060cc !important; }
[data-testid="metric-container"] [data-testid="stMetricLabel"],
[data-testid="metric-container"] [data-testid="stMetricLabel"] * { color: #456080 !important; }
[data-testid="metric-container"] [data-testid="stMetricDelta"],
[data-testid="metric-container"] [data-testid="stMetricDelta"] div,
[data-testid="metric-container"] [data-testid="stMetricDelta"] span,
[data-testid="metric-container"] [data-testid="stMetricDelta"] p { color: #1a6e35 !important; }
[data-testid="metric-container"] [data-testid="stMetricDelta"] svg { fill: #1a6e35 !important; }

/* ── Expanders ───────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: #ffffff !important; border: 1px solid #ccd9e8 !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] details summary,
[data-testid="stExpander"] summary {
    background: #f0f5fb !important; color: #1a2d42 !important; border-radius: 8px;
}
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span { color: #1a2d42 !important; }
[data-testid="stExpander"] summary svg { fill: #456080 !important; }
[data-testid="stExpander"] > div,
[data-testid="stExpander"] details > div {
    background: #ffffff !important; color: #1a2d42 !important;
}

/* ── Formularios ─────────────────────────────────────────────────── */
[data-testid="stForm"] {
    background: #f7fafd !important; border: 1px solid #ccd9e8 !important;
    border-radius: 8px !important;
}

/* ── Alertas (info / warning / error / success) ──────────────────── */
[data-testid="stAlert"],
[data-testid="stAlertContainer"] {
    border-radius: 8px !important;
}
[data-testid="stAlert"] p,
[data-testid="stAlert"] span,
[data-testid="stAlert"] div { color: #1a2d42 !important; }
[data-testid="stAlert"][data-baseweb="notification"] { background: #e8f4fd !important; }
/* Info */
div[data-testid="stAlert"].stInfo,
.stInfo { background: #e8f4fd !important; border-left: 4px solid #1e90ff !important; }
/* Success */
div[data-testid="stAlert"].stSuccess,
.stSuccess { background: #e6f6ec !important; border-left: 4px solid #28a745 !important; }
/* Warning */
div[data-testid="stAlert"].stWarning,
.stWarning { background: #fff8e6 !important; border-left: 4px solid #ffc107 !important; }
/* Error */
div[data-testid="stAlert"].stError,
.stError { background: #fdecea !important; border-left: 4px solid #dc3545 !important; }

/* ── Inputs ──────────────────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] [data-baseweb="select"],
[data-baseweb="input"] {
    background: #ffffff !important; border: 1px solid #b8cce0 !important; color: #1a2d42 !important;
}
[data-testid="stTextInput"] label, [data-testid="stNumberInput"] label,
[data-testid="stTextArea"] label, [data-testid="stSelectbox"] label,
[data-testid="stMultiSelect"] label { color: #456080 !important; }
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p { color: #456080 !important; }

/* ── Selectbox dropdown ──────────────────────────────────────────── */
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="menu"],
[role="listbox"] {
    background: #ffffff !important; border: 1px solid #b8cce0 !important;
}
[role="option"] { background: #ffffff !important; color: #1a2d42 !important; }
[role="option"]:hover, [aria-selected="true"][role="option"] {
    background: #ddeaf7 !important; color: #1a4a72 !important;
}

/* ── Multiselect ─────────────────────────────────────────────────── */
[data-baseweb="tag"] { background: #ddeaf7 !important; }
[data-baseweb="tag"] span { color: #1a4a72 !important; }

/* ── Tablas (st.dataframe) ───────────────────────────────────────── */
[data-testid="stDataFrame"],
[data-testid="stDataFrame"] > div,
[data-testid="stDataFrame"] > div > div,
[data-testid="stDataFrameResizable"] {
    background: #ffffff !important; border: 1px solid #ccd9e8 !important;
    border-radius: 10px !important; color: #1a2d42 !important;
}
[data-testid="stDataFrame"] thead th {
    background: #e4edf7 !important; color: #456080 !important;
}
[data-testid="stDataFrame"] tbody td {
    background: #ffffff !important; color: #1a2d42 !important;
    border-color: #e8eef6 !important;
}
[data-testid="stDataFrame"] tbody tr:nth-child(even) td { background: #f5f8fc !important; }
[data-testid="stDataFrame"] tbody tr:hover td { background: rgba(30,144,255,.05) !important; }

/* ── Charts y file uploader ──────────────────────────────────────── */
[data-testid="stPlotlyChart"] { border: 1px solid #ccd9e8 !important; }
[data-testid="stFileUploader"] {
    background: #f7fafd !important; border: 1px dashed #90b8d8 !important;
}

/* ── Divisores ───────────────────────────────────────────────────── */
hr { border-color: #ccd9e8 !important; }

/* ── Código inline ───────────────────────────────────────────────── */
code {
    background: rgba(16,96,204,.08) !important; color: #0052aa !important;
    border: 1px solid rgba(16,96,204,.2) !important;
}
/* Bloque st.code() */
[data-testid="stCode"] > div, [data-testid="stCode"] pre,
[data-testid="stCodeBlock"] > div, [data-testid="stCodeBlock"] pre {
    background: #eef3fb !important; border: 1px solid #ccd9e8 !important; color: #1a2d42 !important;
}
[data-testid="stCode"] pre code, [data-testid="stCodeBlock"] pre code {
    color: #1a2d42 !important; background: transparent !important;
}

/* ── Checkboxes y captions ───────────────────────────────────────── */
[data-testid="stCheckbox"] label { color: #1a2d42 !important; }
[data-testid="stCaptionContainer"] { color: #456080 !important; }

/* ── Spinner ─────────────────────────────────────────────────────── */
[data-testid="stSpinner"] p { color: #456080 !important; }
"""

# DB
from database import init_db, seed_usuarios
init_db()
seed_usuarios()

# Sync GitHub al arrancar (si está configurado)
import sync as _sync
if _sync.github_configured() and 'github_pulled' not in st.session_state:
    with st.spinner("Sincronizando datos con GitHub…"):
        _sync.pull()
    st.session_state.github_pulled = True

# Auth
from auth import check_login, logout, get_user
if not check_login():
    st.stop()

user = get_user()

# ── Nombre Nebula en header ───────────────────────────────────────────────────
st.markdown("""
<div style="
  text-align: center;
  padding: 4px 0 8px;
  letter-spacing: .45em;
  font-family: 'Courier New', monospace;
  font-size: 2.8rem;
  font-weight: 300;
  color: rgba(255,255,255,0.82);
">NEBULA</div>
""", unsafe_allow_html=True)

# ── Defaults de sesión ────────────────────────────────────────────────────────
if 'marca_activa' not in st.session_state:
    st.session_state.marca_activa = 'k1'
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True
if 'ai_provider' not in st.session_state:
    st.session_state.ai_provider = 'gemini'

# Inyectar tema completo (reemplaza el bloque anterior en cada rerun)
_theme_css = _DARK_CSS if st.session_state.dark_mode else _LIGHT_CSS
st.markdown(f"<style>{_theme_css}</style>", unsafe_allow_html=True)

# Navegación: inicio en Monitor de KPIs
if 'nav_radio' not in st.session_state:
    st.session_state.nav_radio = "🎯  Monitor de KPIs"

# Cambio de sección solicitado por botones externos (debe aplicarse ANTES
# de que el widget radio se instancie en el sidebar)
if '_nav_pending' in st.session_state:
    st.session_state.nav_radio = st.session_state.pop('_nav_pending')

def _set_filter_defaults():
    if 'f_red' in st.session_state:
        return
    from database import get_last_data_month, get_redes_con_datos
    marca_nombre = 'Kabat One' if st.session_state.marca_activa == 'k1' else 'SYM'
    redes = get_redes_con_datos(marca_nombre)
    red   = 'LinkedIn' if 'LinkedIn' in redes else (redes[0] if redes else 'LinkedIn')
    last  = get_last_data_month(marca_nombre, red) if redes else None
    hoy   = date.today()
    if last:
        año, mes = last
    else:
        mes = hoy.month - 1 if hoy.month > 1 else 12
        año = hoy.year if hoy.month > 1 else hoy.year - 1
    st.session_state.f_red = red
    st.session_state.f_año = año
    st.session_state.f_mes = mes

_set_filter_defaults()

from config import REDES
from utils import mes_nombre

ASSETS       = ROOT / "assets"
hoy          = date.today()
marca_activa = st.session_state.marca_activa
años_disp    = list(range(hoy.year + 1, 2022, -1))
if st.session_state.get('f_año') not in años_disp:
    st.session_state.f_año = años_disp[1]

# ── Sidebar — marca + navegación + usuario ────────────────────────────────────
with st.sidebar:
    # Logo según marca activa y modo de color
    dark = st.session_state.get('dark_mode', True)
    logo_map = {
        'k1':  ASSETS / ('logo_k1.png'  if dark else 'logo_k1_day.png'),
        'sym': ASSETS / ('logo_sym.png' if dark else 'logo_sym_day.svg'),
    }
    logo_path = logo_map.get(marca_activa)
    if logo_path and logo_path.exists():
        st.image(str(logo_path), use_container_width=True)
    else:
        st.markdown(
            "<div style='padding:14px 0 6px;font-size:1.35rem;font-weight:700;"
            "color:#1e90ff;'>📊 RRSS Analytics</div>",
            unsafe_allow_html=True,
        )
    st.markdown("---")

    # Selector de marca
    col_k1, col_sym = st.columns(2)
    with col_k1:
        if st.button("Kabat One", use_container_width=True,
                     type="primary" if marca_activa == 'k1' else "secondary",
                     key="btn_k1"):
            st.session_state.marca_activa = 'k1'
            for k in ('f_red', 'f_año', 'f_mes'):
                st.session_state.pop(k, None)
            st.rerun()
    with col_sym:
        if st.button("SYM", use_container_width=True,
                     type="primary" if marca_activa == 'sym' else "secondary",
                     key="btn_sym"):
            st.session_state.marca_activa = 'sym'
            for k in ('f_red', 'f_año', 'f_mes'):
                st.session_state.pop(k, None)
            st.rerun()

    st.markdown("---")

    _nav_base = [
        "🎯  Monitor de KPIs", "🏠  Dashboard", "📁  Importar Datos",
        "🔍  Analista de Contenido", "🤖  Insights para IA",
        "📅  Parrilla de Contenido", "✍️  Post Rápido",
        "📊  Reporte", "📖  Manual de Uso",
    ]
    if user.get('role') == 'admin':
        _nav_base = _nav_base + ["🔐  Accesos"]
    _role = user.get('role', 'viewer')
    if _role == 'visita':
        nav_options = [
            "🎯  Monitor de KPIs", "🏠  Dashboard",
            "📅  Parrilla de Contenido", "📖  Manual de Uso",
        ]
    elif _role in ('admin', 'uploader'):
        nav_options = _nav_base
    else:
        nav_options = [x for x in _nav_base if x != "📁  Importar Datos"]
    # Si la sección activa fue removida por cambio de rol, resetear
    if st.session_state.get('nav_radio') not in nav_options:
        st.session_state.nav_radio = "🎯  Monitor de KPIs"

    nav = st.radio(
        "Módulos",
        nav_options,
        label_visibility="collapsed",
        key="nav_radio",
    )

    st.markdown("---")

    # Toggle modo oscuro / día
    modo_lbl = "☀️ Modo día" if st.session_state.dark_mode else "🌙 Modo noche"
    if st.button(modo_lbl, use_container_width=True, key="btn_modo"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

    st.markdown("---")

    # Selector de motor IA
    st.markdown(
        "<div style='color:#5b8db8;font-size:.7rem;font-weight:600;"
        "text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px;'>"
        "🤖 Motor IA</div>",
        unsafe_allow_html=True,
    )
    _prov_opts  = ['🟢 Gemini (gratis)', '🔷 Claude']
    _prov_map   = {'🟢 Gemini (gratis)': 'gemini', '🔷 Claude': 'claude'}
    _prov_rev   = {v: k for k, v in _prov_map.items()}
    _prov_cur   = _prov_rev.get(st.session_state.ai_provider, '🟢 Gemini (gratis)')
    _prov_sel   = st.radio(
        "Motor IA",
        _prov_opts,
        index=_prov_opts.index(_prov_cur),
        label_visibility="collapsed",
        key="radio_ai_provider",
    )
    st.session_state.ai_provider = _prov_map[_prov_sel]

    st.markdown("---")
    import subprocess as _sp
    try:
        _commit = _sp.check_output(['git','rev-parse','--short','HEAD'],
                                   cwd=str(ROOT), text=True).strip()
    except Exception:
        _commit = 'n/a'
    def _app_load_keys():
        env_path = ROOT / '.env'
        if env_path.exists():
            for _line in env_path.read_text(encoding='utf-8').splitlines():
                _line = _line.strip()
                if _line and not _line.startswith('#') and '=' in _line:
                    _k, _, _v = _line.partition('=')
                    os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))
        try:
            for _k, _v in st.secrets.items():
                if isinstance(_v, str):
                    os.environ.setdefault(_k, _v)
        except Exception:
            pass
    _app_load_keys()
    _api_ok  = bool(os.environ.get('ANTHROPIC_API_KEY','').strip())
    _gem_ok  = bool(os.environ.get('GEMINI_API_KEY','').strip())
    _api_lbl = ('✅ Claude' if _api_ok else '❌ Claude') + ' · ' + ('✅ Gemini' if _gem_ok else '❌ Gemini')
    st.markdown(
        f"<div style='color:#5b8db8;font-size:.72rem;'>"
        f"👤 {user.get('nombre','—')} · {user.get('role','').title()}<br>"
        f"<span style='font-family:monospace'>v {_commit}<br>{_api_lbl}</span></div>",
        unsafe_allow_html=True,
    )
    if st.button("🚪 Cerrar sesión", use_container_width=True, key="logout_btn"):
        logout()

    # ── Panel Accesos (solo admin) — tabla de referencia rápida ───────
    if user.get('role') == 'admin':
        st.markdown("---")
        with st.expander("🔐 Accesos"):
            from database import get_usuarios_lista as _get_lista
            _RLABEL = {'admin': '🛡️', 'uploader': '📁', 'viewer': '👁️'}
            st.markdown(
                "<div style='display:grid;grid-template-columns:1fr 1fr 32px;"
                "gap:4px;font-size:.7rem;font-weight:700;color:#5b8db8;"
                "padding:4px 2px;border-bottom:2px solid rgba(100,140,200,.3);'>"
                "<span>Usuario</span><span>Contraseña</span><span></span></div>",
                unsafe_allow_html=True,
            )
            for _u in _get_lista():
                st.markdown(
                    f"<div style='display:grid;grid-template-columns:1fr 1fr 32px;"
                    f"gap:4px;font-size:.78rem;padding:5px 2px;"
                    f"border-bottom:1px solid rgba(100,100,100,.12);align-items:center;'>"
                    f"<span style='font-weight:600;'>{_u['username']}</span>"
                    f"<span style='font-family:monospace;color:#1e90ff;'>{_u['password']}</span>"
                    f"<span style='font-size:.85rem;'>{_RLABEL.get(_u['role'],'👤')}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("⚙️ Gestionar accesos", use_container_width=True,
                         key="sb_goto_accesos"):
                st.session_state._nav_pending = "🔐  Accesos"
                st.rerun()

# ── Barra de filtros superior ─────────────────────────────────────────────────
# Solo se muestra en secciones que usan los filtros de red/año/mes
_NAV_CON_FILTROS = {
    "🎯  Monitor de KPIs",
    "🏠  Dashboard",
    "🔍  Analista de Contenido",
    "🤖  Insights para IA",
}

if nav in _NAV_CON_FILTROS:
    col_lbl, col_red, col_año, col_mes, col_sp, col_btn = st.columns([1.2, 2.2, 1.4, 2.2, 3, 2.2])

    with col_lbl:
        st.markdown("""
        <div style="margin-top:29px;display:inline-block;
                    background:rgba(30,144,255,.1);
                    border:1px solid rgba(30,144,255,.35);
                    border-radius:7px;padding:7px 13px;
                    color:#7ab3e0;font-size:.7rem;
                    text-transform:uppercase;letter-spacing:.1em;
                    white-space:nowrap;">
          🔧 Filtros
        </div>
        """, unsafe_allow_html=True)

    with col_red:
        st.selectbox("Red Social", REDES, key="f_red")

    with col_año:
        st.selectbox("Año", años_disp, key="f_año")

    with col_mes:
        st.selectbox("Mes", list(range(1, 13)), format_func=mes_nombre, key="f_mes")

    with col_btn:
        st.markdown("<div style='margin-top:29px;'>", unsafe_allow_html=True)
        if user.get('role') in ('admin', 'uploader'):
            if st.button("📁 Importar Datos", use_container_width=True, key="btn_importar_top"):
                st.session_state._nav_pending = "📁  Importar Datos"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

# ── Routing ───────────────────────────────────────────────────────────────────
if nav == "🎯  Monitor de KPIs":
    from modules.kpi_monitor import show_kpis
    show_kpis()

elif nav == "🏠  Dashboard":
    from modules.dashboard import show_dashboard
    show_dashboard()

elif nav == "📁  Importar Datos":
    from modules.data_loader import show_uploader
    show_uploader()

elif nav == "🔍  Analista de Contenido":
    from modules.analista import show_analista
    show_analista()

elif nav == "🤖  Insights para IA":
    from modules.ai_insights import show_insights
    show_insights()

elif nav == "📅  Parrilla de Contenido":
    from modules.parrilla import show_parrilla
    show_parrilla()

elif nav == "✍️  Post Rápido":
    from modules.post_quick import show_post_quick
    show_post_quick()

elif nav == "📊  Reporte":
    from modules.reporte import show_reporte
    show_reporte()

elif nav == "📖  Manual de Uso":
    from modules.readme import show_readme
    show_readme()

elif nav == "🔐  Accesos":
    from modules.accesos import show_accesos
    show_accesos()
