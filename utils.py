# utils.py — Helpers de UI y formato

import plotly.graph_objects as go
from config import COLORS, CHART_COLORS

MESES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo',  6: 'Junio',   7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre',
}


def mes_nombre(m):
    return MESES.get(int(m), str(m))


def mes_etiqueta(año, mes):
    return f"{MESES.get(mes, mes)[:3]} {str(año)[2:]}"


def fmt_num(v):
    try:
        v = float(v)
        if v >= 1_000_000:
            return f"{v/1_000_000:.1f}M"
        if v >= 1_000:
            return f"{v/1_000:.1f}K"
        if v == int(v):
            return f"{int(v):,}"
        return f"{v:.1f}"
    except Exception:
        return str(v)


def fmt_pct(v):
    try:
        return f"{float(v):.1f}%"
    except Exception:
        return "—"


def kpi_status(real, meta):
    """Returns (emoji, color, pct)."""
    if not meta:
        return '⚪', COLORS['muted'], 0.0
    pct = (real / meta) * 100
    if pct >= 100:
        return '✅', COLORS['success'], pct
    if pct >= 75:
        return '🟡', COLORS['warning'], pct
    return '🔴', COLORS['danger'], pct


# ── Plotly layout ─────────────────────────────────────────────────────────────

_PLOTLY_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(10,22,40,0.6)',
    font=dict(color=COLORS['text'], family='Inter, sans-serif', size=12),
    xaxis=dict(gridcolor='rgba(30,58,95,.4)', linecolor='#1e3a5f', tickcolor='#1e3a5f'),
    yaxis=dict(gridcolor='rgba(30,58,95,.4)', linecolor='#1e3a5f', tickcolor='#1e3a5f'),
    legend=dict(bgcolor='rgba(0,0,0,0)', bordercolor='#1e3a5f'),
    margin=dict(t=40, b=40, l=40, r=20),
)


def apply_layout(fig, title='', height=360):
    fig.update_layout(**_PLOTLY_LAYOUT, height=height,
                      title=dict(text=title, font=dict(color=COLORS['muted'], size=12)))


# ── Gauge chart ───────────────────────────────────────────────────────────────

def gauge_chart(pct, label, color=None):
    color = color or COLORS['primary']
    val   = min(pct, 150)
    fig   = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        number={'suffix': '%', 'font': {'color': color, 'size': 28}},
        title={'text': label, 'font': {'color': COLORS['muted'], 'size': 11}},
        gauge={
            'axis': {'range': [0, 150], 'tickcolor': COLORS['muted'],
                     'tickfont': {'size': 9, 'color': COLORS['muted']}},
            'bar':  {'color': color, 'thickness': 0.25},
            'bgcolor': COLORS['bg2'],
            'borderwidth': 1, 'bordercolor': COLORS['border'],
            'steps': [
                {'range': [0, 75],   'color': 'rgba(255,68,68,.12)'},
                {'range': [75, 100], 'color': 'rgba(255,215,0,.12)'},
                {'range': [100, 150],'color': 'rgba(34,197,94,.12)'},
            ],
            'threshold': {'line': {'color': COLORS['accent'], 'width': 2},
                          'thickness': 0.75, 'value': 100},
        },
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=200, margin=dict(t=30, b=10, l=20, r=20),
    )
    return fig


# ── Metric card HTML ──────────────────────────────────────────────────────────

def metric_card_html(label, value, delta='', color=None, dark=True):
    color = color or COLORS['primary']
    if dark:
        bg, border, muted = COLORS['bg2'], COLORS['border'], COLORS['muted']
    else:
        bg, border, muted = '#ffffff', '#ccd9e8', '#456080'
    delta_html = f'<div style="font-size:.75rem;color:{muted};margin-top:4px;">{delta}</div>' if delta else ''
    return f"""
    <div style="
        background:{bg};border:1px solid {border};
        border-left:3px solid {color};border-radius:10px;
        padding:18px 20px;position:relative;
    ">
      <div style="font-size:.75rem;color:{muted};text-transform:uppercase;
                  letter-spacing:.08em;margin-bottom:6px;">{label}</div>
      <div style="font-size:1.8rem;font-weight:700;color:{color};
                  font-family:'Space Mono',monospace;">{value}</div>
      {delta_html}
    </div>"""


# ── Copy-to-clipboard button ──────────────────────────────────────────────────

def copy_button_html(text, label='📋 Copiar'):
    escaped = text.replace('`', r'\`').replace('\\', '\\\\')
    return f"""
    <button onclick="navigator.clipboard.writeText(`{escaped}`).then(()=>{{
        this.textContent='✅ Copiado!';setTimeout(()=>this.textContent='{label}',2000)
    }})" style="
        background:linear-gradient(135deg,#1e90ff,#0052cc);color:#fff;
        border:none;border-radius:8px;padding:10px 16px;cursor:pointer;
        font-size:13px;font-weight:600;width:100%;
        box-shadow:0 0 14px rgba(30,144,255,.35);
    ">{label}</button>"""
