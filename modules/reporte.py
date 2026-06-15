# modules/reporte.py — Generador de Reporte HTML con identidad de marca

import base64
import json
from datetime import datetime
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from database import (
    get_kpi_objetivos,
    get_metricas_historico_mensual,
    get_metricas_mensuales,
    get_parrilla_posts,
    get_redes_con_datos,
)

ROOT = Path(__file__).parent.parent

MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

# Marca key → nombre de marca para la DB
_MARCA_DB = {
    "k1": "Kabat One",
    "sym": "SYM",
}

# Marca key → archivo brand.json
_BRAND_JSON = {
    "k1": ROOT / "marca" / "kabat-one" / "brand.json",
    "sym": ROOT / "marca" / "sym-servicios" / "brand.json",
}

# Marca key → logo path(s): dark logo first (for report dark cover), day logo for body
_LOGO_PATHS = {
    "k1": ROOT / "assets" / "logo_k1.png",
    "sym": ROOT / "assets" / "logo_sym.png",
}

# Display name for networks
_RED_DISPLAY = {
    "LinkedIn": "LinkedIn",
    "Facebook": "Facebook / Instagram",
    "Instagram": "Facebook / Instagram",
}

# Metrics to show per network on the KPI cards (label, possible metric keys)
_KPI_METRICS = [
    ("Seguidores", ["seguidores", "followers", "page_fans", "connections"]),
    ("Publicaciones", ["publicaciones", "posts", "total_posts"]),
    ("Engagement", ["engagement_rate", "tasa_interaccion", "engagement"]),
    ("Alcance", ["alcance", "reach", "impresiones", "impressions"]),
]


# ── Data gathering ─────────────────────────────────────────────────────────────

def _load_brand(marca_key: str) -> dict:
    """Load brand.json for the given marca_key. Returns dict."""
    path = _BRAND_JSON.get(marca_key)
    if path and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    # Fallback minimal brand
    return {
        "label": marca_key.upper(),
        "tagline": "",
        "colors": {
            "primary": "#1e90ff",
            "secondary": "#24326A",
            "accent": "#31D8FF",
            "background_dark": "#060E40",
        },
        "rrss": {},
    }


def _get_logo_b64(marca_key: str) -> str:
    """Return base64 data URL for the brand logo. Supports PNG and SVG."""
    path = _LOGO_PATHS.get(marca_key)
    if path and path.exists():
        suffix = path.suffix.lower()
        if suffix == ".svg":
            mime = "image/svg+xml"
        elif suffix in (".jpg", ".jpeg"):
            mime = "image/jpeg"
        else:
            mime = "image/png"
        b64 = base64.b64encode(path.read_bytes()).decode()
        return f"data:{mime};base64,{b64}"
    return ""


def _find_metric(metricas: dict, candidates: list) -> float | None:
    """Find the first matching metric value from a list of candidate keys (case-insensitive)."""
    metricas_lower = {k.lower(): v for k, v in metricas.items()}
    for candidate in candidates:
        val = metricas_lower.get(candidate.lower())
        if val is not None:
            return val
    return None


def _get_report_data(marca: str, marca_key: str, año: int, mes: int) -> dict:
    """Gather all data needed for the report. Returns a structured dict."""
    redes = get_redes_con_datos(marca)

    networks_data = {}
    for red in redes:
        metricas = get_metricas_mensuales(marca, red, año, mes)
        historico_df = get_metricas_historico_mensual(marca, red)
        objetivos = get_kpi_objetivos(marca, red, año, mes)
        networks_data[red] = {
            "metricas": metricas,
            "historico": historico_df,
            "objetivos": objetivos,
        }

    parrilla = get_parrilla_posts(marca, año, mes)

    return {
        "redes": redes,
        "networks": networks_data,
        "parrilla": parrilla,
    }


# ── Chart builder ──────────────────────────────────────────────────────────────

