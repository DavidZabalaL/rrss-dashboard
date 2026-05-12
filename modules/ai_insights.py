# modules/ai_insights.py — Generador de Script para IA

import html as _html
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

from config import METRICAS
from database import (
    get_metricas_mensuales, get_kpi_objetivos,
    get_kpi_manual, get_contenido_posts, get_contenido_redes,
)
from utils import fmt_num, fmt_pct, kpi_status, mes_nombre


def show_insights():
    marca        = st.session_state.get('marca_activa', 'k1')
    marca_nombre = 'Kabat One' if marca == 'k1' else 'SYM'
    red  = st.session_state.get('f_red', 'LinkedIn')
    año  = st.session_state.get('f_año', 2026)
    mes  = st.session_state.get('f_mes', 4)

    st.markdown(f"""
    <h2 style="color:#1e90ff;font-size:1.5rem;font-weight:700;margin-bottom:2px;">
      🤖 Insights para IA — {marca_nombre}
    </h2>
    <p style="color:#5b8db8;font-size:.85rem;margin-top:0;">
      {red} · {mes_nombre(mes)} {año} — Cambia los filtros en el panel lateral.
    </p>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Recopilar datos ──────────────────────────────────────────────────────
    reales       = get_metricas_mensuales(marca_nombre, red, año, mes)
    objetivos    = get_kpi_objetivos(marca_nombre, red, año, mes)
    metricas_red = METRICAS.get(red, [])

    redes_contenido = get_contenido_redes(marca_nombre)
    posts_df = pd.DataFrame()
    if red in redes_contenido:
        posts_df = get_contenido_posts(marca_nombre, red, año, mes)

    # ── Resumen de KPIs ──────────────────────────────────────────────────────
    vis_real = float(reales.get('visualizaciones', 0) or 0)
    kpi_lines = []
    for m in metricas_red:
        key  = m['key']
        tipo = m['tipo']
        real = get_kpi_manual(marca_nombre, red, key, año, mes) \
               if tipo in ('manual', 'manual_50pct') else float(reales.get(key, 0) or 0)
        if tipo == 'auto_4pct':
            meta = round(float(reales.get('impresiones', 0) or 0) * 0.04)
        elif tipo in ('auto_50pct', 'manual_50pct'):
            meta = round(vis_real * 0.50)
        else:
            meta = float(objetivos.get(key, 0) or 0)
        _, _, pct = kpi_status(real, meta)
        pct_str = fmt_pct(pct) if meta else "sin meta"
        kpi_lines.append(
            f"  - {m['label']}: {fmt_num(real)} "
            f"(meta: {fmt_num(meta) if meta else 'N/D'}, cumplimiento: {pct_str})"
        )
    kpi_texto = "\n".join(kpi_lines) or "  (Sin datos de KPI para este período)"

    # ── Top 5 / Bottom 5 ────────────────────────────────────────────────────
    top5_texto = "(No hay datos de publicaciones individuales cargados)"
    bot5_texto = "(No hay datos de publicaciones individuales cargados)"
    tendencias_texto = ""

    if not posts_df.empty:
        sort_col = 'tasa_interaccion' if 'tasa_interaccion' in posts_df.columns else 'impresiones'
        df_sorted = posts_df.sort_values(sort_col, ascending=False).reset_index(drop=True)

        def _post_line(row, i):
            titulo = str(row.get('titulo', ''))[:80] or "(sin título)"
            tipo   = str(row.get('tipo', '')) or "—"
            imp    = fmt_num(row.get('impresiones', 0))
            reac   = fmt_num(row.get('reacciones',  0))
            tasa_v = float(row.get('tasa_interaccion', 0) or 0)
            tasa   = fmt_pct(tasa_v * 100 if tasa_v <= 1 else tasa_v)
            return f"  {i}. [{tipo}] \"{titulo}\" — Imp: {imp} | Reac: {reac} | Tasa: {tasa}"

        top5 = [_post_line(r, i+1) for i, (_, r) in enumerate(df_sorted.head(5).iterrows())]
        bot5_df = df_sorted.tail(5)
        if sort_col in bot5_df.columns:
            bot5_df = bot5_df.sort_values(sort_col)
        bot5 = [_post_line(r, i+1) for i, (_, r) in enumerate(bot5_df.iterrows())]
        top5_texto = "\n".join(top5)
        bot5_texto = "\n".join(bot5)

        if 'tipo' in posts_df.columns:
            tipo_res = posts_df.groupby('tipo')[[sort_col]].mean().sort_values(sort_col, ascending=False)
            tendencias_lineas = [
                f"  - {t}: promedio tasa {fmt_pct(v*100 if v <= 1 else v)}"
                for t, v in zip(tipo_res.index, tipo_res[sort_col])
            ]
            tendencias_texto = "\n\n📌 RENDIMIENTO POR TIPO DE CONTENIDO:\n" + "\n".join(tendencias_lineas)

    # ── Script ───────────────────────────────────────────────────────────────
    script = f"""Actúa como un especialista senior en redes sociales y creación de contenido digital con más de 10 años de experiencia en estrategia de marca, crecimiento orgánico y análisis de métricas. Tu objetivo es analizar los datos de rendimiento que te comparto, identificar patrones, diagnosticar la salud de la cuenta y proponer acciones concretas para mejorar los resultados.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 DATOS DE RENDIMIENTO — {marca_nombre} | {red} | {mes_nombre(mes)} {año}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 KPIs DEL MES:
{kpi_texto}

🏆 TOP 5 PUBLICACIONES (mayor engagement):
{top5_texto}

📉 BOTTOM 5 PUBLICACIONES (menor engagement):
{bot5_texto}{tendencias_texto}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Con base en los datos anteriores, proporciona el siguiente análisis:

1. DIAGNÓSTICO DE SALUD (califica: Excelente / Bueno / Regular / Crítico)
   Evalúa el estado general de la cuenta basándote en los números. Señala qué métricas están por encima o debajo del benchmark típico para {red}. ¿Hay tendencias de crecimiento o declive?

2. ANÁLISIS DE CONTENIDO GANADOR VS PERDEDOR
   ¿Qué tienen en común los posts del Top 5? ¿Formato, tema, longitud, hora de publicación, tipo de llamado a la acción? ¿Qué falló en el Bottom 5 y por qué? Sé específico.

3. RECOMENDACIONES DE TEMAS PARA EL PRÓXIMO MES (mínimo 5 ideas)
   Para cada idea indica:
   - Tema / ángulo del mensaje
   - Formato recomendado (video, carrusel, imagen estática, texto)
   - Por qué este tema tiene potencial basado en los datos

4. PLAN DE PUBLICACIONES LISTAS PARA USAR (3 posts completos)
   Para cada post incluye:
   - Título o primer línea gancho
   - Cuerpo del mensaje (máximo 4 líneas)
   - Llamado a la acción (CTA)
   - 5 hashtags relevantes para {red}

5. ACCIÓN PRIORITARIA DE IMPACTO INMEDIATO
   Una sola acción específica que, implementada esta semana, tendría el mayor impacto positivo en las métricas de {marca_nombre} en {red}. Justifica por qué.

Responde en español. Sé directo, específico y orientado a resultados. Evita generalidades — cada recomendación debe poder ejecutarse sin necesidad de más contexto.
"""

    # ── UI ────────────────────────────────────────────────────────────────────
    # Título + 3 botones en una sola fila
    col_ttl, col_btns = st.columns([3, 2.8])
    with col_ttl:
        st.markdown("#### 📝 Script generado para IA")
    with col_btns:
        safe_script = _html.escape(script)
        components.html(f"""
        <style>
          .brow {{ display:flex; gap:7px; margin-top:6px; flex-wrap:nowrap; }}
          .btn  {{ border:none; border-radius:8px; padding:8px 13px; cursor:pointer;
                   font-size:12px; font-weight:600; color:#fff; text-decoration:none;
                   display:inline-block; white-space:nowrap; line-height:1.2; }}
          .copy   {{ background:linear-gradient(135deg,#1e3a5f,#0d2137);
                     border:1px solid #1e90ff; color:#7ab3e0; }}
          .claude {{ background:linear-gradient(135deg,#7c3aed,#5b21b6); }}
          .gemini {{ background:linear-gradient(135deg,#0066ff,#0052cc); }}
        </style>
        <textarea id="cb" style="position:fixed;top:-9999px;left:-9999px;">{safe_script}</textarea>
        <div class="brow">
          <button class="btn copy"
            onclick="var e=document.getElementById('cb');e.select();
                     document.execCommand('copy');
                     this.innerHTML='✅ Copiado!';
                     setTimeout(()=>{{this.innerHTML='📋 Copiar'}},2000);">
            📋 Copiar
          </button>
          <a class="btn claude" href="https://claude.ai" target="_blank">🤖 Claude.ai</a>
          <a class="btn gemini" href="https://gemini.google.com" target="_blank">✨ Gemini</a>
        </div>
        """, height=48)

    st.code(script, language="text")

    # ── Vista rápida ──────────────────────────────────────────────────────────
    if reales:
        st.markdown("---")
        st.markdown("#### 📌 Vista rápida del mes")
        metricas_show = [m for m in metricas_red if reales.get(m['key'])][:4]
        if metricas_show:
            mcols = st.columns(len(metricas_show))
            for col, m in zip(mcols, metricas_show):
                real = float(reales.get(m['key'], 0) or 0)
                meta = float(objetivos.get(m['key'], 0) or 0)
                _, _, pct = kpi_status(real, meta)
                with col:
                    st.metric(
                        f"{m['icon']} {m['label']}",
                        fmt_num(real),
                        f"{fmt_pct(pct)} cumpl." if meta else None,
                    )
