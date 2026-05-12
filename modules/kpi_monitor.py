# modules/kpi_monitor.py — Ingreso y monitor de KPIs

import streamlit as st
import pandas as pd

from config import METRICAS
from database import (
    get_metricas_mensuales, get_kpi_objetivos, get_kpi_manual,
    save_kpi_objetivos_bulk, save_kpi_manuales_bulk,
)
from utils import fmt_num, fmt_pct, kpi_status, mes_nombre, gauge_chart
import sync


def _kpi_card(m, dark):
    real    = m['real']
    meta    = m['meta']
    emoji   = m['emoji']
    color   = m['color']
    pct     = m['pct']
    icon    = m['icon']
    label   = m['label']
    bar_pct = min(int(pct), 100) if meta else 0

    bg    = '#0a1628'   if dark else '#ffffff'
    brd   = '#1e3a5f'   if dark else '#ccd9e8'
    txt   = '#dde3ee'   if dark else '#1a2d42'
    muted = '#5b8db8'   if dark else '#456080'
    bbg   = 'rgba(255,255,255,.07)' if dark else 'rgba(0,0,0,.07)'

    s_card      = f"background:{bg};border:1px solid {brd};border-top:3px solid {color};border-radius:12px;padding:18px 20px 18px;min-height:170px;box-shadow:0 2px 8px rgba(0,0,0,.1);"
    s_header    = f"font-size:.68rem;font-weight:700;color:{muted};text-transform:uppercase;letter-spacing:.1em;margin-bottom:10px;"
    s_value     = f"font-size:2.1rem;font-weight:800;color:{txt};line-height:1;letter-spacing:-.02em;"
    s_bar_bg    = f"background:{bbg};border-radius:4px;height:6px;margin:12px 0 10px;overflow:hidden;"
    s_bar_fg    = f"width:{bar_pct}%;background:{color};height:100%;border-radius:4px;"
    s_footer    = "display:flex;justify-content:space-between;align-items:flex-end;"
    s_meta_lbl  = f"font-size:.72rem;color:{muted};margin-bottom:2px;"
    s_meta_val  = f"font-size:1.45rem;font-weight:700;color:{txt};"
    s_pct       = f"font-size:1.65rem;font-weight:800;color:{color};letter-spacing:-.02em;"
    s_empty     = f"font-size:.8rem;color:{muted};margin-top:14px;"

    real_fmt = fmt_num(real)
    meta_fmt = fmt_num(meta)
    pct_fmt  = fmt_pct(pct)

    if meta:
        bottom = (
            f'<div style="{s_bar_bg}"><div style="{s_bar_fg}"></div></div>'
            f'<div style="{s_footer}">'
            f'<div>'
            f'<div style="{s_meta_lbl}">Meta</div>'
            f'<div style="{s_meta_val}">{meta_fmt}</div>'
            f'</div>'
            f'<div style="{s_pct}">{emoji} {pct_fmt}</div>'
            f'</div>'
        )
    else:
        bottom = f'<div style="{s_empty}">Sin meta establecida</div>'

    return (
        f'<div style="{s_card}">'
        f'<div style="{s_header}">{icon}&nbsp;{label}</div>'
        f'<div style="{s_value}">{real_fmt}</div>'
        f'{bottom}'
        f'</div>'
    )


