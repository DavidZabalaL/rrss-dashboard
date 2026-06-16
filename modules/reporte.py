# modules/reporte.py — Generador de Reporte HTML con identidad de marca

import base64
import json
from datetime import datetime
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import METRICAS
from database import (
    get_kpi_manual,
    get_kpi_objetivos,
    get_metricas_historico_mensual,
    get_metricas_mensuales,
    get_parrilla_posts,
    get_publicaciones_count,
    get_redes_con_datos,
)

ROOT = Path(__file__).parent.parent

MESES_ES = {
    1: "Enero",    2: "Febrero",   3: "Marzo",     4: "Abril",
    5: "Mayo",     6: "Junio",     7: "Julio",      8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

_MARCA_DB = {"k1": "Kabat One", "sym": "SYM"}
_BRAND_JSON = {
    "k1":  ROOT / "marca" / "kabat-one"     / "brand.json",
    "sym": ROOT / "marca" / "sym-servicios"  / "brand.json",
}
_LOGO_PATHS = {
    "k1":  ROOT / "assets" / "logo_k1.png",
    "sym": ROOT / "assets" / "logo_sym.png",
}

# Colores e íconos por red social
_NET_COLOR = {
    "LinkedIn":  "#0077B5",
    "Facebook":  "#1877F2",
    "Instagram": "#C13584",
}
_NET_ICON = {
    "LinkedIn":  "in",
    "Facebook":  "f",
    "Instagram": "ig",
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _load_brand(marca_key: str) -> dict:
    path = _BRAND_JSON.get(marca_key)
    if path and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "label": marca_key.upper(), "tagline": "",
        "colors": {"primary": "#1e90ff", "secondary": "#24326A",
                   "accent": "#31D8FF", "background_dark": "#060E40"},
    }


def _get_logo_b64(marca_key: str) -> str:
    path = _LOGO_PATHS.get(marca_key)
    if not path or not path.exists():
        return ""
    suffix = path.suffix.lower()
    mime = ("image/svg+xml" if suffix == ".svg"
            else "image/jpeg" if suffix in (".jpg", ".jpeg")
            else "image/png")
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def _fmt(v) -> str:
    try:
        v = float(v)
        if v >= 1_000_000: return f"{v/1_000_000:.1f}M"
        if v >= 1_000:     return f"{v/1_000:.1f}K"
        if v == int(v):    return f"{int(v):,}"
        return f"{v:.1f}"
    except Exception:
        return "—"


def _badge_style(pct: float, has_meta: bool):
    """Returns (bg, fg, label) for a cumplimiento badge."""
    if not has_meta:
        return "#e5e7eb", "#6b7280", "S/Meta"
    if pct >= 100: return "#d1fae5", "#065f46", f"✅ {pct:.0f}%"
    if pct >= 75:  return "#fef3c7", "#92400e", f"🟡 {pct:.0f}%"
    return "#fee2e2", "#991b1b", f"🔴 {pct:.0f}%"


def _tipo_hint(tipo: str) -> str:
    if tipo == "auto_4pct":         return "auto 4%"
    if tipo in ("auto_50pct", "manual_50pct"): return "50% viz."
    if tipo == "contenido":         return "posts"
    return ""


# ── Data gathering ─────────────────────────────────────────────────────────────

def _get_network_kpis(marca: str, red: str, año: int, mes: int) -> list:
    """Full KPI list — identical logic to KPI Monitor."""
    defs      = METRICAS.get(red, [])
    reales    = get_metricas_mensuales(marca, red, año, mes)
    objetivos = get_kpi_objetivos(marca, red, año, mes)
    imp_real  = float(reales.get("impresiones",    0) or 0)
    vis_real  = float(reales.get("visualizaciones", 0) or 0)

    out = []
    for m in defs:
        key, tipo = m["key"], m["tipo"]

        real = (float(get_publicaciones_count(marca, red, año, mes))
                if tipo == "contenido"
                else float(get_kpi_manual(marca, red, key, año, mes))
                if tipo in ("manual", "manual_50pct")
                else float(reales.get(key, 0) or 0))

        meta = (round(imp_real * 0.04)   if tipo == "auto_4pct"
                else round(vis_real * 0.50) if tipo in ("auto_50pct", "manual_50pct")
                else float(objetivos.get(key, 0) or 0))

        pct      = (real / meta * 100) if meta else 0.0
        bg, fg, badge = _badge_style(pct, bool(meta))

        out.append({
            "key": key, "label": m["label"], "icon": m["icon"], "tipo": tipo,
            "real": real, "meta": meta, "pct": pct,
            "badge_bg": bg, "badge_fg": fg, "badge_lbl": badge,
            "has_meta": bool(meta),
            "tipo_hint": _tipo_hint(tipo),
        })
    return out


def _get_report_data(marca: str, marca_key: str, año: int, mes: int) -> dict:
    redes_raw = get_redes_con_datos(marca)
    networks  = {}
    for red in redes_raw:
        networks[red] = {
            "kpis":      _get_network_kpis(marca, red, año, mes),
            "historico": get_metricas_historico_mensual(marca, red),
        }
    return {
        "redes":    list(networks.keys()),
        "networks": networks,
        "parrilla": get_parrilla_posts(marca, año, mes),
    }


# ── Chart builders ─────────────────────────────────────────────────────────────

def _chart_trend(historico_df, net_color: str) -> str:
    if historico_df is None or historico_df.empty:
        return ""
    metrics = historico_df["metrica"].unique().tolist()
    priority = ["incremento_seguidores", "alcance", "impresiones",
                "visualizaciones", "interaccion", "visitas"]
    sel = [m for p in priority for m in metrics if p in m][:2] or metrics[:2]

    colors = [net_color, "#f59e0b", "#8b5cf6", "#10b981"]
    fig = go.Figure()
    for i, met in enumerate(sel):
        df = historico_df[historico_df["metrica"] == met].sort_values(["año", "mes"])
        xl = [f"{MESES_ES.get(int(r['mes']), '')[:3]} {str(r['año'])[2:]}" for _, r in df.iterrows()]
        fig.add_trace(go.Scatter(
            x=xl, y=df["valor"].tolist(), mode="lines+markers",
            name=met.replace("_", " ").title(),
            line=dict(color=colors[i % len(colors)], width=2.5),
            marker=dict(size=6),
        ))
    fig.update_layout(
        height=240, margin=dict(l=36, r=16, t=8, b=36),
        paper_bgcolor="white", plot_bgcolor="#f8fafc",
        font=dict(family="Inter, sans-serif", size=10, color="#555"),
        legend=dict(orientation="h", y=1.06, x=1, xanchor="right", font=dict(size=9)),
        xaxis=dict(showgrid=True, gridcolor="#eee", tickfont=dict(size=9)),
        yaxis=dict(showgrid=True, gridcolor="#eee", tickfont=dict(size=9)),
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)


def _chart_mom(historico_df, net_color: str) -> str:
    if historico_df is None or historico_df.empty:
        return ""
    metrics = historico_df["metrica"].unique().tolist()
    top = [m for m in ["incremento_seguidores", "visualizaciones",
                        "interaccion", "alcance", "impresiones"] if m in metrics][:3]
    if not top:
        top = metrics[:3]

    df = historico_df[historico_df["metrica"].isin(top)].copy()
    df["lbl"] = df.apply(
        lambda r: f"{MESES_ES.get(int(r['mes']), '')[:3]} {str(int(r['año']))[2:]}", axis=1
    )
    ultimas = df.sort_values(["año", "mes"])["lbl"].unique()[-6:]
    df = df[df["lbl"].isin(ultimas)]
    if df.empty:
        return ""

    fig = px.bar(df, x="lbl", y="valor", color="metrica", barmode="group",
                 color_discrete_sequence=[net_color, "#f59e0b", "#8b5cf6"])
    fig.update_layout(
        height=240, margin=dict(l=36, r=16, t=8, b=36),
        paper_bgcolor="white", plot_bgcolor="#f8fafc",
        font=dict(family="Inter, sans-serif", size=10, color="#555"),
        legend=dict(orientation="h", y=1.06, x=1, xanchor="right", font=dict(size=9)),
        xaxis=dict(showgrid=False, tickfont=dict(size=9)),
        yaxis=dict(showgrid=True, gridcolor="#eee", tickfont=dict(size=9)),
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)


# ── HTML component builders ────────────────────────────────────────────────────

def _kpi_card(kpi: dict, net_color: str) -> str:
    bar_w    = min(int(kpi["pct"]), 100)
    bar_col  = kpi["badge_fg"] if kpi["has_meta"] else "#cbd5e1"
    tipo_tag = (f'<span style="font-size:.55rem;background:#e0f2fe;color:#0369a1;'
                f'border-radius:10px;padding:1px 5px;margin-left:4px;">'
                f'{kpi["tipo_hint"]}</span>'
                if kpi["tipo_hint"] else "")
    meta_txt = (f'Meta: <b>{_fmt(kpi["meta"])}</b>' if kpi["has_meta"] else "Sin meta")

    return f"""<div style="background:#fff;border-radius:10px;padding:16px 14px 12px;
border:1px solid #e2e8f0;border-left:3px solid {net_color};
box-shadow:0 1px 4px rgba(0,0,0,.06);">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
    <span style="font-size:.6rem;font-weight:700;color:#94a3b8;text-transform:uppercase;
    letter-spacing:.1em;">{kpi['icon']}&nbsp;{kpi['label']}{tipo_tag}</span>
  </div>
  <div style="font-size:1.9rem;font-weight:800;color:#1e293b;line-height:1;margin-bottom:10px;">{_fmt(kpi['real'])}</div>
  <div style="background:#f1f5f9;border-radius:4px;height:5px;margin-bottom:10px;overflow:hidden;">
    <div style="width:{bar_w}%;background:{bar_col};height:100%;border-radius:4px;"></div>
  </div>
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <span style="font-size:.68rem;color:#64748b;">{meta_txt}</span>
    <span style="font-size:.68rem;font-weight:700;padding:2px 8px;border-radius:20px;
    background:{kpi['badge_bg']};color:{kpi['badge_fg']};white-space:nowrap;">{kpi['badge_lbl']}</span>
  </div>
</div>"""


def _kpi_table(kpis: list, primary: str) -> str:
    rows = ""
    for k in kpis:
        bg, fg, badge = k["badge_bg"], k["badge_fg"], k["badge_lbl"]
        meta_disp = _fmt(k["meta"]) if k["has_meta"] else "—"
        if k["tipo_hint"]:
            meta_disp += f' <span style="font-size:.6rem;color:#94a3b8;">({k["tipo_hint"]})</span>'
        rows += f"""<tr>
  <td style="font-weight:600;">{k['icon']}&nbsp;{k['label']}</td>
  <td style="font-weight:800;font-size:1rem;color:{primary};">{_fmt(k['real'])}</td>
  <td>{meta_disp}</td>
  <td><span style="font-size:.72rem;font-weight:700;padding:3px 10px;border-radius:20px;
  background:{bg};color:{fg};">{badge}</span></td>
</tr>"""
    return f"""<table style="width:100%;border-collapse:collapse;font-size:.82rem;">
  <thead>
    <tr style="background:#f8fafc;">
      <th style="padding:9px 14px;font-size:.65rem;font-weight:700;text-transform:uppercase;
      letter-spacing:.08em;color:#64748b;text-align:left;border-bottom:2px solid #e2e8f0;">Métrica</th>
      <th style="padding:9px 14px;font-size:.65rem;font-weight:700;text-transform:uppercase;
      letter-spacing:.08em;color:#64748b;text-align:left;border-bottom:2px solid #e2e8f0;">Real</th>
      <th style="padding:9px 14px;font-size:.65rem;font-weight:700;text-transform:uppercase;
      letter-spacing:.08em;color:#64748b;text-align:left;border-bottom:2px solid #e2e8f0;">Meta</th>
      <th style="padding:9px 14px;font-size:.65rem;font-weight:700;text-transform:uppercase;
      letter-spacing:.08em;color:#64748b;text-align:left;border-bottom:2px solid #e2e8f0;">Cumplimiento</th>
    </tr>
  </thead>
  <tbody>{rows}</tbody>
</table>"""


def _network_section(red: str, net_data: dict, primary: str, mes_label: str, año: int) -> str:
    kpis      = net_data.get("kpis", [])
    historico = net_data.get("historico")
    net_color = _NET_COLOR.get(red, primary)
    net_icon  = _NET_ICON.get(red, "●")

    # Resumen para el header
    total    = len([k for k in kpis if k["has_meta"]])
    en_meta  = len([k for k in kpis if k["has_meta"] and k["pct"] >= 100])
    avg_pct  = (sum(k["pct"] for k in kpis if k["has_meta"]) / total) if total else 0

    if total:
        hdr_badge = (f'<span style="background:rgba(255,255,255,.2);border-radius:20px;'
                     f'padding:3px 12px;font-size:.78rem;font-weight:700;">'
                     f'{en_meta}/{total} KPIs en meta · {avg_pct:.0f}% avg</span>')
    else:
        hdr_badge = ""

    # KPI cards
    cards_html = "".join(_kpi_card(k, net_color) for k in kpis)
    cards_per_row = 3
    grid_html = (f'<div style="display:grid;grid-template-columns:repeat({cards_per_row},1fr);'
                 f'gap:14px;padding:22px 24px;background:#f8fafc;">{cards_html}</div>')

    # KPI table
    table_html = (f'<div style="padding:0 24px 24px;">'
                  f'<div style="font-size:.72rem;font-weight:700;text-transform:uppercase;'
                  f'letter-spacing:.08em;color:#64748b;margin-bottom:12px;">Detalle de KPIs</div>'
                  f'{_kpi_table(kpis, net_color)}</div>')

    # Charts
    trend_html = _chart_trend(historico, net_color)
    mom_html   = _chart_mom(historico, net_color)

    if trend_html or mom_html:
        def _chart_box(title, html):
            return (f'<div style="padding:16px 20px 8px;border-top:1px solid #f1f5f9;">'
                    f'<div style="font-size:.65rem;font-weight:700;text-transform:uppercase;'
                    f'letter-spacing:.1em;color:#94a3b8;margin-bottom:6px;">{title}</div>'
                    f'{html}</div>')

        if trend_html and mom_html:
            charts_html = (
                f'<div style="display:grid;grid-template-columns:1fr 1fr;">'
                f'{_chart_box("Tendencia histórica", trend_html)}'
                f'{_chart_box("Comparativa mes a mes", mom_html)}'
                f'</div>'
            )
        else:
            charts_html = _chart_box("Tendencia histórica", trend_html or mom_html)
    else:
        charts_html = ""

    return f"""<div style="margin:28px 0;background:#fff;border-radius:14px;overflow:hidden;
box-shadow:0 2px 16px rgba(0,0,0,.08);page-break-inside:avoid;">
  <!-- Network header -->
  <div style="background:linear-gradient(135deg,{net_color} 0%,{net_color}cc 100%);
  padding:18px 24px;display:flex;align-items:center;justify-content:space-between;gap:16px;">
    <div style="display:flex;align-items:center;gap:14px;">
      <div style="width:40px;height:40px;border-radius:50%;background:rgba(255,255,255,.2);
      display:flex;align-items:center;justify-content:center;font-size:1rem;font-weight:800;
      color:#fff;flex-shrink:0;">{net_icon}</div>
      <div>
        <div style="font-size:1.1rem;font-weight:700;color:#fff;line-height:1.2;">{red}</div>
        <div style="font-size:.78rem;color:rgba(255,255,255,.75);margin-top:2px;">{mes_label} {año}</div>
      </div>
    </div>
    {hdr_badge}
  </div>
  {grid_html}
  {table_html}
  {charts_html}
</div>"""


# ── Main HTML builder ──────────────────────────────────────────────────────────

def _build_html_report(marca_key: str, año: int, mes: int,
                       brand: dict, data: dict, logo_b64: str) -> str:

    colors    = brand.get("colors", {})
    primary   = colors.get("primary",          "#1e90ff")
    secondary = colors.get("secondary",         "#24326A")
    accent    = colors.get("accent",            "#31D8FF")
    dark_bg   = colors.get("background_dark",   "#060E40")
    label     = brand.get("label", marca_key.upper())
    tagline   = brand.get("tagline", "")
    mes_label = MESES_ES.get(mes, str(mes))
    fecha_gen = datetime.now().strftime("%d/%m/%Y %H:%M")

    css = f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: 'Inter', Arial, sans-serif;
    background: #e8edf4;
    color: #1a2d42;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}}
.report-wrapper {{
    max-width: 960px;
    margin: 0 auto;
    background: #f0f4f9;
    box-shadow: 0 4px 32px rgba(0,0,0,.18);
}}
.cover {{
    background: linear-gradient(145deg, {dark_bg} 0%, {secondary} 55%, {primary}22 100%);
    min-height: 100vh;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    padding: 60px 48px;
    page-break-after: always; break-after: page;
    position: relative; overflow: hidden;
}}
.cover::before {{
    content: '';
    position: absolute; inset: 0;
    background: radial-gradient(ellipse at 70% 30%, {accent}18 0%, transparent 55%);
    pointer-events: none;
}}
.cover::after {{
    content: '';
    position: absolute;
    bottom: -40px; left: -40px; width: 300px; height: 300px;
    background: radial-gradient(circle, {primary}18 0%, transparent 70%);
    pointer-events: none;
}}
.cover-logo {{ max-width:220px;max-height:110px;object-fit:contain;margin-bottom:44px;
    filter:drop-shadow(0 4px 16px rgba(0,0,0,.3)); }}
.cover-eyebrow {{ font-size:.75rem;font-weight:700;color:{accent};text-transform:uppercase;
    letter-spacing:.25em;margin-bottom:20px;opacity:.9; }}
.cover-title {{ font-size:2.6rem;font-weight:800;color:#fff;text-align:center;
    letter-spacing:-.02em;line-height:1.15;margin-bottom:12px;
    text-shadow:0 2px 8px rgba(0,0,0,.3); }}
.cover-pill {{ background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.2);
    border-radius:40px;padding:8px 24px;font-size:1.1rem;font-weight:700;color:#fff;
    margin:16px 0;letter-spacing:.04em; }}