def _build_historico_chart(red: str, historico_df, brand_colors: dict) -> str:
    """Build a Plotly line/bar chart for historical monthly metrics. Returns HTML div string."""
    primary = brand_colors.get("primary", "#1e90ff")
    secondary = brand_colors.get("secondary", "#24326A")
    accent = brand_colors.get("accent", "#31D8FF")

    if historico_df is None or historico_df.empty:
        return (
            "<div style='padding:30px;text-align:center;color:#888;"
            "border:1px dashed #ccc;border-radius:8px;font-size:.9rem;'>"
            "Sin datos históricos para esta red.</div>"
        )

    # Priority metrics to display
    priority_metrics = ["seguidores", "followers", "connections", "page_fans",
                        "alcance", "reach", "impresiones", "impressions"]

    metrics_available = historico_df["metrica"].unique().tolist()

    # Pick up to 2 metrics to chart
    selected = []
    for pm in priority_metrics:
        for m in metrics_available:
            if pm.lower() in m.lower() and m not in selected:
                selected.append(m)
                break
        if len(selected) >= 2:
            break
    if not selected:
        selected = metrics_available[:2]

    if not selected:
        return (
            "<div style='padding:30px;text-align:center;color:#888;"
            "border:1px dashed #ccc;border-radius:8px;font-size:.9rem;'>"
            "Sin métricas disponibles para graficar.</div>"
        )

    colors_list = [primary, accent, secondary, "#a0a0a0"]
    fig = go.Figure()

    for i, metrica in enumerate(selected):
        df_m = historico_df[historico_df["metrica"] == metrica].sort_values(["año", "mes"])
        if df_m.empty:
            continue
        x_labels = [f"{MESES_ES.get(int(r['mes']), str(r['mes']))[:3]} {str(r['año'])[2:]}"
                    for _, r in df_m.iterrows()]
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=df_m["valor"].tolist(),
            mode="lines+markers",
            name=metrica.replace("_", " ").title(),
            line=dict(color=colors_list[i % len(colors_list)], width=2.5),
            marker=dict(size=6, color=colors_list[i % len(colors_list)]),
        ))

    fig.update_layout(
        height=280,
        margin=dict(l=40, r=20, t=20, b=40),
        paper_bgcolor="white",
        plot_bgcolor="#fafbfc",
        font=dict(family="Inter, sans-serif", size=11, color="#444"),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(size=10),
        ),
        xaxis=dict(
            showgrid=True, gridcolor="#eeeeee",
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            showgrid=True, gridcolor="#eeeeee",
            tickfont=dict(size=10),
        ),
    )

    return fig.to_html(full_html=False, include_plotlyjs=False)


# ── HTML report builder ────────────────────────────────────────────────────────

def _build_html_report(
    marca_key: str,
    año: int,
    mes: int,
    brand: dict,
    data: dict,
    logo_b64: str,
) -> str:
    """Build and return a complete, self-contained HTML report string."""

    colors = brand.get("colors", {})
    primary    = colors.get("primary", "#1e90ff")
    secondary  = colors.get("secondary", "#24326A")
    accent     = colors.get("accent", "#31D8FF")
    dark_bg    = colors.get("background_dark", "#060E40")
    label      = brand.get("label", marca_key.upper())
    tagline    = brand.get("tagline", "")
    mes_label  = MESES_ES.get(mes, str(mes))
    fecha_gen  = datetime.now().strftime("%d/%m/%Y %H:%M")

    # ── CSS ──────────────────────────────────────────────────────────────────
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
    max-width: 900px;
    margin: 0 auto;
    background: #ffffff;
    box-shadow: 0 4px 32px rgba(0,0,0,.18);
}}

