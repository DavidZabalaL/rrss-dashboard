# modules/analista.py — Analista de Contenido (Top / Bottom posts)

import streamlit as st
import plotly.express as px
import pandas as pd

from config import CHART_COLORS
from database import get_contenido_posts, get_contenido_redes
from utils import fmt_num, mes_nombre, apply_layout

_METRIC_LABELS = {
    'impresiones':      '👁️ Impresiones',
    'clics':            '🖱️ Clics',
    'reacciones':       '❤️ Reacciones',
    'comentarios':      '💬 Comentarios',
    'compartidos':      '🔁 Compartidos',
    'tasa_interaccion': '📈 Tasa Interacción',
    'visualizaciones':  '🎬 Visualizaciones',
}


def show_analista():
    _role = st.session_state.get('current_user', {}).get('role', 'visita')
    if _role == 'visita':
        st.warning("⛔ Vista no disponible en modo lectura.")
        return

    marca        = st.session_state.get('marca_activa', 'k1')
    marca_nombre = 'Kabat One' if marca == 'k1' else 'SYM'
    red  = st.session_state.get('f_red', 'LinkedIn')
    año  = st.session_state.get('f_año', 2026)
    mes  = st.session_state.get('f_mes', 4)

    st.markdown(f"""
    <h2 style="color:#1e90ff;font-size:1.5rem;font-weight:700;margin-bottom:2px;">
      🔍 Analista de Contenido — {marca_nombre}
    </h2>
    <p style="color:#5b8db8;font-size:.85rem;margin-top:0;">
      {red} · {mes_nombre(mes)} {año} — Cambia los filtros en el panel lateral.
    </p>
    """, unsafe_allow_html=True)

    redes_disp = get_contenido_redes(marca_nombre)
    if not redes_disp:
        st.info("📂 No hay datos de contenido. Importa un archivo `k1_contenido.xlsx` o `sym_contenido.xlsx`.")
        return

    col_periodo, col_metrica = st.columns([2, 2])
    with col_periodo:
        todo_periodo = st.checkbox("Todo el año", value=False, key="anal_todo")
        if todo_periodo:
            st.caption(f"Mostrando todo {año}")
    with col_metrica:
        metrica_rank = st.selectbox(
            "Ordenar por",
            list(_METRIC_LABELS.keys()),
            format_func=lambda k: _METRIC_LABELS[k],
            key="anal_metrica",
        )

    st.markdown("---")

    df = get_contenido_posts(
        marca_nombre, red, año,
        mes=None if todo_periodo else mes,
    )

    if df.empty:
        st.warning("No hay publicaciones para los filtros seleccionados.")
        return

    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    if metrica_rank in df.columns:
        df = df.sort_values(metrica_rank, ascending=False).reset_index(drop=True)

    # ── Resumen ───────────────────────────────────────────────────────────────
    periodo_lbl = f"Todo {año}" if todo_periodo else f"{mes_nombre(mes)} {año}"
    st.markdown(f"#### 📋 Resumen — {red} · {periodo_lbl}")

    resumen_cols = [c for c in ['impresiones', 'clics', 'reacciones', 'comentarios', 'compartidos']
                    if c in df.columns]
    if resumen_cols:
        rcols = st.columns(len(resumen_cols))
        for col, met in zip(rcols, resumen_cols):
            col.metric(_METRIC_LABELS.get(met, met), fmt_num(df[met].sum()))

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Top 5 ─────────────────────────────────────────────────────────────────
    st.markdown("#### 🏆 Top 5 — Mejores publicaciones")
    df_top5 = df.head(5)
    _show_posts_table(df_top5)

    # ── Bottom 5 ──────────────────────────────────────────────────────────────
    st.markdown("#### 📉 Bottom 5 — Menor desempeño")
    top_indices = set(df_top5.index)
    df_remaining = df.drop(index=top_indices)
    if not df_remaining.empty:
        bottom = df_remaining.nsmallest(5, metrica_rank) if metrica_rank in df_remaining.columns else df_remaining.tail(5)
        if metrica_rank in bottom.columns:
            bottom = bottom.sort_values(metrica_rank)
        _show_posts_table(bottom)
    else:
        st.caption("No hay publicaciones adicionales fuera del Top 5.")

    # ── Distribución por tipo ─────────────────────────────────────────────────
    if 'tipo' in df.columns and df['tipo'].notna().any() and metrica_rank in df.columns:
        st.markdown("#### 🍩 Por tipo de publicación")
        tipo_df = (
            df.groupby('tipo')[metrica_rank].sum()
            .reset_index().sort_values(metrica_rank, ascending=False)
        )
        if not tipo_df.empty and tipo_df[metrica_rank].sum() > 0:
            fig = px.pie(tipo_df, names='tipo', values=metrica_rank,
                         color_discrete_sequence=CHART_COLORS, hole=0.5)
            fig.update_traces(textposition='inside', textinfo='percent+label',
                              textfont_size=12)
            apply_layout(fig, height=320)
            fig.update_layout(showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

    # ── Exportar tabla ────────────────────────────────────────────────────────
    export_cols = [c for c in ['fecha', 'tipo', 'titulo', 'impresiones', 'reacciones',
                               'comentarios', 'clics', 'tasa_interaccion', 'url']
                   if c in df.columns]
    export_df = df[export_cols].copy()
    if 'fecha' in export_df.columns:
        export_df['fecha'] = export_df['fecha'].astype(str).str[:10]
    periodo_lbl_file = f"{año}" if todo_periodo else f"{mes_nombre(mes)}{año}"
    st.download_button(
        f"📥 Descargar tabla ({len(df)} posts)",
        data=export_df.to_csv(index=False).encode('utf-8'),
        file_name=f"Analista_{marca_nombre.replace(' ','_')}_{red}_{periodo_lbl_file}.csv",
        mime="text/csv",
        use_container_width=False,
        key="btn_analista_export",
    )

    # ── Scatter Impresiones vs Tasa ───────────────────────────────────────────
    if 'impresiones' in df.columns and 'tasa_interaccion' in df.columns:
        scatter_df = df[df['impresiones'] > 0].copy()
        if 'titulo' in scatter_df.columns:
            scatter_df['titulo_corto'] = scatter_df['titulo'].str[:60] + "…"
        if not scatter_df.empty:
            st.markdown("#### 🔵 Impresiones vs Tasa de Interacción")
            fig2 = px.scatter(
                scatter_df, x='impresiones', y='tasa_interaccion',
                hover_name='titulo_corto' if 'titulo_corto' in scatter_df.columns else None,
                color='tipo' if 'tipo' in scatter_df.columns else None,
                size='reacciones' if 'reacciones' in scatter_df.columns else None,
                color_discrete_sequence=CHART_COLORS,
            )
            fig2.update_traces(marker=dict(opacity=0.8, line=dict(width=1, color='#1e90ff')))
            apply_layout(fig2, title="Cada burbuja = 1 publicación", height=380)
            st.plotly_chart(fig2, use_container_width=True)


def _show_posts_table(df):
    cols_show = [c for c in ['fecha', 'tipo', 'titulo', 'impresiones', 'reacciones',
                              'comentarios', 'clics', 'tasa_interaccion', 'url']
                 if c in df.columns]
    display_df = df[cols_show].copy()
    if 'fecha' in display_df.columns:
        display_df['fecha'] = display_df['fecha'].astype(str).str[:10]
    rename_map = {
        'fecha': 'Fecha', 'tipo': 'Tipo', 'titulo': 'Título',
        'impresiones': '👁️ Imp.', 'reacciones': '❤️ Reac.',
        'comentarios': '💬 Com.', 'clics': '🖱️ Clics',
        'tasa_interaccion': '📈 Tasa %', 'url': 'URL',
    }
    display_df = display_df.rename(columns={k: v for k, v in rename_map.items() if k in display_df.columns})
    if 'Título' in display_df.columns:
        display_df['Título'] = display_df['Título'].str[:80]
    st.dataframe(
        display_df, use_container_width=True, hide_index=True,
        column_config={'URL': st.column_config.LinkColumn("URL")} if 'URL' in display_df.columns else {},
    )