.cover-brand {{ font-size:.9rem;font-weight:500;color:rgba(255,255,255,.6);margin-top:8px; }}
.cover-tagline {{ position:absolute;bottom:40px;font-size:.82rem;color:rgba(255,255,255,.4);
    font-style:italic;letter-spacing:.06em; }}

.body-wrapper {{ padding: 28px 32px; }}

.section-header {{
    display: flex; align-items: center; gap: 12px;
    margin: 32px 0 20px;
    padding-bottom: 12px;
    border-bottom: 2px solid #e2e8f0;
}}
.section-header-dot {{
    width: 10px; height: 10px;
    background: {primary}; border-radius: 50%; flex-shrink: 0;
}}
.section-header-title {{
    font-size: 1rem; font-weight: 700; color: {secondary};
    text-transform: uppercase; letter-spacing: .06em;
}}

.parrilla-table {{ width:100%;border-collapse:collapse;font-size:.78rem;margin-top:8px; }}
.parrilla-table thead tr {{ background:{primary};color:#fff; }}
.parrilla-table thead th {{ padding:9px 12px;font-weight:600;font-size:.68rem;
    letter-spacing:.06em;text-transform:uppercase;text-align:left;white-space:nowrap; }}
.parrilla-table tbody tr:nth-child(even) {{ background:#f5f8fc; }}
.parrilla-table tbody tr:nth-child(odd)  {{ background:#ffffff; }}
.parrilla-table tbody td {{ padding:8px 12px;border-bottom:1px solid #edf1f7;
    color:#2a3d55;vertical-align:middle; }}
.parrilla-table tbody td:first-child {{ font-weight:600;color:{secondary};white-space:nowrap; }}
.estado-badge {{ display:inline-block;padding:2px 8px;border-radius:20px;
    font-size:.65rem;font-weight:600;letter-spacing:.04em;text-transform:uppercase; }}
.estado-publicado  {{ background:#d4f0e0;color:#1a6e35; }}
.estado-programado {{ background:#ddeaf7;color:#1060cc; }}
.estado-borrador   {{ background:#f0f0f0;color:#666; }}
.estado-cancelado  {{ background:#fdecea;color:#c0392b; }}
.estado-revision   {{ background:#fff3cd;color:#856404; }}

.report-footer {{ background:{dark_bg};padding:28px 40px;
    display:flex;align-items:center;justify-content:space-between;gap:20px; }}
.footer-logo {{ max-height:36px;max-width:130px;object-fit:contain;opacity:.9; }}
.footer-tagline {{ font-size:.75rem;color:rgba(255,255,255,.5);font-style:italic;
    flex:1;text-align:center; }}
.footer-credit {{ font-size:.68rem;color:rgba(255,255,255,.35);text-align:right;white-space:nowrap; }}

@media print {{
    .report-wrapper {{ box-shadow:none; }}
    .cover {{ min-height:100vh;page-break-after:always; }}
    .body-wrapper {{ padding:20px 24px; }}
}}
"""

    # ── Cover ────────────────────────────────────────────────────────────────
    logo_html = (f'<img class="cover-logo" src="{logo_b64}" alt="{label}">'
                 if logo_b64
                 else f'<div style="font-size:2rem;font-weight:800;color:{accent};margin-bottom:44px;">{label}</div>')

    cover = f"""<div class="cover">
  {logo_html}
  <div class="cover-eyebrow">Reporte Mensual</div>
  <div class="cover-title">Redes Sociales</div>
  <div class="cover-pill">{mes_label} {año}</div>
  <div class="cover-brand">{label}</div>
  <div class="cover-tagline">{tagline}</div>
</div>"""

    # ── Network sections ──────────────────────────────────────────────────────
    net_sections = ""
    for red in data["redes"]:
        net_sections += _network_section(
            red, data["networks"][red], primary, mes_label, año
        )

    if not data["redes"]:
        net_sections = ('<div style="padding:40px;text-align:center;color:#94a3b8;'
                        'font-size:.9rem;">No hay datos importados para este período.</div>')

    # ── Parrilla ──────────────────────────────────────────────────────────────
    parrilla = data.get("parrilla", [])
    if parrilla:
        rows_html = ""
        for post in parrilla:
            tema_raw = post.get("tema") or post.get("copy_linkedin") or ""
            tema     = (tema_raw[:85] + "…") if len(tema_raw) > 85 else tema_raw
            estado   = post.get("estado", "Borrador")
            ec       = estado.lower().replace(" ", "")
            ecls     = ("estado-publicado"  if "publicad" in ec else
                        "estado-programado" if "programad" in ec else
                        "estado-cancelado"  if "cancelad" in ec else
                        "estado-revision"   if "revision" in ec or "revisión" in ec else
                        "estado-borrador")
            rows_html += f"""<tr>
  <td>{post.get('fecha','')}</td>
  <td>{post.get('dia_semana','')}</td>
  <td>{post.get('formato') or post.get('tipo_dia','')}</td>
  <td style="max-width:300px;">{tema}</td>
  <td><span class="estado-badge {ecls}">{estado}</span></td>
</tr>"""

        parrilla_inner = f"""<table class="parrilla-table">
  <thead><tr>
    <th>Fecha</th><th>Día</th><th>Tipo</th><th>Tema / Copy</th><th>Estado</th>
  </tr></thead>
  <tbody>{rows_html}</tbody>
</table>"""
    else:
        parrilla_inner = ('<div style="padding:24px;text-align:center;color:#94a3b8;'
                          'font-size:.85rem;font-style:italic;">No hay parrilla registrada para este período.</div>')

    # ── Footer ────────────────────────────────────────────────────────────────
    footer_logo = (f'<img class="footer-logo" src="{logo_b64}" alt="{label}">' if logo_b64 else "")
    footer = f"""<div class="report-footer">
  {footer_logo}
  <div class="footer-tagline">{tagline}</div>
  <div class="footer-credit">Generado por RRSS Analytics · {fecha_gen}</div>
</div>"""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reporte RRSS — {label} — {mes_label} {año}</title>
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <style>{css}</style>
</head>
<body>
<div class="report-wrapper">
  {cover}
  <div class="body-wrapper">
    <div class="section-header">
      <div class="section-header-dot"></div>
      <div class="section-header-title">Resultados por Red Social — {mes_label} {año}</div>
    </div>
    {net_sections}
    <div class="section-header" style="margin-top:40px;">
      <div class="section-header-dot"></div>
      <div class="section-header-title">Parrilla de Contenido — {mes_label} {año}</div>
    </div>
    <div style="background:#fff;border-radius:14px;overflow:hidden;
    box-shadow:0 2px 8px rgba(0,0,0,.06);margin-bottom:32px;">
      {parrilla_inner}
    </div>
  </div>
  {footer}
</div>
</body>
</html>"""


# ── Streamlit UI ───────────────────────────────────────────────────────────────

def show_reporte():
    from auth import get_user
    user = get_user()
    if user.get("role") == "visita":
        st.warning("Tu rol no tiene acceso al generador de reportes.")
        return

    from datetime import date as _date
    hoy = _date.today()

    st.title("📊 Generador de Reporte")

    col_ctrl, col_info = st.columns([1, 1.4])

    with col_ctrl:
        st.markdown("#### Configuración")
        marca_key   = st.session_state.get("marca_activa", "k1")
        brand       = _load_brand(marca_key)
        marca_label = brand.get("label", marca_key.upper())
        st.markdown(f"**Marca:** {marca_label}")
        st.caption("Cambia la marca activa desde el selector del sidebar.")

        año_opts    = list(range(hoy.year + 1, 2022, -1))
        año_idx     = año_opts.index(hoy.year) if hoy.year in año_opts else 0
        año_sel     = st.selectbox("Año", año_opts, index=año_idx, key="rep_año")

        mes_opts    = list(MESES_ES.keys())
        mes_default = hoy.month - 1 if hoy.month > 1 else 12
        mes_idx     = mes_opts.index(mes_default) if mes_default in mes_opts else 0
        mes_sel     = st.selectbox("Mes", mes_opts, format_func=lambda m: MESES_ES[m],
                                   index=mes_idx, key="rep_mes")

        gen_btn = st.button("🔄 Generar Reporte", type="primary", use_container_width=True)

    with col_info:
        st.markdown("#### ¿Qué incluye?")
        st.info(
            "El reporte incluye **todos los KPIs** del Monitor + gráficas históricas "
            "y MoM por cada red social, más la parrilla del mes.\n\n"
            "📌 **Para PDF:** Descarga el HTML → ábrelo en Chrome → Ctrl+P → "
            "Guardar como PDF → activa *Gráficos de fondo*."
        )

    st.markdown("---")

    if gen_btn:
        marca_db = _MARCA_DB.get(marca_key, "Kabat One")
        with st.spinner(f"Generando reporte {marca_label} — {MESES_ES[mes_sel]} {año_sel}…"):
            try:
                data     = _get_report_data(marca_db, marca_key, año_sel, mes_sel)
                logo_b64 = _get_logo_b64(marca_key)
                html_str = _build_html_report(marca_key, año_sel, mes_sel, brand, data, logo_b64)
            except Exception as exc:
                st.error(f"Error al generar el reporte: {exc}")
                return

        filename = f"Reporte_{marca_label.replace(' ','_')}_{MESES_ES[mes_sel]}_{año_sel}.html"
        st.success("Reporte generado. Descárgalo y ábrelo en Chrome para mejor visualización.")

        st.download_button(
            "⬇️ Descargar Reporte HTML",
            data=html_str.encode("utf-8"),
            file_name=filename,
            mime="text/html",
            use_container_width=True,
            type="primary",
        )

        redes    = data.get("redes", [])
        parrilla = data.get("parrilla", [])
        c1, c2, c3 = st.columns(3)
        c1.metric("Redes con datos",  len(redes))
        c2.metric("Posts en parrilla", len(parrilla))
        c3.metric("Período", f"{MESES_ES[mes_sel]} {año_sel}")

        if redes:
            st.markdown("**Redes incluidas:** " + " · ".join(redes))

        if not redes and not parrilla:
            st.warning("No hay datos para este período. Importa archivos primero.")
