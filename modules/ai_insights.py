# modules/ai_insights.py — Análisis directo con Claude IA

import os
from pathlib import Path
import streamlit as st
import pandas as pd

from config import METRICAS
from database import (
    get_metricas_mensuales, get_kpi_objetivos,
    get_kpi_manual, get_contenido_posts, get_contenido_redes,
    get_publicaciones_count,
)
from utils import fmt_num, fmt_pct, kpi_status, mes_nombre

ROOT = Path(__file__).parent.parent


# ── API helpers ────────────────────────────────────────────────────────────────

def _load_env():
    env_path = ROOT / '.env'
    if env_path.exists():
        for line in env_path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, val = line.partition('=')
                os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))
    try:
        import streamlit as st
        for key, val in st.secrets.items():
            if isinstance(val, str):
                os.environ.setdefault(key, val)
    except Exception:
        pass


def _get_api_key():
    _load_env()
    return os.environ.get('ANTHROPIC_API_KEY', '').strip()


def _get_gemini_key():
    _load_env()
    return os.environ.get('GEMINI_API_KEY', '').strip()


def _ai_provider():
    try:
        return st.session_state.get('ai_provider', 'gemini')
    except Exception:
        return 'gemini'


def _stream_analysis(prompt):
    """Generator: yields text chunks from the active AI provider."""
    if _ai_provider() == 'gemini':
        import json, urllib.request
        key = _get_gemini_key()
        url = (f'https://generativelanguage.googleapis.com/v1beta/models/'
               f'gemini-2.5-flash:streamGenerateContent?alt=sse&key={key}')
        body = json.dumps({
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'maxOutputTokens': 8192},
        }).encode()
        req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
        resp = urllib.request.urlopen(req, timeout=120)
        for line in resp:
            line = line.decode('utf-8').strip()
            if line.startswith('data: '):
                data_str = line[6:]
                if data_str == '[DONE]':
                    break
                try:
                    data = json.loads(data_str)
                    for cand in data.get('candidates', []):
                        for part in cand.get('content', {}).get('parts', []):
                            text = part.get('text', '')
                            if text:
                                yield text
                except Exception:
                    pass
    else:
        import anthropic
        client = anthropic.Anthropic(api_key=_get_api_key())
        with client.messages.stream(
            model='claude-sonnet-4-6',
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                yield text


# ── Data helpers ───────────────────────────────────────────────────────────────

def _build_kpi_text(marca_nombre, red, año, mes, reales, objetivos):
    metricas_red = METRICAS.get(red, [])
    vis_real = float(reales.get('visualizaciones', 0) or 0)
    lines = []
    for m in metricas_red:
        key  = m['key']
        tipo = m['tipo']
        if tipo == 'contenido':
            real = float(get_publicaciones_count(marca_nombre, red, año, mes))
        elif tipo in ('manual', 'manual_50pct'):
            real = get_kpi_manual(marca_nombre, red, key, año, mes)
        else:
            real = float(reales.get(key, 0) or 0)
        if tipo == 'auto_4pct':
            meta = round(float(reales.get('impresiones', 0) or 0) * 0.04)
        elif tipo in ('auto_50pct', 'manual_50pct'):
            meta = round(vis_real * 0.50)
        else:
            meta = float(objetivos.get(key, 0) or 0)
        _, _, pct = kpi_status(real, meta)
        pct_str = fmt_pct(pct) if meta else "sin meta"
        lines.append(
            f"  - {m['label']}: {fmt_num(real)} "
            f"(meta: {fmt_num(meta) if meta else 'N/D'}, cumplimiento: {pct_str})"
        )
    return "\n".join(lines) or "  (Sin datos de KPI para este período)"


def _build_posts_text(posts_df, red):
    if posts_df.empty:
        return "(No hay datos de publicaciones)", "(No hay datos de publicaciones)", ""

    sort_col = 'tasa_interaccion' if 'tasa_interaccion' in posts_df.columns else 'impresiones'
    df_sorted = posts_df.sort_values(sort_col, ascending=False).reset_index(drop=True)

    def _line(row, i):
        titulo = str(row.get('titulo', ''))[:80] or "(sin título)"
        tipo   = str(row.get('tipo', '')) or "—"
        imp    = fmt_num(row.get('impresiones', 0))
        reac   = fmt_num(row.get('reacciones', 0))
        tasa_v = float(row.get('tasa_interaccion', 0) or 0)
        tasa   = fmt_pct(tasa_v * 100 if tasa_v <= 1 else tasa_v)
        return f"  {i}. [{tipo}] \"{titulo}\" — Imp: {imp} | Reac: {reac} | Tasa: {tasa}"

    top5 = "\n".join(_line(r, i + 1) for i, (_, r) in enumerate(df_sorted.head(5).iterrows()))
    bot5_df = df_sorted.tail(5).sort_values(sort_col)
    bot5 = "\n".join(_line(r, i + 1) for i, (_, r) in enumerate(bot5_df.iterrows()))

    tendencias = ""
    if 'tipo' in posts_df.columns:
        tipo_res = (posts_df.groupby('tipo')[[sort_col]]
                    .mean().sort_values(sort_col, ascending=False))
        lineas = [
            f"  - {t}: promedio tasa {fmt_pct(v * 100 if v <= 1 else v)}"
            for t, v in zip(tipo_res.index, tipo_res[sort_col])
        ]
        tendencias = "\n\n📌 RENDIMIENTO POR TIPO DE CONTENIDO:\n" + "\n".join(lineas)

    return top5, bot5, tendencias


def _build_prompt(marca_nombre, red, año, mes, kpi_texto, top5, bot5, tendencias):
    return f"""Actúa como un especialista senior en redes sociales y estrategia de contenido digital con más de 10 años de experiencia en marcas B2B/B2G del sector tecnología y seguridad pública en México. Tu objetivo es analizar los datos que te presento, identificar patrones, diagnosticar la salud de la cuenta y proponer acciones concretas y ejecutables.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 DATOS DE RENDIMIENTO — {marca_nombre} | {red} | {mes_nombre(mes)} {año}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 KPIs DEL MES:
{kpi_texto}

🏆 TOP 5 PUBLICACIONES (mayor engagement):
{top5}

📉 BOTTOM 5 PUBLICACIONES (menor engagement):
{bot5}{tendencias}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Con base en los datos anteriores, entrega el siguiente análisis:

1. DIAGNÓSTICO DE SALUD (califica: Excelente / Bueno / Regular / Crítico)
   Evalúa el estado general de la cuenta. Señala qué métricas están por encima o debajo del benchmark típico para {red}. ¿Hay tendencias de crecimiento o declive?

2. ANÁLISIS DE CONTENIDO GANADOR VS PERDEDOR
   ¿Qué tienen en común los posts del Top 5? ¿Formato, tema, tipo de llamado a la acción? ¿Qué falló en el Bottom 5 y por qué? Sé específico.

3. RECOMENDACIONES DE TEMAS PARA EL PRÓXIMO MES (mínimo 5 ideas)
   Para cada idea indica:
   - Tema / ángulo del mensaje
   - Formato recomendado (carrusel, imagen estática, video, texto)
   - Por qué este tema tiene potencial basado en los datos

4. PLAN DE PUBLICACIONES LISTAS PARA USAR (3 posts completos)
   Para cada post incluye:
   - Primera línea gancho
   - Cuerpo del mensaje (máximo 4 líneas)
   - Llamado a la acción (CTA)
   - 5 hashtags relevantes para {red}

5. ACCIÓN PRIORITARIA DE IMPACTO INMEDIATO
   Una sola acción específica que, implementada esta semana, tendría el mayor impacto positivo en las métricas de {marca_nombre} en {red}. Justifica por qué.

Responde en español. Sé directo, específico y orientado a resultados. Evita generalidades — cada recomendación debe poder ejecutarse sin más contexto."""


# ── Vista principal ────────────────────────────────────────────────────────────

def show_insights():
    marca        = st.session_state.get('marca_activa', 'k1')
    marca_nombre = 'Kabat One' if marca == 'k1' else 'SYM'
    red  = st.session_state.get('f_red', 'LinkedIn')
    año  = st.session_state.get('f_año', 2026)
    mes  = st.session_state.get('f_mes', 4)

    st.markdown(
        f"<h2 style='color:#1e90ff;font-size:1.5rem;font-weight:700;margin-bottom:2px;'>"
        f"🤖 Insights con IA — {marca_nombre}</h2>"
        f"<p style='color:#5b8db8;font-size:.85rem;margin-top:0;'>"
        f"{red} · {mes_nombre(mes)} {año} — Cambia los filtros en el panel superior.</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # ── Recopilar datos ────────────────────────────────────────────────────────
    reales    = get_metricas_mensuales(marca_nombre, red, año, mes)
    objetivos = get_kpi_objetivos(marca_nombre, red, año, mes)

    posts_df = pd.DataFrame()
    if red in get_contenido_redes(marca_nombre):
        posts_df = get_contenido_posts(marca_nombre, red, año, mes)

    kpi_texto           = _build_kpi_text(marca_nombre, red, año, mes, reales, objetivos)
    top5, bot5, trends  = _build_posts_text(posts_df, red)
    prompt              = _build_prompt(marca_nombre, red, año, mes, kpi_texto, top5, bot5, trends)

    analysis_key = f"ai_analysis_{marca}_{red}_{año}_{mes}"

    # ── Vista rápida ───────────────────────────────────────────────────────────
    metricas_red = METRICAS.get(red, [])
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

    st.markdown("---")

    # ── Controles de análisis ──────────────────────────────────────────────────
    provider = _ai_provider()
    api_key  = _get_gemini_key() if provider == 'gemini' else _get_api_key()
    api_ok   = bool(api_key)
    _prov_lbl = "Gemini" if provider == 'gemini' else "Claude"

    col_btn, col_clear = st.columns([3, 1])
    with col_btn:
        analyze = st.button(
            f"🤖  Analizar con {_prov_lbl}",
            type="primary",
            use_container_width=True,
            disabled=not api_ok,
            key="btn_analizar_claude",
        )
    with col_clear:
        if analysis_key in st.session_state:
            if st.button("🗑️  Limpiar", use_container_width=True, key="btn_limpiar_insights"):
                st.session_state.pop(analysis_key, None)
                st.rerun()

    if not api_ok:
        _needed = 'GEMINI_API_KEY' if provider == 'gemini' else 'ANTHROPIC_API_KEY'
        st.warning(f"Configura `{_needed}` en el archivo `.env` para habilitar el análisis con IA.")
        return

    # ── Llamada a IA con streaming ─────────────────────────────────────────────
    if analyze:
        st.session_state.pop(analysis_key, None)

        thinking_ph = st.empty()
        thinking_ph.info(f"⏳ {_prov_lbl} está analizando los datos… (15-40 segundos)")
        full_text = ""

        try:
            for chunk in _stream_analysis(prompt):
                full_text += chunk
                thinking_ph.info(f"✍️ Generando análisis… {len(full_text)} caracteres")

            thinking_ph.empty()
            st.session_state[analysis_key] = full_text
            st.rerun()

        except Exception as e:
            thinking_ph.empty()
            st.error(f"Error al conectar con {_prov_lbl}: {e}")
            return

    # ── Mostrar análisis guardado ──────────────────────────────────────────────
    elif analysis_key in st.session_state:
        st.markdown(st.session_state[analysis_key])

    # ── Acciones post-análisis ─────────────────────────────────────────────────
    if analysis_key in st.session_state:
        st.markdown("---")
        col_dl, col_prompt = st.columns([2, 3])
        with col_dl:
            nombre = f"Insights_{marca_nombre.replace(' ','_')}_{red}_{mes_nombre(mes)}{año}.txt"
            st.download_button(
                "📥  Descargar análisis (.txt)",
                data=st.session_state[analysis_key].encode('utf-8'),
                file_name=nombre,
                mime="text/plain",
                use_container_width=True,
            )
        with col_prompt:
            with st.expander(f"Ver prompt enviado a {_prov_lbl}"):
                st.code(prompt, language="text")