/* ── Cover ── */
.cover {{
    background: linear-gradient(145deg, {dark_bg} 0%, {secondary} 60%, {primary}33 100%);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 48px;
    page-break-after: always;
    break-after: page;
    position: relative;
    overflow: hidden;
}}
.cover::before {{
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse at 70% 30%, {accent}18 0%, transparent 60%);
    pointer-events: none;
}}
.cover-logo {{
    max-width: 240px;
    max-height: 120px;
    object-fit: contain;
    margin-bottom: 48px;
    filter: drop-shadow(0 4px 16px rgba(0,0,0,.3));
}}
.cover-title {{
    font-size: 2.6rem;
    font-weight: 800;
    color: #ffffff;
    text-align: center;
    letter-spacing: -.02em;
    line-height: 1.15;
    margin-bottom: 16px;
    text-shadow: 0 2px 8px rgba(0,0,0,.3);
}}
.cover-subtitle {{
    font-size: 1.45rem;
    font-weight: 600;
    color: {accent};
    text-align: center;
    letter-spacing: .04em;
    text-transform: uppercase;
    margin-bottom: 12px;
}}
.cover-brand {{
    font-size: 1rem;
    font-weight: 500;
    color: rgba(255,255,255,.7);
    text-align: center;
    margin-bottom: 8px;
}}
.cover-tagline {{
    position: absolute;
    bottom: 40px;
    font-size: .85rem;
    color: rgba(255,255,255,.5);
    letter-spacing: .08em;
    text-align: center;
    font-style: italic;
}}
.cover-divider {{
    width: 60px;
    height: 3px;
    background: {accent};
    border-radius: 2px;
    margin: 24px auto;
}}

/* ── Sections ── */
.section {{
    padding: 48px 52px 40px;
    border-bottom: 1px solid #e8edf4;
}}
.section:last-of-type {{ border-bottom: none; }}

.section-title {{
    font-size: 1.3rem;
    font-weight: 700;
    color: {secondary};
    border-left: 4px solid {primary};
    padding-left: 14px;
    margin-bottom: 28px;
    letter-spacing: -.01em;
}}
.section-subtitle {{
    font-size: 1rem;
    font-weight: 600;
    color: {primary};
    margin: 28px 0 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.section-subtitle::before {{
    content: '';
    display: inline-block;
    width: 8px; height: 8px;
    background: {accent};
    border-radius: 50%;
    flex-shrink: 0;
}}

/* ── KPI Cards ── */
.kpi-row {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 28px;
}}
@media (max-width: 680px) {{
    .kpi-row {{ grid-template-columns: repeat(2, 1fr); }}
}}
.kpi-card {{
    background: #ffffff;
    border: 1px solid #e0e8f2;
    border-top: 3px solid {primary};
    border-radius: 12px;
    padding: 18px 16px 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,.06);
    text-align: center;
}}
.kpi-value {{
    font-size: 2.5rem;
    font-weight: 800;
    color: {primary};
    line-height: 1;
    letter-spacing: -.03em;
    margin-bottom: 6px;
}}
.kpi-label {{
    font-size: .65rem;
    font-weight: 700;
    color: #8a9bb0;
    text-transform: uppercase;
    letter-spacing: .12em;
}}
.kpi-network {{
    font-size: .72rem;
    font-weight: 600;
    color: {secondary};
    margin-top: 4px;
    opacity: .75;
}}

/* ── Network section ── */
.network-block {{
    margin-bottom: 36px;
    background: #f8fafc;
    border: 1px solid #e8edf4;
    border-radius: 12px;
    overflow: hidden;
}}
.network-header {{
    background: linear-gradient(90deg, {secondary}22 0%, transparent 100%);
    border-bottom: 1px solid #e8edf4;
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 10px;
}}
.network-name {{
    font-size: .95rem;
    font-weight: 700;
    color: {secondary};
    letter-spacing: -.01em;
}}
.network-dot {{
    width: 8px; height: 8px;
    background: {primary};
    border-radius: 50%;
}}
.network-chart-area {{
    padding: 16px 16px 8px;
    background: #ffffff;
}}
.no-data-msg {{
    padding: 30px;
    text-align: center;
    color: #9aacbe;
    font-size: .88rem;
    font-style: italic;
}}