def show_kpis():
    marca        = st.session_state.get('marca_activa', 'k1')
    marca_nombre = 'Kabat One' if marca == 'k1' else 'SYM'
    red          = st.session_state.get('f_red', 'LinkedIn')
    año          = st.session_state.get('f_año', 2026)
    mes          = st.session_state.get('f_mes', 4)
    can_edit     = st.session_state.get('current_user', {}).get('role') == 'admin'
    dark         = st.session_state.get('dark_mode', True)

    st.markdown(f"""
    <h2 style="color:#1e90ff;font-size:1.5rem;font-weight:700;margin-bottom:2px;">
      🎯 Monitor de KPIs — {marca_nombre}
    </h2>
    <p style="color:#5b8db8;font-size:.85rem;margin-top:0;">
      {red} · {mes_nombre(mes)} {año}
    </p>
    """, unsafe_allow_html=True)

    st.markdown("---")

    metricas_red = METRICAS.get(red, [])
    reales       = get_metricas_mensuales(marca_nombre, red, año, mes)
    objetivos    = get_kpi_objetivos(marca_nombre, red, año, mes)
    imp_real     = float(reales.get('impresiones', 0) or 0)
    vis_real     = float(reales.get('visualizaciones', 0) or 0)

    # ── Construir datos de todas las métricas ─────────────────────────────────
    metrics_data = []
    for m in metricas_red:
        key  = m['key']
        tipo = m['tipo']

        real = (get_kpi_manual(marca_nombre, red, key, año, mes)
                if tipo in ('manual', 'manual_50pct')
                else float(reales.get(key, 0) or 0))

        if tipo == 'auto_4pct':
            meta = round(imp_real * 0.04)
        elif tipo in ('auto_50pct', 'manual_50pct'):
            meta = round(vis_real * 0.50)
        else:
            meta = float(objetivos.get(key, 0) or 0)

        emoji, color, pct = kpi_status(real, meta)
        metrics_data.append({
            'key': key, 'tipo': tipo,
            'icon': m['icon'], 'label': m['label'],
            'real': real, 'meta': meta,
            'emoji': emoji, 'color': color, 'pct': pct,
        })

    # ── Vista admin: formulario editable ─────────────────────────────────────
    if can_edit:
        st.markdown("#### ✏️ Registrar Metas y Valores Manuales")
        st.caption("**auto_4pct**: meta = 4% impresiones · **manual_50pct**: meta = 50% visualizaciones.")

        with st.form(key=f"kpi_form_{red}_{año}_{mes}"):
            nuevas_metas    = {}
            nuevos_manuales = {}

            h = st.columns([3, 2, 2, 1.5, 1])
            h[0].markdown("**Métrica**")
            h[1].markdown("**Meta del mes**")
            h[2].markdown("**Real**")
            h[3].markdown("**Cumpl.**")
            h[4].markdown("**Tipo**")

            for md in metrics_data:
                key  = md['key']
                tipo = md['tipo']
                cols = st.columns([3, 2, 2, 1.5, 1])
                cols[0].markdown(f"{md['icon']} {md['label']}")
                cols[4].markdown(f"`{tipo}`")

                if tipo == 'auto_4pct':
                    cols[1].markdown(
                        f"<span style='color:#5b8db8;font-size:.78rem;'>"
                        f"Auto · {fmt_num(md['meta'])}</span>",
                        unsafe_allow_html=True,
                    )
                elif tipo in ('auto_50pct', 'manual_50pct'):
                    cols[1].markdown(
                        f"<span style='color:#5b8db8;font-size:.78rem;'>"
                        f"50% viz · {fmt_num(md['meta'])}</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    nuevas_metas[key] = cols[1].number_input(
                        f"meta_{key}", value=float(objetivos.get(key, 0) or 0),
                        min_value=0.0, step=1.0, label_visibility="collapsed",
                        key=f"meta_{key}_{red}_{año}_{mes}",
                    )

                if tipo in ('manual', 'manual_50pct'):
                    val_v = get_kpi_manual(marca_nombre, red, key, año, mes)
                    nuevos_manuales[key] = cols[2].number_input(
                        f"real_{key}", value=float(val_v or 0),
                        min_value=0.0, step=1.0, label_visibility="collapsed",
                        key=f"real_{key}_{red}_{año}_{mes}",
                    )
                else:
                    cols[2].markdown(
                        f"<span style='color:#5b8db8;font-size:.85rem;'>"
                        f"{fmt_num(md['real'])}</span>",
                        unsafe_allow_html=True,
                    )

                if md['meta']:
                    cols[3].markdown(
                        f"<span style='color:{md['color']};font-size:.9rem;font-weight:600;'>"
                        f"{md['emoji']} {fmt_pct(md['pct'])}</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    cols[3].markdown(
                        "<span style='color:#5b8db8;font-size:.8rem;'>—</span>",
                        unsafe_allow_html=True,
                    )

            submitted = st.form_submit_button(
                "💾 Guardar KPIs", type="primary", use_container_width=True
            )
            if submitted:
                save_kpi_objetivos_bulk(marca_nombre, red, año, mes, nuevas_metas)
                save_kpi_manuales_bulk(marca_nombre, red, año, mes, nuevos_manuales)
                if sync.github_configured():
                    sync.push()
                st.success("✅ KPIs guardados.")
                st.rerun()

        st.markdown("---")

        # Tabla resumen para admin
        st.markdown(f"#### 📊 Cumplimiento — {red} · {mes_nombre(mes)} {año}")
        tabla = [{
            'Est.':    md['emoji'],
            'Métrica': f"{md['icon']} {md['label']}",
            'Real':    fmt_num(md['real']),
            'Meta':    fmt_num(md['meta']) if md['meta'] else '—',
            'Cumpl.':  fmt_pct(md['pct']) if md['meta'] else '—',
            'Tipo':    md['tipo'],
        } for md in metrics_data]
        if tabla:
            st.dataframe(pd.DataFrame(tabla), use_container_width=True, hide_index=True)

    # ── Vista solo lectura: tarjetas visuales ─────────────────────────────────
    else:
        periodo = f"{red} · {mes_nombre(mes)} {año}"
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:16px;">'
            f'<span style="font-size:1.05rem;font-weight:700;color:#1e90ff;">📊 {periodo}</span>'
            f'<span style="font-size:.72rem;color:#5b8db8;">👁️ Vista de lectura</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Tarjetas en filas de 3
        for i in range(0, len(metrics_data), 3):
            row  = metrics_data[i:i + 3]
            cols = st.columns(len(row))
            for j, md in enumerate(row):
                with cols[j]:
                    st.markdown(_kpi_card(md, dark), unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

        st.markdown("---")

    # ── Gauges (ambas vistas) ─────────────────────────────────────────────────
    gauges = [
        {'label': md['label'], 'pct': md['pct'], 'color': md['color']}
        for md in metrics_data
        if md['meta'] and md['key'] not in ('vis_seguidores', 'vis_no_seguidores')
    ]
    if gauges:
        st.markdown("#### 🔵 Indicadores de cumplimiento")
        n     = min(len(gauges), 4)
        gcols = st.columns(n)
        for i, gd in enumerate(gauges[:n]):
            with gcols[i]:
                st.plotly_chart(
                    gauge_chart(gd['pct'], gd['label'], gd['color']),
                    use_container_width=True,
                )
