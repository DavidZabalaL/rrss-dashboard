# modules/dashboard.py — Resumen, MoM y tendencias

import streamlit as st
import plotly.express as px
import pandas as pd

from config import METRICAS, COLORS, CHART_COLORS
from database import (
    get_metricas_mensuales, get_metricas_historico_mensual,
    get_redes_con_datos, get_kpi_objetivos,
    get_kpi_manual, get_publicaciones_count,
)
from utils import (
    fmt_num, fmt_pct, kpi_status, mes_nombre,
    mes_etiqueta, apply_layout, metric_card_html,
)


def show_dashboard():
    marca        = st.session_state.get('marca_activa', 'k1')
    marca_nombre = 'Kabat One' if marca == 'k1' else 'SYM'
    red  = st.session_state.get('f_red', 'LinkedIn')
    año  = st.session_state.get('f_año', 2026)
    mes  = st.session_state.get('f_mes', 4)

    st.markdown(f"""
    <h2 style="color:#1e90ff;font-size:1.5rem;font-weight:700;margin-bottom:2px;">
      🏠 Dashboard — {marca_nombre}
    </h2>
    <p style="color:#5b8db8;font-size:.85rem;margin-top:0;">
      {red} · {mes_nombre(mes)} {año}
    </p>
    """, unsafe_allow_html=True)

    # ── Verificar datos ────────────────────────────────────────────────────────
    redes_disp = get_redes_con_datos(marca_nombre)
    if not redes_disp:
        st.info("📂 No hay datos. Ve a **Importar Datos** para subir tus primeros archivos.")
        return
    if red not in redes_disp:
        st.warning(f"No hay datos de **{red}** para **{marca_nombre}**.")
        return

    st.markdown("---")

    reales    = get_metricas_mensuales(marca_nombre, red, año, mes)
    objetivos = get_kpi_objetivos(marca_nombre, red, año, mes)

    # Mes anterior para deltas
    mes_ant = mes - 1 if mes > 1 else 12
    año_ant = año if mes > 1 else año - 1
    reales_ant = get_metricas_mensuales(marca_nombre, red, año_ant, mes_ant)

    # ── KPI Cards ──────────────────────────────────────────────────────────────
    metricas_red   = METRICAS.get(red, [])

    def _get_real(m, reales_dict, año_r, mes_r):
        """Obtiene el valor real según el tipo de métrica, igual que kpi_monitor."""
        tipo = m['tipo']
        key  = m['key']
        if tipo == 'contenido':
            return float(get_publicaciones_count(marca_nombre, red, año_r, mes_r))
        if tipo in ('manual', 'manual_50pct'):
            return get_kpi_manual(marca_nombre, red, key, año_r, mes_r)
        return float(reales_dict.get(key, 0) or 0)

    if not reales:
        st.warning(f"Sin datos para **{red}** · **{mes_nombre(mes)} {año}**.")
    else:
        metricas_cards = [m for m in metricas_red
                          if m['key'] != 'publicaciones'][:4]

        if metricas_cards:
            dark = st.session_state.get('dark_mode', True)
            cols = st.columns(len(metricas_cards))
            for col, m in zip(cols, metricas_cards):
                real = _get_real(m, reales, año, mes)
                prev = _get_real(m, reales_ant, año_ant, mes_ant)
                meta = float(objetivos.get(m['key'], 0) or 0)
                _, color, _ = kpi_status(real, meta)

                delta = ''
                if prev:
                    diff  = ((real - prev) / prev) * 100
                    arrow = '▲' if diff >= 0 else '▼'
                    delta = f"{arrow} {abs(diff):.1f}% vs {mes_nombre(mes_ant)}"

                with col:
                    st.markdown(
                        metric_card_html(f"{m['icon']} {m['label']}", fmt_num(real),
                                         delta, color if meta else COLORS['secondary'],
                                         dark=dark),
                        unsafe_allow_html=True,
                    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tendencia histórica ────────────────────────────────────────────────────
    hist_df = get_metricas_historico_mensual(marca_nombre, red)
    if not hist_df.empty:
        st.markdown("#### 📈 Tendencia histórica mensual")

        metricas_disp = hist_df['metrica'].unique().tolist()
        default_sel   = [m for m in metricas_disp
                         if m not in ('vis_seguidores', 'vis_no_seguidores')][:3]

        sel = st.multiselect(
            "Métricas a visualizar",
            metricas_disp, default=default_sel,
            key="dash_metricas_sel",
        )
        if sel:
            filt = hist_df[hist_df['metrica'].isin(sel)].copy()
            filt['etiqueta'] = filt.apply(
                lambda r: mes_etiqueta(int(r['año']), int(r['mes'])), axis=1
            )
            fig = px.line(
                filt, x='etiqueta', y='valor', color='metrica',
                markers=True, color_discrete_sequence=CHART_COLORS,
            )
            fig.update_traces(line=dict(width=2.5), marker=dict(size=7))
            apply_layout(fig, height=380)
            st.plotly_chart(fig, use_container_width=True)

    # ── Comparativa MoM (últimos 6 meses) ────────────────────────────────────
    if not hist_df.empty:
        st.markdown("#### 📊 Comparativa mes a mes — últimos 6 meses")
        top_keys = [m['key'] for m in metricas_red
                    if m['tipo'] not in ('manual_50pct',) and m['key'] != 'publicaciones'][:4]
        comp = hist_df[hist_df['metrica'].isin(top_keys)].copy()
        comp['etiqueta'] = comp.apply(
            lambda r: mes_etiqueta(int(r['año']), int(r['mes'])), axis=1
        )
        ultimas = comp.sort_values(['año', 'mes'])['etiqueta'].unique()[-6:]
        comp    = comp[comp['etiqueta'].isin(ultimas)]

        if not comp.empty:
            fig2 = px.bar(
                comp, x='etiqueta', y='valor', color='metrica',
                barmode='group', color_discrete_sequence=CHART_COLORS,
            )
            apply_layout(fig2, height=360)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Importa datos de varios meses para ver la comparativa.")

    # ── Cumplimiento del mes ───────────────────────────────────────────────────
    if objetivos and reales:
        st.markdown("#### 🎯 Cumplimiento de KPIs")
        imp_real = float(reales.get('impresiones', 0) or 0)
        vis_real = float(reales.get('visualizaciones', 0) or 0)
        kpi_rows = []
        for m in metricas_red:
            real = _get_real(m, reales, año, mes)
            if m['tipo'] == 'auto_4pct':
                meta = round(imp_real * 0.04)
            elif m['tipo'] in ('auto_50pct', 'manual_50pct'):
                meta = round(vis_real * 0.50)
            else:
                meta = float(objetivos.get(m['key'], 0) or 0)
            if not meta:
                continue
            emoji, _, pct = kpi_status(real, meta)
            kpi_rows.append({
                'Est.': emoji, 'Métrica': f"{m['icon']} {m['label']}",
                'Real': fmt_num(real), 'Meta': fmt_num(meta), 'Cumpl.': fmt_pct(pct),
            })
        if kpi_rows:
            st.dataframe(pd.DataFrame(kpi_rows), use_container_width=True, hide_index=True)