/* ── Parrilla table ── */
.parrilla-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: .8rem;
    margin-top: 8px;
}}
.parrilla-table thead tr {{
    background: {primary};
    color: #ffffff;
}}
.parrilla-table thead th {{
    padding: 10px 12px;
    font-weight: 600;
    font-size: .72rem;
    letter-spacing: .06em;
    text-transform: uppercase;
    text-align: left;
    white-space: nowrap;
}}
.parrilla-table tbody tr:nth-child(even) {{
    background: #f5f8fc;
}}
.parrilla-table tbody tr:nth-child(odd) {{
    background: #ffffff;
}}
.parrilla-table tbody tr:hover {{
    background: {primary}12;
}}
.parrilla-table tbody td {{
    padding: 8px 12px;
    border-bottom: 1px solid #edf1f7;
    color: #2a3d55;
    vertical-align: middle;
}}
.parrilla-table tbody td:first-child {{
    font-weight: 600;
    color: {secondary};
    white-space: nowrap;
}}
.estado-badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 20px;
    font-size: .68rem;
    font-weight: 600;
    letter-spacing: .04em;
    text-transform: uppercase;
}}
.estado-publicado {{ background: #d4f0e0; color: #1a6e35; }}
.estado-programado {{ background: #ddeaf7; color: #1060cc; }}
.estado-borrador    {{ background: #f0f0f0; color: #666; }}
.estado-cancelado   {{ background: #fdecea; color: #c0392b; }}
.estado-revision    {{ background: #fff3cd; color: #856404; }}

/* ── Footer ── */
.report-footer {{
    background: {dark_bg};
    padding: 32px 52px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
}}
.footer-logo {{
    max-height: 40px;
    max-width: 140px;
    object-fit: contain;
    opacity: .9;
}}
.footer-tagline {{
    font-size: .78rem;
    color: rgba(255,255,255,.55);
    font-style: italic;
    flex: 1;
    text-align: center;
}}
.footer-credit {{
    font-size: .72rem;
    color: rgba(255,255,255,.4);
    text-align: right;
    white-space: nowrap;
}}

/* ── Print ── */
@media print {{
    .no-print {{ display: none !important; }}
    body {{ background: white; }}
    .report-wrapper {{ box-shadow: none; }}
    .cover {{ min-height: 100vh; page-break-after: always; }}
    .section {{ page-break-inside: avoid; }}
    .network-block {{ page-break-inside: avoid; }}
}}
"""

    # ── Cover page ──────────────────────────────────────────────────────────
    if logo_b64:
        cover_logo_html = f'<img class="cover-logo" src="{logo_b64}" alt="{label} logo">'
    else:
        cover_logo_html = f'<div style="font-size:1.8rem;font-weight:800;color:{accent};margin-bottom:48px;">{label}</div>'

    cover_html = f"""
<div class="cover">
    {cover_logo_html}
    <div class="cover-title">Reporte de Redes Sociales</div>
    <div class="cover-divider"></div>
    <div class="cover-subtitle">{mes_label} {año}</div>
    <div class="cover-brand">{label}</div>
    <div class="cover-tagline">{tagline}</div>
</div>
"""

    # ── Executive summary ────────────────────────────────────────────────────
    kpi_blocks_html = ""
    for red in data["redes"]:
        net_data = data["networks"].get(red, {})
        metricas = net_data.get("metricas", {})
        display_name = _RED_DISPLAY.get(red, red)

        kpi_cards_html = ""
        for kpi_label, candidates in _KPI_METRICS:
            val = _find_metric(metricas, candidates)
            if val is not None:
                # Format value
                if "rate" in " ".join(candidates).lower() or "tasa" in " ".join(candidates).lower():
                    if val < 2:
                        formatted = f"{val:.2f}%"
                    else:
                        formatted = f"{val:.1f}%"
                elif val >= 1_000_000:
                    formatted = f"{val/1_000_000:.1f}M"
                elif val >= 1_000:
                    formatted = f"{val:,.0f}"
                else:
                    formatted = f"{int(val):,}" if val == int(val) else f"{val:.1f}"
            else:
                formatted = "—"

            kpi_cards_html += f"""
<div class="kpi-card">
    <div class="kpi-value">{formatted}</div>
    <div class="kpi-label">{kpi_label}</div>
    <div class="kpi-network">{display_name}</div>
</div>"""

        kpi_blocks_html += f"""
<div class="section-subtitle">{display_name}</div>
<div class="kpi-row">{kpi_cards_html}</div>
"""

    if not data["redes"]:
        kpi_blocks_html = '<p class="no-data-msg">No hay datos disponibles para este período.</p>'

    summary_html = f"""
<div class="section">
    <div class="section-title">Resumen Ejecutivo</div>
    {kpi_blocks_html}
</div>
"""

    # ── Rendimiento por red ──────────────────────────────────────────────────
    network_sections_html = ""
    for red in data["redes"]:
        net_data = data["networks"].get(red, {})
        historico_df = net_data.get("historico")
        display_name = _RED_DISPLAY.get(red, red)
        chart_html = _build_historico_chart(red, historico_df, colors)

        network_sections_html += f"""
<div class="network-block">
    <div class="network-header">
        <div class="network-dot"></div>
        <div class="network-name">{display_name}</div>
    </div>
    <div class="network-chart-area">
        {chart_html}
    </div>
</div>
"""

    if not data["redes"]:
        network_sections_html = '<p class="no-data-msg">No hay redes con datos importados.</p>'

    rendimiento_html = f"""
<div class="section">
    <div class="section-title">Rendimiento por Red Social</div>
    {network_sections_html}
</div>
"""

    # ── Parrilla del mes ─────────────────────────────────────────────────────
    parrilla = data.get("parrilla", [])

    if parrilla:
        rows_html = ""
        for post in parrilla:
            fecha  = post.get("fecha", "")
            dia    = post.get("dia_semana", "")
            tipo   = post.get("formato") or post.get("tipo_dia", "")
            red_p  = post.get("red", "")  # may not exist in parrilla_posts schema
            tema_raw = post.get("tema") or post.get("copy_linkedin") or ""
            tema   = (tema_raw[:80] + "…") if len(tema_raw) > 80 else tema_raw
            estado = post.get("estado", "Borrador")

            estado_lower = estado.lower().replace(" ", "")
            estado_class = "estado-borrador"
            if "publicad" in estado_lower:
                estado_class = "estado-publicado"
            elif "programad" in estado_lower:
                estado_class = "estado-programado"
            elif "cancelad" in estado_lower:
                estado_class = "estado-cancelado"
            elif "revisión" in estado_lower or "revision" in estado_lower:
                estado_class = "estado-revision"

            rows_html += f"""
<tr>
    <td>{fecha}</td>
    <td>{dia}</td>
    <td>{tipo}</td>
    <td>{red_p}</td>
    <td style="max-width:280px;">{tema}</td>
    <td><span class="estado-badge {estado_class}">{estado}</span></td>
</tr>"""

        parrilla_content_html = f"""
<table class="parrilla-table">
    <thead>
        <tr>
            <th>Fecha</th>
            <th>Día</th>
            <th>Tipo</th>
            <th>Red Social</th>
            <th>Tema / Copy</th>
            <th>Estado</th>
        </tr>
    </thead>
    <tbody>
        {rows_html}
    </tbody>
</table>
"""
    else:
        parrilla_content_html = '<p class="no-data-msg">No hay parrilla registrada para este período.</p>'

    parrilla_html = f"""
<div class="section">
    <div class="section-title">Contenido Publicado — {mes_label} {año}</div>
    {parrilla_content_html}
</div>
"""

    # ── Footer ───────────────────────────────────────────────────────────────
    if logo_b64:
        footer_logo_html = f'<img class="footer-logo" src="{logo_b64}" alt="{label}">'
    else:
        footer_logo_html = ""

    footer_html = f"""
<div class="report-footer">
    {footer_logo_html}
    <div class="footer-tagline">{tagline}</div>
    <div class="footer-credit">Generado por RRSS Analytics · {fecha_gen}</div>
</div>
"""

    # ── Assemble full HTML ───────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte RRSS — {label} — {mes_label} {año}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
{css}
    </style>
</head>
<body>
<div class="report-wrapper">
    {cover_html}
    {summary_html}
    {rendimiento_html}
    {parrilla_html}
    {footer_html}
</div>
</body>
</html>
"""
    return html


# ── Streamlit UI ───────────────────────────────────────────────────────────────

def show_reporte():
    """Streamlit page: HTML report generator."""
    from auth import get_user

    user = get_user()
    role = user.get("role", "viewer")

    st.title("📊 Generador de Reporte")

    if role == "visita":
        st.warning(
            "⚠️ Tu rol de **visita** no tiene acceso al generador de reportes. "
            "Contacta al administrador para obtener permisos."
        )
        return

    from datetime import date as _date
    hoy = _date.today()

    col_ctrl, col_info = st.columns([1, 1.4])

    with col_ctrl:
        st.markdown("#### Configuración del Reporte")

        # Marca (driven by session state)
        marca_key = st.session_state.get("marca_activa", "k1")
        brand = _load_brand(marca_key)
        marca_label = brand.get("label", marca_key.upper())

        st.markdown(f"**Marca:** {marca_label}")
        st.caption("Cambia la marca activa desde el selector en el sidebar.")

        año_opts = list(range(hoy.year + 1, 2022, -1))
        año_default = hoy.year
        año_idx = año_opts.index(año_default) if año_default in año_opts else 0

        año_sel = st.selectbox(
            "Año",
            año_opts,
            index=año_idx,
            key="rep_año",
        )

        mes_opts = list(MESES_ES.keys())
        mes_default = hoy.month - 1 if hoy.month > 1 else 12
        mes_idx = mes_opts.index(mes_default) if mes_default in mes_opts else 0

        mes_sel = st.selectbox(
            "Mes",
            mes_opts,
            format_func=lambda m: MESES_ES[m],
            index=mes_idx,
            key="rep_mes",
        )

        generate_btn = st.button("🔄 Generar Reporte", type="primary", use_container_width=True)

    with col_info:
        st.markdown("#### Acerca del Reporte")
        st.info(
            "El reporte se genera como un archivo **HTML autocontenido** con toda la "
            "información de KPIs, métricas históricas y parrilla del mes seleccionado.\n\n"
            "📌 **Para obtener el PDF:**\n"
            "1. Descarga el archivo HTML\n"
            "2. Ábrelo en **Google Chrome**\n"
            "3. Presiona **Ctrl+P** (o Cmd+P en Mac)\n"
            "4. Selecciona **Guardar como PDF**\n"
            "5. Activa \"Gráficos de fondo\" en opciones"
        )

    st.markdown("---")

    if generate_btn:
        marca_db = _MARCA_DB.get(marca_key, "Kabat One")

        with st.spinner(f"Generando reporte para {marca_label} — {MESES_ES[mes_sel]} {año_sel}…"):
            try:
                data = _get_report_data(marca_db, marca_key, año_sel, mes_sel)
                logo_b64 = _get_logo_b64(marca_key)
                html_str = _build_html_report(marca_key, año_sel, mes_sel, brand, data, logo_b64)
            except Exception as exc:
                st.error(f"Error al generar el reporte: {exc}")
                return

        filename = f"Reporte_{marca_label.replace(' ', '_')}_{MESES_ES[mes_sel]}_{año_sel}.html"

        st.success(
            f"Reporte generado correctamente. "
            f"Descárgalo y ábrelo en **Chrome** para mejor visualización y conversión a PDF."
        )

        st.download_button(
            label="⬇️ Descargar Reporte HTML",
            data=html_str.encode("utf-8"),
            file_name=filename,
            mime="text/html",
            use_container_width=True,
            type="primary",
        )

        # Preview stats
        redes = data.get("redes", [])
        parrilla = data.get("parrilla", [])

        st.markdown("#### Vista previa del contenido incluido")
        c1, c2, c3 = st.columns(3)
        c1.metric("Redes con datos", len(redes))
        c2.metric("Posts en parrilla", len(parrilla))
        c3.metric("Período", f"{MESES_ES[mes_sel]} {año_sel}")

        if redes:
            st.markdown("**Redes incluidas:** " + " · ".join(
                _RED_DISPLAY.get(r, r) for r in redes
            ))

        if not redes and not parrilla:
            st.warning(
                "No se encontraron datos para este período. "
                "El reporte se generó pero estará vacío. "
                "Importa datos primero desde **📁 Importar Datos**."
            )
