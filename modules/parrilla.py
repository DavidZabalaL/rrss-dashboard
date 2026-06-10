# modules/parrilla.py — Parrilla de Contenido generada con IA

import os
import json
import calendar as cal_mod
from datetime import date
from pathlib import Path
import io
import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent.parent

_DIA_MAP = {
    'lunes': 0, 'martes': 1, 'miércoles': 2, 'miercoles': 2,
    'jueves': 3, 'viernes': 4, 'sábado': 5, 'sabado': 5, 'domingo': 6,
}
_DIA_LABEL = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

MESES_ES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre',
}

OBJETIVOS_PRESET = [
    "Posicionamiento y liderazgo en el sector seguridad pública",
    "Generación de interés y leads en nuevos territorios",
    "Educación técnica: mostrar capacidades de la plataforma",
    "Construcción de confianza y prueba social",
    "Presencia y cobertura de evento o temporada relevante",
    "Lanzamiento o anuncio de nuevo producto / módulo",
    "Personalizado…",
]

_ESTADOS = ['Borrador', 'En diseño', 'Aprobado', 'Publicado']

_ESTADO_COLORS = {
    'Borrador':  {
        'bg':     '#1c1f2e',
        'border': '#6b7280',
        'text':   '#d1d5db',
        'badge':  '#4b5563',
        'solid':  '#6b7280',   # for filled indicators
    },
    'En diseño': {
        'bg':     '#2d1f02',
        'border': '#f59e0b',
        'text':   '#fde68a',
        'badge':  '#b45309',
        'solid':  '#f59e0b',
    },
    'Aprobado':  {
        'bg':     '#0a1e4a',
        'border': '#60a5fa',
        'text':   '#bfdbfe',
        'badge':  '#2563eb',
        'solid':  '#3b82f6',
    },
    'Publicado': {
        'bg':     '#052e16',
        'border': '#22c55e',
        'text':   '#bbf7d0',
        'badge':  '#16a34a',
        'solid':  '#22c55e',
    },
}

_ESTADO_EMOJI = {
    'Borrador':  '⚪',
    'En diseño': '🟡',
    'Aprobado':  '🔵',
    'Publicado': '🟢',
}

# Display labels used in the data_editor selectbox (emoji prefix for visual color cue)
_ESTADOS_DISPLAY   = [f"{_ESTADO_EMOJI[e]} {e}" for e in _ESTADOS]
_DISPLAY_TO_ESTADO = {f"{_ESTADO_EMOJI[e]} {e}": e for e in _ESTADOS}

# Allow color lookups with either clean name or display name
for _e in list(_ESTADOS):
    _ESTADO_COLORS[f"{_ESTADO_EMOJI[_e]} {_e}"] = _ESTADO_COLORS[_e]


def _to_display(estado):
    emoji = _ESTADO_EMOJI.get(estado, '')
    return f"{emoji} {estado}" if emoji else estado


def _from_display(display):
    return _DISPLAY_TO_ESTADO.get(display, display)


# ── Env / Brand ────────────────────────────────────────────────────────────────

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


def _load_brand(brand_id):
    p = ROOT / 'marca' / brand_id / 'brand.json'
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}


def _get_api_key():
    _load_env()
    return os.environ.get('ANTHROPIC_API_KEY', '').strip()


def _get_gemini_key():
    _load_env()
    return os.environ.get('GEMINI_API_KEY', '').strip()


def _call_gemini_raw(prompt):
    """Calls Gemini generateContent and returns the raw text response."""
    import urllib.request
    key = _get_gemini_key()
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}'
    body = json.dumps({
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {'maxOutputTokens': 8192},
    }).encode()
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req, timeout=120)
    data = json.loads(resp.read())
    return data['candidates'][0]['content']['parts'][0]['text']


def _stream_gemini(prompt):
    """Generator: yields text chunks from Gemini streaming API."""
    import urllib.request
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


def _ai_provider():
    try:
        return st.session_state.get('ai_provider', 'gemini')
    except Exception:
        return 'gemini'


# ── Dates ──────────────────────────────────────────────────────────────────────

def _prev_month(año, mes):
    return (año - 1, 12) if mes == 1 else (año, mes - 1)


def _pub_dates_in_month(año, mes, dias_semana_list):
    target_wd = set()
    for d in dias_semana_list:
        wd = _DIA_MAP.get(d.lower().strip())
        if wd is not None:
            target_wd.add(wd)
    num_days = cal_mod.monthrange(año, mes)[1]
    return [date(año, mes, day) for day in range(1, num_days + 1)
            if date(año, mes, day).weekday() in target_wd]


# ── Special Dates Research ─────────────────────────────────────────────────────

def _research_special_dates(año, mes, brand_label):
    prompt = f"""Eres un estratega de contenido B2G especializado en tecnología de seguridad pública en México. Tu trabajo es identificar fechas de alto valor real para la comunicación de {brand_label}.

CONTEXTO DE LA MARCA: empresa de tecnología para seguridad pública que vende a gobiernos. Productos: C4/C5, videovigilancia con IA, reconocimiento facial, LPR, centros de mando. Clientes: secretarías de seguridad estatales/municipales, policías, protección civil, gobierno federal.

═══ ANÁLISIS DE {MESES_ES[mes].upper()} {año} ═══

Hay DOS tipos de fechas válidas para esta marca. Evalúa ambos:

──────────────────────────────────────────────
EJE A: TÉCNICO-INSTITUCIONAL
Fechas directamente del sector seguridad pública:
• Días oficiales de cuerpos de seguridad (Día del Policía, Guardia Nacional, Bomberos, Protección Civil)
• Fechas institucionales de SSP, CNSP, SESNSP, C4, C5
• Días relacionados con seguridad ciudadana, prevención del delito, ciudades seguras
• Congresos o expos DOCUMENTADOS del sector (solo si ocurren en {MESES_ES[mes]})

Criterio de aprobación EJE A: ¿Un director de C4/C5 lo pondría en la agenda de su institución? Si sí → incluir.

──────────────────────────────────────────────
EJE B: SOCIAL-EMPÁTICO
Fechas que conectan la marca con el impacto humano de la seguridad pública:
• Días relacionados con víctimas de violencia, feminicidio, desaparición forzada, violencia familiar
• Días de derechos humanos en contextos de seguridad (no derechos humanos genérico)
• Días contra la violencia en general — donde la marca puede hablar de su rol en la PREVENCIÓN y RESPUESTA
• Días de memoria o conmemoración de caídos en servicio (policías, bomberos, rescatistas)

Criterio de aprobación EJE B: ¿La marca puede hablar de este tema con genuina empatía Y mostrar cómo su tecnología contribuye a reducir ese problema en concreto, sin forzar la conexión? Si el contenido sonaría natural y humano → incluir.

──────────────────────────────────────────────
DESCARTE AUTOMÁTICO (aplica a ambos ejes):

✗ ABSURDO TECNOLÓGICO: fechas de otros sectores donde la seguridad pública NO es el tema principal.
  Ejemplos concretos de lo que NO incluir:
  - Día del Océano — aunque alguien argumente que "las cámaras detectan derrames"
  - Día del Medio Ambiente, Día de la Tierra, Día del Agua, Día del Árbol
  - Día de la Salud Mental, Día del Médico, Día de la Educación
  PRUEBA: ¿La seguridad pública, el orden público o la protección ciudadana es el TEMA CENTRAL de esta fecha? Si no → descarta. Si sí → puede incluirse.

✗ FESTIVIDADES GENÉRICAS: Día del Padre, Día de las Madres, Halloween, Navidad, Día del Maestro, Día del Niño — a menos que haya un ángulo explícito de seguridad pública (ej: "Regreso a Clases Seguro" podría aplica si hay campaña de seguridad escolar documentada).

✗ TECNOLOGÍA GENÉRICA: Día del Internet, Día del Programador, Día de la IA sin contexto de seguridad pública gubernamental.

✗ SALUD, EDUCACIÓN, MEDIO AMBIENTE: salvo que el vínculo con seguridad pública sea el tema PRINCIPAL de la fecha, no un ángulo derivado.

✗ CONEXIÓN DE MÁS DE 1 PASO: si para llegar a "seguridad pública" necesitas más de una inferencia, descarta.

──────────────────────────────────────────────
RESULTADO:
• Solo incluye fechas que pasaron el filtro con confianza real
• Máximo 5 en total (EJE A + EJE B combinados). Mínimo 0.
• En "conexion": escribe el ángulo de contenido en máximo 12 palabras — cómo la marca hablaría de este día de forma natural y honesta.
• En "eje": indica "tecnico" o "empatico"

Responde ÚNICAMENTE con JSON válido, sin markdown ni texto previo:
[
  {{
    "fecha": "{año}-{mes:02d}-DD",
    "nombre": "Nombre oficial exacto de la fecha o evento",
    "conexion": "Angulo de contenido en max 12 palabras",
    "tipo": "nacional",
    "relevancia": "alta",
    "eje": "tecnico"
  }}
]

Tipos: "nacional" | "internacional" | "sector"
Relevancia: "alta" (conexión directa y obvia) | "media" (conexión genuina pero requiere buen copy)
Eje: "tecnico" | "empatico"
"""
    provider = _ai_provider()
    try:
        if provider == 'gemini':
            raw_text = _call_gemini_raw(prompt)
        else:
            import anthropic
            client = anthropic.Anthropic(api_key=_get_api_key())
            with client.messages.stream(
                model='claude-opus-4-8',
                max_tokens=8000,
                thinking={"type": "adaptive"},
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                msg = stream.get_final_message()
            raw_text = ""
            for block in msg.content:
                if hasattr(block, 'text') and block.text:
                    raw_text += block.text
    except Exception as e:
        raise RuntimeError(f"Error al conectar con la IA ({provider}): {e}") from e

    raw_text = raw_text.strip()
    start, end = raw_text.find('['), raw_text.rfind(']') + 1
    if start == -1 or end <= 0:
        raise ValueError(f"La IA no devolvió JSON válido. Respuesta:\n{raw_text[:500]}")
    try:
        return json.loads(raw_text[start:end])
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON inválido: {e}\nFragmento: {raw_text[start:start+300]}") from e


# ── Calendar Rendering ─────────────────────────────────────────────────────────

def _render_calendar(año, mes, pub_dates, special_dates):
    pub_set     = {d.strftime('%Y-%m-%d') for d in pub_dates}
    special_set = {sd['fecha'] for sd in special_dates}
    day_names   = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

    cells = ''
    for d in day_names:
        cells += (
            f'<div style="color:#5b8db8;font-size:.68rem;font-weight:700;'
            f'text-align:center;padding:3px 0;">{d}</div>'
        )

    for week in cal_mod.monthcalendar(año, mes):
        for day in week:
            if day == 0:
                cells += '<div></div>'
                continue
            d_str  = f"{año}-{mes:02d}-{day:02d}"
            is_pub = d_str in pub_set
            is_sp  = d_str in special_set
            if is_pub and is_sp:
                bg, color, border = 'linear-gradient(135deg,#1e3a8a 50%,#78350f 50%)', '#fff', '2px solid #f59e0b'
            elif is_pub:
                bg, color, border = '#1e3a5f', '#60a5fa', '1px solid #3b82f6'
            elif is_sp:
                bg, color, border = '#78350f', '#fbbf24', '1px solid #f59e0b'
            else:
                bg, color, border = 'transparent', '#64748b', '1px solid transparent'
            weight = '700' if (is_pub or is_sp) else '400'
            cells += (
                f'<div style="background:{bg};color:{color};border:{border};'
                f'border-radius:5px;padding:5px 2px;font-size:.75rem;font-weight:{weight};'
                f'text-align:center;">{day}</div>'
            )

    return f"""
<div style="background:#0d1b2e;border:1px solid #1e3a5f;border-radius:10px;padding:14px 16px;">
  <div style="color:#60a5fa;font-size:.82rem;font-weight:700;text-align:center;margin-bottom:10px;">
    📅 {MESES_ES[mes]} {año}
  </div>
  <div style="display:grid;grid-template-columns:repeat(7,1fr);gap:3px;">{cells}</div>
  <div style="display:flex;gap:14px;margin-top:10px;font-size:.68rem;color:#8892a4;flex-wrap:wrap;">
    <span><span style="display:inline-block;width:9px;height:9px;background:#1e3a5f;
      border:1px solid #3b82f6;border-radius:2px;margin-right:3px;"></span>Publicación</span>
    <span><span style="display:inline-block;width:9px;height:9px;background:#78350f;
      border:1px solid #f59e0b;border-radius:2px;margin-right:3px;"></span>Fecha especial</span>
  </div>
</div>"""


def _render_status_calendar(año, mes, df):
    """Month calendar — highlights days with publications using status color."""
    pub_days = {}
    for _, row in df.iterrows():
        fecha = str(row.get('Fecha', row.get('fecha', ''))).strip()
        if len(fecha) >= 10:
            key    = fecha[:10]
            estado = _from_display(str(row.get('Estado', row.get('estado', 'Borrador'))))
            if estado not in _ESTADOS:
                estado = 'Borrador'
            if key not in pub_days:
                pub_days[key] = estado  # first post's estado drives the color

    day_names = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    header = ''.join(
        f'<div style="color:#5b8db8;font-size:.7rem;font-weight:700;'
        f'text-align:center;padding:4px 0;">{d}</div>'
        for d in day_names
    )

    cells = ''
    for week in cal_mod.monthcalendar(año, mes):
        for day in week:
            if day == 0:
                cells += '<div></div>'
                continue
            d_str  = f"{año}-{mes:02d}-{day:02d}"
            estado = pub_days.get(d_str)
            if estado:
                c = _ESTADO_COLORS[estado]
                cells += (
                    f'<div style="background:{c["bg"]};border:1.5px solid {c["solid"]};'
                    f'border-radius:5px;padding:3px 2px;text-align:center;">'
                    f'<span style="font-size:.72rem;font-weight:700;color:{c["text"]};">{day}</span>'
                    f'</div>'
                )
            else:
                cells += (
                    f'<div style="border:1px solid #1e2d45;border-radius:5px;'
                    f'padding:3px 2px;text-align:center;">'
                    f'<span style="font-size:.72rem;color:#3d4d60;">{day}</span>'
                    f'</div>'
                )

    legend = ''.join(
        f'<span style="display:inline-flex;align-items:center;gap:5px;font-size:.72rem;color:#8892a4;">'
        f'<span style="width:11px;height:11px;border-radius:50%;background:{_ESTADO_COLORS[e]["solid"]};'
        f'display:inline-block;"></span>{_ESTADO_EMOJI[e]} {e}</span>'
        for e in _ESTADOS
    )

    return f"""
<div style="background:#0d1b2e;border:1px solid #1e3a5f;border-radius:12px;padding:18px 14px;">
  <div style="color:#60a5fa;font-size:.9rem;font-weight:700;text-align:center;margin-bottom:14px;">
    {MESES_ES[mes]} {año}
  </div>
  <div style="display:grid;grid-template-columns:repeat(7,1fr);gap:3px;">
    {header}{cells}
  </div>
  <div style="display:flex;gap:14px;margin-top:14px;flex-wrap:wrap;justify-content:center;">
    {legend}
  </div>
</div>"""


# ── Insights Context ───────────────────────────────────────────────────────────

def _get_ai_insights_from_session(marca_key, prev_año, prev_mes):
    found = {}
    for red in ['LinkedIn', 'Facebook', 'Instagram']:
        key = f"ai_analysis_{marca_key}_{red}_{prev_año}_{prev_mes}"
        if key in st.session_state and st.session_state[key]:
            found[red] = st.session_state[key]
    return found


def _get_raw_insights_context(marca_nombre, prev_año, prev_mes):
    try:
        from database import _conn, get_metricas_mensuales, get_kpi_objetivos, get_publicaciones_count, get_kpi_manual
        from config import METRICAS
        from utils import fmt_num, fmt_pct, kpi_status, mes_nombre

        redes, lines = ['LinkedIn', 'Facebook', 'Instagram'], []
        for red in redes:
            reales = get_metricas_mensuales(marca_nombre, red, prev_año, prev_mes)
            if not reales:
                continue
            objetivos    = get_kpi_objetivos(marca_nombre, red, prev_año, prev_mes)
            metricas_red = METRICAS.get(red, [])
            kpi_lines    = []
            for m in metricas_red:
                tipo = m['tipo']
                if tipo == 'contenido':
                    val = float(get_publicaciones_count(marca_nombre, red, prev_año, prev_mes))
                elif tipo in ('manual', 'manual_50pct'):
                    val = float(get_kpi_manual(marca_nombre, red, m['key'], prev_año, prev_mes) or 0)
                else:
                    val = float(reales.get(m['key'], 0) or 0)
                if val:
                    meta = float(objetivos.get(m['key'], 0) or 0)
                    _, _, pct = kpi_status(val, meta)
                    kpi_lines.append(f"    · {m['label']}: {fmt_num(val)}"
                                     + (f" ({fmt_pct(pct)} cumpl.)" if meta else ""))
            if kpi_lines:
                lines.append(f"  {red}:\n" + "\n".join(kpi_lines))

        with _conn() as con:
            df_fmt = pd.read_sql_query(
                """SELECT tipo, AVG(tasa_interaccion) AS avg_tasa,
                          AVG(reacciones) AS avg_reac, COUNT(*) AS total
                   FROM contenido_posts
                   WHERE marca=? AND strftime('%Y-%m',fecha)=?
                   GROUP BY tipo ORDER BY avg_reac DESC LIMIT 5""",
                con, params=[marca_nombre, f"{prev_año}-{prev_mes:02d}"],
            )

        if not lines and df_fmt.empty:
            return None

        ctx = f"KPIs de {mes_nombre(prev_mes)} {prev_año}:\n" + "\n".join(lines)
        if not df_fmt.empty:
            ctx += "\n\nFormatos con mejor engagement:\n"
            for _, r in df_fmt.iterrows():
                tasa = float(r.get('avg_tasa', 0) or 0)
                ctx += (f"  · {r['tipo']}: {fmt_num(r['avg_reac'])} reac. promedio, "
                        f"tasa {fmt_pct(tasa*100 if tasa<=1 else tasa)} ({int(r['total'])} posts)\n")
        return ctx
    except Exception:
        return None


# ── Prompt Builders ────────────────────────────────────────────────────────────

_PERSONA = """Eres un Community Manager y Creador de Contenido Senior especializado en marcas B2G del sector tecnología y seguridad pública en México, con más de 10 años de experiencia gestionando redes sociales para empresas que venden a gobiernos, secretarías de seguridad y tomadores de decisión del sector público.

Tu expertise incluye:
- Storytelling estratégico para audiencias ejecutivas y gubernamentales
- Hooks que detienen el scroll de gobernadores, secretarios y directores de seguridad
- Estructura narrativa que convierte: gancho → problema → solución → prueba social → CTA
- Copywriting diferenciado por red: LinkedIn (formal, autoridad), Facebook/Instagram (conversacional)
- Conocimiento profundo de C4/C5, videovigilancia, IA aplicada, reconocimiento facial, LPR
- Criterios editoriales para priorizar pilares según rendimiento histórico"""


def _build_brand_section(brand):
    rrss     = brand.get('rrss', {})
    pilares  = rrss.get('pilares', [])
    formatos = rrss.get('formatos', [])
    htags    = rrss.get('hashtags', {})
    cta_list = rrss.get('cta_opciones', [])
    tone     = brand.get('tone', {})

    all_tags   = [t for tags in htags.values() for t in tags]
    marca_tags = htags.get('marca', [])
    pilares_txt = '\n'.join(f"  • {p['label']}: {p.get('descripcion','')}" for p in pilares)

    return f"""
=== BRIEF: {brand.get('label','')} ===
Tagline: "{brand.get('tagline','')}"
Audiencia: {brand.get('audience','')}
Tono: {tone.get('style','')}
Evitar: {', '.join(tone.get('avoid',[]))}
Mensajes clave:
{chr(10).join(f"  • {m}" for m in brand.get('key_messages',[]))}

PILARES:
{pilares_txt}

FORMATOS: {', '.join(formatos)}
HASHTAGS (siempre incluir de marca): marca={' '.join(marca_tags)} | pool={' '.join(all_tags[:16])}
CTAs:
{chr(10).join(f"  • {c}" for c in cta_list)}

REGLA DE ESPEJO:
  • LinkedIn: formal, autoridad, 2-3 párrafos con datos o casos concretos.
  • Facebook/Instagram: COPY IDÉNTICO entre sí, tono conversacional, 1-2 párrafos, emojis moderados."""


def _build_main_prompt(brand, año, mes, objetivo, pub_dates,
                       special_dates_selected, ai_insights, raw_ctx):
    prev_año, prev_mes = _prev_month(año, mes)

    dates_base = '\n'.join(
        f"  {d.strftime('%Y-%m-%d')} ({_DIA_LABEL[d.weekday()]}) — publicación regular"
        for d in pub_dates
    )
    dates_extra = ''
    if special_dates_selected:
        dates_extra = '\n\nFECHAS ESPECIALES (publicaciones EXTRA además de las regulares):\n'
        dates_extra += '\n'.join(
            f"  {sd['fecha']} — {sd['nombre']}: {sd.get('conexion','')}"
            for sd in special_dates_selected
        )

    if ai_insights:
        ctx = (f"\n\n=== ANÁLISIS IA DE {MESES_ES[prev_mes].upper()} {prev_año} ===\n"
               "Usa este análisis como base estratégica para las decisiones de contenido.\n")
        for red, texto in ai_insights.items():
            ctx += f"\n── {red} ──\n{texto[:1400]}{'…' if len(texto)>1400 else ''}\n"
    elif raw_ctx:
        ctx = f"\n\n=== DATOS HISTÓRICOS ({MESES_ES[prev_mes]} {prev_año}) ===\n{raw_ctx}"
    else:
        ctx = ""

    num_base  = len(pub_dates)
    num_extra = len(special_dates_selected)
    num_total = num_base + num_extra

    return f"""{_PERSONA}
{_build_brand_section(brand)}
{ctx}
=== PARRILLA: {MESES_ES[mes].upper()} {año} ===
Objetivo mensual: {objetivo}

DÍAS DE PUBLICACIÓN ({num_base} regulares + {num_extra} especiales = {num_total} piezas total):
{dates_base}{dates_extra}

INSTRUCCIONES:
1. Genera UNA pieza por cada fecha listada arriba (regulares + especiales).
2. Las fechas especiales son publicaciones EXTRA para aprovechar la efeméride — no reemplazan las regulares.
3. Si tienes análisis del mes anterior, prioriza pilares y formatos con mejor rendimiento.
4. Cada post necesita un HOOK potente en la primera línea que detenga el scroll.
5. Arte sugerida: descripción concreta y accionable para el diseñador.
6. Distribuye pilares equilibradamente; si hay datos de rendimiento, pondera según resultados.
7. Selecciona 5-7 hashtags del pool + siempre al menos uno de marca.
8. Alterna formatos entre publicaciones.
9. Para fechas especiales, conecta la efeméride con el mensaje de marca de forma natural.

RESPONDE ÚNICAMENTE con JSON válido — sin markdown, sin texto previo:
[
  {{
    "fecha": "YYYY-MM-DD",
    "dia_semana": "Lunes",
    "tipo_dia": "regular",
    "pilar": "Posicionamiento",
    "formato": "Imagen estática / Infografía",
    "tema": "Título conciso (máx 60 chars)",
    "copy_linkedin": "Copy formal completo para LinkedIn",
    "copy_facebook": "Copy conversacional completo para Facebook e Instagram",
    "arte_sugerencia": "Descripción detallada y accionable para el diseñador",
    "hashtags": "#Tag1 #Tag2 #Tag3 #Tag4 #Tag5",
    "cta": "CTA seleccionada",
    "estado": "Borrador"
  }}
]

tipo_dia puede ser "regular" o "especial".
Genera exactamente {num_total} objetos ordenados por fecha.
"""


def _build_adjustment_prompt(brand, parrilla_json, historial, nuevo_pedido):
    historial_txt = ''
    for i, h in enumerate(historial, 1):
        historial_txt += f"\n[Ajuste #{i}]\nUsuario: {h['pedido']}\nCambios realizados: {h['cambios']}\n"

    return f"""{_PERSONA}
{_build_brand_section(brand)}

=== PARRILLA ACTUAL ===
{json.dumps(parrilla_json, ensure_ascii=False, indent=2)}
{historial_txt}
=== NUEVO PEDIDO DE AJUSTE ===
{nuevo_pedido}

Aplica los cambios solicitados a la parrilla. Modifica SOLO lo necesario — mantén el resto igual.
Respeta siempre el brief de marca, la regla de espejo Facebook/Instagram y la estructura de pilares.
Conserva el campo "estado" de cada post tal como está.

Responde con DOS bloques separados por el separador "---CAMBIOS---":
1. Primero: una descripción breve (2-3 líneas) de qué cambiaste y por qué.
2. Después del separador: el JSON completo de la parrilla ajustada (mismo formato que antes).

Ejemplo:
Modifiqué los posts del 7 y 14 de julio para enfocarlos en Educación Técnica ya que mencionas que Posicionamiento ya está cubierto. Ajusté también los hashtags correspondientes.
---CAMBIOS---
[...JSON completo...]
"""


# ── Image Prompt Builder ───────────────────────────────────────────────────────

def _build_image_prompt_request(row, brand, red_formato):
    tema   = str(row.get('Tema', ''))
    pilar  = str(row.get('Pilar', ''))
    arte   = str(row.get('Arte Sugerida', ''))
    copy   = str(row.get('Copy LinkedIn', ''))[:300]
    fmt    = str(row.get('Formato', ''))
    fecha  = str(row.get('Fecha', ''))
    tipo   = str(row.get('Tipo', 'regular'))
    label  = brand.get('label', '')
    tone   = brand.get('tone', {}).get('style', 'profesional y moderno')
    avoid  = ', '.join(brand.get('tone', {}).get('avoid', []))

    if 'LinkedIn' in red_formato:
        aspect = '1200×628 px (horizontal, landscape)'
    elif 'Instagram' in red_formato or 'Facebook' in red_formato:
        aspect = '1080×1080 px (cuadrado)'
    else:
        aspect = '1200×628 px (LinkedIn) y 1080×1080 px (Instagram/Facebook)'

    return f"""Eres un director de arte especializado en contenido B2G para sector tecnología y seguridad pública en México.

PUBLICACIÓN:
- Marca: {label}
- Fecha: {fecha} · Tipo: {tipo}
- Pilar de contenido: {pilar}
- Formato: {fmt}
- Tema: {tema}
- Sugerencia de arte original: {arte}
- Copy de referencia: {copy}…
- Tono de marca: {tone}
- Evitar: {avoid}
- Formato de imagen destino: {aspect}

TAREA:
Genera dos prompts de imagen de nivel profesional para que un diseñador o el equipo de contenido pueda producir la imagen en IA generativa.

REGLAS:
- Sin texto ni logos en la imagen (eso lo agrega el diseñador en post-producción)
- Evitar imágenes de conflicto, violencia o armas
- Preferir tecnología, profesionalismo, modernidad, entornos urbanos de México/LatAm
- Los prompts deben ser en INGLÉS (mejor resultado en ambas herramientas)
- Estilo coherente con sector seguridad pública y tecnología

Responde SOLO con JSON válido, sin texto antes ni después:
{{
  "descripcion_corta": "(15 palabras máximo describiendo la imagen)",
  "dalle3": {{
    "prompt": "(150-250 palabras en inglés, muy detallado: sujeto, composición, iluminación, paleta, estilo, ambiente, acabado técnico)",
    "notas": "(1 frase de consejo para usar en ChatGPT)"
  }},
  "gemini": {{
    "prompt": "(100-180 palabras en inglés, optimizado para Gemini Imagen: descriptivo y directo)",
    "notas": "(1 frase de consejo para usar en Gemini)"
  }}
}}"""


# ── Claude Calls ───────────────────────────────────────────────────────────────

def _call_claude_json(prompt):
    if _ai_provider() == 'gemini':
        return _call_gemini_raw(prompt)
    import anthropic
    client = anthropic.Anthropic(api_key=_get_api_key())
    with client.messages.stream(
        model='claude-sonnet-4-6',
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        msg = stream.get_final_message()
    for block in msg.content:
        if hasattr(block, 'text') and block.text:
            return block.text
    return ''


def _parse_json(text):
    text  = text.strip()
    start = text.find('[')
    end   = text.rfind(']') + 1
    if start == -1 or end == 0:
        raise ValueError(f"No se encontró JSON.\nRespuesta:\n{text[:500]}")
    return json.loads(text[start:end])


def _parse_json_obj(text):
    """Parse a JSON object {...} from raw text (strips markdown fences)."""
    text = text.strip()
    # Strip markdown code fences if present
    if text.startswith('```'):
        text = text.split('```', 2)[1]
        if text.startswith('json'):
            text = text[4:]
        text = text.strip()
    start = text.find('{')
    end   = text.rfind('}') + 1
    if start == -1 or end == 0:
        raise ValueError(f"No se encontró JSON.\nRespuesta:\n{text[:500]}")
    return json.loads(text[start:end])


def _call_adjustment(prompt):
    """Returns (descripcion_cambios, parrilla_json_list)."""
    provider    = _ai_provider()
    placeholder = st.empty()
    full_text   = ""
    lbl         = "Gemini" if provider == 'gemini' else "Claude"
    thinking_ph = st.info(f"⏳ {lbl} está ajustando la parrilla…")

    if provider == 'gemini':
        for chunk in _stream_gemini(prompt):
            if not full_text:
                thinking_ph.empty()
            full_text += chunk
            placeholder.markdown(full_text + "▌")
    else:
        import anthropic
        client = anthropic.Anthropic(api_key=_get_api_key())
        with client.messages.stream(
            model='claude-sonnet-4-6',
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for chunk in stream.text_stream:
                if not full_text:
                    thinking_ph.empty()
                full_text += chunk
                placeholder.markdown(full_text + "▌")

    placeholder.empty()

    if '---CAMBIOS---' in full_text:
        descripcion, _, json_part = full_text.partition('---CAMBIOS---')
    else:
        descripcion = ""
        json_part   = full_text

    posts = _parse_json(json_part)
    return descripcion.strip(), posts


# ── Excel Export ───────────────────────────────────────────────────────────────

def _to_excel(df):
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    buf       = io.BytesIO()
    export_df = df.copy()
    # Drop Estado column from Excel — it's a workflow field
    export_df = export_df.drop(columns=['Estado'], errors='ignore')

    if 'Copy Facebook / Instagram' in export_df.columns:
        export_df.insert(
            export_df.columns.get_loc('Copy Facebook / Instagram') + 1,
            'Copy Instagram',
            export_df['Copy Facebook / Instagram'],
        )

    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='Parrilla')
        ws = writer.sheets['Parrilla']

        hfill = PatternFill('solid', fgColor='1E3A5F')
        hfont = Font(bold=True, color='FFFFFF', size=10)
        wrap  = Alignment(wrap_text=True, vertical='top')
        wide  = {'Copy LinkedIn', 'Copy Facebook / Instagram', 'Copy Instagram', 'Arte Sugerida'}
        med   = {'Hashtags', 'Tema', 'CTA', 'Pilar', 'Formato'}

        for ci, col in enumerate(ws.iter_cols(1, ws.max_column), 1):
            col[0].fill      = hfill
            col[0].font      = hfont
            col[0].alignment = Alignment(horizontal='center', vertical='center')
            cname = str(col[0].value or '')
            ws.column_dimensions[get_column_letter(ci)].width = (
                55 if cname in wide else 30 if cname in med else 16
            )
            for cell in col[1:]:
                cell.alignment = wrap
        for ri in range(2, ws.max_row + 1):
            ws.row_dimensions[ri].height = 90

    buf.seek(0)
    return buf.read()


# ── DataFrame helpers ──────────────────────────────────────────────────────────

_COL_MAP = {
    'fecha':           'Fecha',
    'dia_semana':      'Día',
    'tipo_dia':        'Tipo',
    'pilar':           'Pilar',
    'formato':         'Formato',
    'tema':            'Tema',
    'copy_linkedin':   'Copy LinkedIn',
    'copy_facebook':   'Copy Facebook / Instagram',
    'arte_sugerencia': 'Arte Sugerida',
    'hashtags':        'Hashtags',
    'cta':             'CTA',
    'estado':          'Estado',
}


def _posts_to_df(posts):
    raw = pd.DataFrame(posts)
    df  = raw.rename(columns={k: v for k, v in _COL_MAP.items() if k in raw.columns})
    for col in _COL_MAP.values():
        if col not in df.columns:
            df[col] = _to_display('Borrador') if col == 'Estado' else ''
    if 'Estado' in df.columns:
        df['Estado'] = df['Estado'].fillna('Borrador').apply(
            lambda x: _to_display(_from_display(x) if x in _DISPLAY_TO_ESTADO
                                   else (x if x in _ESTADOS else 'Borrador'))
        )
    return df[[v for v in _COL_MAP.values() if v in df.columns]]


def _df_to_posts(df):
    inv  = {v: k for k, v in _COL_MAP.items()}
    out  = df.copy()
    # Strip emoji prefix from Estado before saving to DB
    if 'Estado' in out.columns:
        out['Estado'] = out['Estado'].apply(_from_display)
    return out.rename(columns={v: k for v, k in inv.items()}).to_dict('records')


def _posts_from_db(db_posts):
    posts = [{
        'fecha':           p.get('fecha', ''),
        'dia_semana':      p.get('dia_semana', ''),
        'tipo_dia':        p.get('tipo_dia', 'regular'),
        'pilar':           p.get('pilar', ''),
        'formato':         p.get('formato', ''),
        'tema':            p.get('tema', ''),
        'copy_linkedin':   p.get('copy_linkedin', ''),
        'copy_facebook':   p.get('copy_facebook', ''),
        'arte_sugerencia': p.get('arte_sugerencia', ''),
        'hashtags':        p.get('hashtags', ''),
        'cta':             p.get('cta', ''),
        'estado':          p.get('estado', 'Borrador'),
    } for p in db_posts]
    return _posts_to_df(posts)


def _save_df_to_db(df, marca, año, mes):
    from database import save_parrilla_posts
    save_parrilla_posts(marca, año, mes, _df_to_posts(df))


# ── Monday.com Integration ─────────────────────────────────────────────────────

def _monday_api_key():
    _load_env()
    return os.environ.get('MONDAY_API_KEY', '').strip()


def _monday_board_id():
    _load_env()
    return os.environ.get('MONDAY_BOARD_ID', '').strip()


def _monday_configured():
    return bool(_monday_api_key() and _monday_board_id())


def _monday_request(api_key, query, variables=None):
    import requests as rq
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    resp = rq.post(
        "https://api.monday.com/v2",
        json=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": api_key,
            "API-Version": "2024-01",
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if 'errors' in data:
        raise ValueError(f"Monday.com API error: {data['errors'][0].get('message','?')}")
    return data.get('data', {})


def _monday_get_board_info(api_key, board_id):
    """Returns (board_name, columns_list, groups_list). Raises on error."""
    query = f"""query {{
      boards(ids: [{board_id}]) {{
        name
        columns {{ id title type }}
        groups {{ id title }}
      }}
    }}"""
    data   = _monday_request(api_key, query)
    boards = data.get('boards', [])
    if not boards:
        raise ValueError(f"No se encontró el tablero con ID {board_id}.")
    board  = boards[0]
    return board.get('name', ''), board.get('columns', []), board.get('groups', [])


def _monday_find_group(groups, marca):
    """Returns group_id matching the brand name, or None."""
    marca_lower = marca.lower()
    for g in groups:
        title = g.get('title', '').lower()
        if 'kabat' in marca_lower and 'kabat' in title:
            return g['id']
        if 'sym' in marca_lower and 'sym' in title:
            return g['id']
    return None


def _monday_match_columns(columns):
    """Returns dict mapping our field names to {id, type} for each detected column."""
    mapping = {}
    for col in columns:
        title = col['title'].lower()
        ctype = col['type']
        cid   = col['id']
        info  = {'id': cid, 'type': ctype}
        if ctype == 'date' or any(k in title for k in ('fecha', 'date', 'publicación', 'publicacion')):
            mapping.setdefault('fecha', info)
        elif ctype == 'color' or any(k in title for k in ('estado', 'status', 'etapa')):
            mapping.setdefault('estado', info)
        elif 'linkedin' in title:
            mapping.setdefault('copy_linkedin', info)
        elif any(k in title for k in ('facebook', 'fb / instagram', 'instagram')):
            mapping.setdefault('copy_facebook', info)
        elif 'arte' in title:
            mapping.setdefault('arte_sugerencia', info)
        elif 'hashtag' in title:
            mapping.setdefault('hashtags', info)
        elif title == 'cta':
            mapping.setdefault('cta', info)
        elif 'pilar' in title:
            mapping.setdefault('pilar', info)
        elif 'formato' in title:
            mapping.setdefault('formato', info)
    return mapping


def _monday_col_value(field, value, col_type):
    """Formats a value for a Monday.com column based on its type."""
    if not value:
        return None
    if col_type == 'date':
        return {"date": str(value)[:10], "time": "00:00:00"}
    if col_type == 'long_text':
        return {"text": str(value)}
    if col_type == 'color':
        return {"label": str(value)}
    # text and everything else
    return str(value)


def _monday_create_item(api_key, board_id, item_name, col_vals_json, group_id=None):
    if group_id:
        mutation = """mutation ($boardId: ID!, $groupId: String!, $name: String!, $cols: JSON!) {
          create_item(board_id: $boardId, group_id: $groupId, item_name: $name, column_values: $cols) {
            id name
          }
        }"""
        variables = {
            "boardId":  str(board_id),
            "groupId":  str(group_id),
            "name":     item_name,
            "cols":     col_vals_json,
        }
    else:
        mutation = """mutation ($boardId: ID!, $name: String!, $cols: JSON!) {
          create_item(board_id: $boardId, item_name: $name, column_values: $cols) {
            id name
          }
        }"""
        variables = {
            "boardId": str(board_id),
            "name":    item_name,
            "cols":    col_vals_json,
        }
    data = _monday_request(api_key, mutation, variables)
    return data.get('create_item', {}).get('id')


def _monday_add_update(api_key, item_id, body):
    mutation = """mutation ($itemId: ID!, $body: String!) {
      create_update(item_id: $itemId, body: $body) { id }
    }"""
    _monday_request(api_key, mutation, {"itemId": str(item_id), "body": body})


def _monday_push_estados(df, marca, año, mes):
    """After a DB save, push Estado changes to Monday for items that already exist there.
    Returns (updated_count, skipped_count, error_msg_or_None)."""
    if not _monday_configured():
        return 0, 0, None

    from database import get_parrilla_posts
    api_key  = _monday_api_key()
    board_id = _monday_board_id()

    # Get monday_item_ids from DB
    db_posts = get_parrilla_posts(marca, año, mes)
    id_map = {
        (p['fecha'], p.get('tipo_dia', 'regular')): p.get('monday_item_id')
        for p in db_posts
        if p.get('monday_item_id')
    }
    if not id_map:
        return 0, 0, None  # Nothing synced to Monday yet

    # Find the Estado column id on the board
    try:
        _, columns, _ = _monday_get_board_info(api_key, board_id)
    except Exception as e:
        return 0, 0, str(e)

    # Find Estado column: prefer exact title match on text columns first,
    # fall back to any column whose title contains 'estado'
    estado_col = None
    for col in columns:
        if col['title'].lower() == 'estado' and col['type'] == 'text':
            estado_col = {'id': col['id'], 'type': col['type']}
            break
    if not estado_col:
        for col in columns:
            if col['title'].lower() == 'estado':
                estado_col = {'id': col['id'], 'type': col['type']}
                break
    if not estado_col:
        col_map = _monday_match_columns(columns)
        estado_col = col_map.get('estado')
    if not estado_col:
        return 0, 0, (
            "No se encontró columna 'Estado' en Monday. "
            f"Columnas disponibles: {', '.join(c['title'] for c in columns)}"
        )

    col_id   = estado_col['id']
    col_type = estado_col['type']

    if col_type in ('color', 'status'):
        return 0, 0, (
            "La columna 'Estado' en Monday es de tipo Status (con colores nativos). "
            "Solo acepta etiquetas pre-configuradas, por eso 'En diseño' y 'Aprobado' no se sincronizan. "
            "Solución: en Monday, borra esa columna y crea una nueva columna de tipo Texto con el nombre 'Estado'."
        )

    mutation = """mutation ($boardId: ID!, $itemId: ID!, $colId: String!, $val: JSON!) {
      change_column_value(board_id: $boardId, item_id: $itemId, column_id: $colId, value: $val) {
        id
      }
    }"""

    posts      = _df_to_posts(df)
    updated    = 0
    skipped    = 0
    stale_ids  = []

    for p in posts:
        key     = (p.get('fecha', ''), p.get('tipo_dia', 'regular'))
        item_id = id_map.get(key)
        if not item_id:
            skipped += 1
            continue
        estado = p.get('estado', 'Borrador')
        # Format value for the column type
        if col_type == 'long_text':
            val_json = json.dumps({"text": estado})
        elif col_type in ('color', 'status'):
            val_json = json.dumps({"label": estado})
        elif col_type == 'date':
            skipped += 1
            continue
        else:
            # text column: plain JSON-encoded string
            val_json = json.dumps(estado)

        try:
            _monday_request(api_key, mutation, {
                "boardId": str(board_id),
                "itemId":  str(item_id),
                "colId":   col_id,
                "val":     val_json,
            })
            updated += 1
        except Exception as e:
            err_msg = str(e).lower()
            if 'inactive' in err_msg or 'not found' in err_msg or 'invalid' in err_msg:
                # Item was deleted from Monday — clear the stale ID from DB
                stale_ids.append((None, marca, año, mes,
                                  p.get('fecha', ''), p.get('tipo_dia', 'regular')))
            skipped += 1

    if stale_ids:
        from database import update_monday_item_ids
        update_monday_item_ids(stale_ids)

    return updated, skipped, (
        f"{len(stale_ids)} ítem(s) eliminados de Monday — usa '🔄 Re-sincronizar tablero' para crearlos de nuevo."
        if stale_ids else None
    )


def _monday_format_update(p):
    return (
        f"**📅 {p.get('fecha','')} ({p.get('dia_semana','')}) — {p.get('tipo_dia','').upper()}**\n"
        f"**Pilar:** {p.get('pilar','')} | **Formato:** {p.get('formato','')}\n\n"
        f"**🔵 LINKEDIN:**\n{p.get('copy_linkedin','')}\n\n"
        f"**🟣 FACEBOOK / INSTAGRAM:**\n{p.get('copy_facebook','')}\n\n"
        f"**🎨 Arte sugerida:** {p.get('arte_sugerencia','')}\n\n"
        f"**#️⃣ Hashtags:** {p.get('hashtags','')}\n\n"
        f"**📣 CTA:** {p.get('cta','')}"
    )


def _monday_sync_parrilla(df, marca, año, mes, api_key, board_id):
    """Creates Monday.com items for each post in df. Returns result dict."""
    from database import get_parrilla_posts, update_monday_item_ids

    # Load existing Monday IDs from DB
    db_posts = get_parrilla_posts(marca, año, mes)
    existing_ids = {
        (p['fecha'], p.get('tipo_dia', 'regular')): p.get('monday_item_id')
        for p in db_posts
    }

    board_name, columns, groups = _monday_get_board_info(api_key, board_id)
    col_map  = _monday_match_columns(columns)
    group_id = _monday_find_group(groups, marca)

    # Field-to-post-key mapping
    _FIELD_MAP = {
        'fecha':           'fecha',
        'estado':          'estado',
        'pilar':           'pilar',
        'formato':         'formato',
        'copy_linkedin':   'copy_linkedin',
        'copy_facebook':   'copy_facebook',
        'arte_sugerencia': 'arte_sugerencia',
        'hashtags':        'hashtags',
        'cta':             'cta',
    }

    posts      = _df_to_posts(df)
    results    = []
    new_ids    = []
    skipped    = 0

    for p in posts:
        fecha    = p.get('fecha', '')
        tipo_dia = p.get('tipo_dia', 'regular')
        key      = (fecha, tipo_dia)

        if existing_ids.get(key):
            skipped += 1
            results.append({'fecha': fecha, 'tipo_dia': tipo_dia,
                            'item_id': existing_ids[key], 'new': False})
            continue

        tema      = p.get('tema', '')
        date_part = fecha[-5:].replace('-', '/') if fecha else ''
        item_name = f"{date_part} — {tema[:50]}"

        # Build column values from all matched columns
        col_vals = {}
        for field, col_info in col_map.items():
            post_key = _FIELD_MAP.get(field)
            if not post_key:
                continue
            raw_val  = p.get(post_key, '')
            if not raw_val:
                continue
            formatted = _monday_col_value(field, raw_val, col_info['type'])
            if formatted is not None:
                col_vals[col_info['id']] = formatted

        col_vals_json = json.dumps(col_vals, ensure_ascii=False) if col_vals else "{}"
        item_id = _monday_create_item(api_key, board_id, item_name, col_vals_json, group_id)

        if item_id:
            _monday_add_update(api_key, item_id, _monday_format_update(p))
            new_ids.append((str(item_id), marca, año, mes, fecha, tipo_dia))
            results.append({'fecha': fecha, 'tipo_dia': tipo_dia,
                            'item_id': str(item_id), 'new': True})

    if new_ids:
        update_monday_item_ids(new_ids)

    return {
        'board_name': board_name,
        'created':    len(new_ids),
        'skipped':    skipped,
        'results':    results,
    }


# ── Main View ──────────────────────────────────────────────────────────────────

def show_parrilla():
    st.title("📅 Parrilla de Contenido")
    st.caption(
        "2 días/semana por red · LinkedIn (formal) · Facebook = Instagram (espejo) · "
        "Fechas especiales como publicaciones extra."
    )

    marca_key = st.session_state.get('marca_activa', 'k1')
    marca_id  = 'kabat-one' if marca_key == 'k1' else 'sym-servicios'
    brand     = _load_brand(marca_id)
    if not brand:
        st.error("No se encontró el brief de la marca.")
        return

    # Si la parrilla en sesión es de otra marca, limpiarla para cargar la correcta
    _meta_marca = st.session_state.get('parrilla_meta', {}).get('marca', '')
    if _meta_marca and _meta_marca != brand.get('label', ''):
        for _k in ('parrilla_df', 'parrilla_meta', 'parrilla_historial'):
            st.session_state.pop(_k, None)

    rrss     = brand.get('rrss', {})
    dias_pub = rrss.get('frecuencia', {}).get('dias_publicacion', [])
    pilares  = rrss.get('pilares', [])
    formatos = rrss.get('formatos', [])

    # ── Selector de mes/año ────────────────────────────────────────────────────
    st.markdown("### Configuración")
    hoy = date.today()

    col1, col2 = st.columns([1, 1])
    with col1:
        años = list(range(hoy.year + 2, 2023, -1))
        año  = st.selectbox("Año", años,
                            index=años.index(hoy.year) if hoy.year in años else 0,
                            key="parrilla_año")
    with col2:
        mes = st.selectbox("Mes", list(range(1, 13)),
                           format_func=lambda m: MESES_ES[m],
                           index=hoy.month - 1, key="parrilla_mes")

    pub_dates          = _pub_dates_in_month(año, mes, dias_pub)
    prev_año, prev_mes = _prev_month(año, mes)

    if not pub_dates:
        st.warning(f"No hay días de publicación en {MESES_ES[mes]} {año}. "
                   f"Días configurados: {', '.join(dias_pub)}")
        return

    # ── Fechas especiales — investigación automática ───────────────────────────
    st.markdown("---")
    st.markdown("### 📆 Fechas Especiales del Mes")

    fd_key     = f"fechas_esp_{marca_key}_{año}_{mes}"
    fd_sel_key = f"fechas_sel_{marca_key}_{año}_{mes}"

    fechas_ya_buscadas = fd_key in st.session_state

    col_inv, col_ref, col_info = st.columns([1.8, 1, 3])
    with col_inv:
        lbl_buscar = "✅ Fechas buscadas" if fechas_ya_buscadas else "🔍  Buscar fechas del mes"
        if st.button(lbl_buscar, use_container_width=True,
                     key="btn_investigar_fechas",
                     disabled=fechas_ya_buscadas,
                     type="secondary" if fechas_ya_buscadas else "primary"):
            with st.spinner(f"Analizando {MESES_ES[mes]} {año}…"):
                try:
                    fechas = _research_special_dates(año, mes, brand.get('label', ''))
                    st.session_state[fd_key]     = fechas
                    st.session_state[fd_sel_key] = [f['fecha'] for f in fechas]
                except Exception as e:
                    st.error(f"Error al buscar fechas: {e}")
                    st.stop()
            st.rerun()
    with col_ref:
        if fechas_ya_buscadas:
            if st.button("🔄 Regenerar", use_container_width=True,
                         key="btn_regenerar_fechas",
                         help="Vuelve a buscar fechas (puede dar resultados distintos)"):
                st.session_state.pop(fd_key, None)
                st.session_state.pop(fd_sel_key, None)
                st.rerun()
    with col_info:
        if fechas_ya_buscadas:
            n = len(st.session_state.get(fd_key, []))
            st.caption(
                f"{'✅' if n > 0 else 'ℹ️'} {'Se encontraron' if n > 0 else 'No se encontraron'} "
                f"**{n} fechas** relevantes para el sector en {MESES_ES[mes]}. "
                f"Solo se incluyen fechas con vínculo directo a seguridad pública."
            )
        else:
            st.caption(
                "Análisis específico del sector: solo fechas con conexión directa a "
                "C4/C5, videovigilancia o tecnología de mando. Calidad sobre cantidad."
            )

    special_dates   = st.session_state.get(fd_key, [])
    selected_fechas = st.session_state.get(fd_sel_key, [])

    if special_dates:
        col_cal, col_list = st.columns([1, 1.4])
        with col_cal:
            st.markdown(
                _render_calendar(año, mes, pub_dates, special_dates),
                unsafe_allow_html=True,
            )
        with col_list:
            altas  = [sd for sd in special_dates if sd.get('relevancia','alta') == 'alta']
            medias = [sd for sd in special_dates if sd.get('relevancia','') == 'media']
            new_sel = list(selected_fechas)

            _eje_icon = {"tecnico": "🔒", "empatico": "🤝"}

            if altas:
                st.markdown("**🎯 Alta relevancia**")
                for sd in altas:
                    d_obj   = date.fromisoformat(sd['fecha'])
                    dia_lbl = f"{d_obj.day} {MESES_ES[mes][:3]} ({_DIA_LABEL[d_obj.weekday()]})"
                    tipo_b  = {"nacional": "🇲🇽", "internacional": "🌍", "sector": "🔒"}.get(sd.get('tipo',''), "📌")
                    eje_b   = _eje_icon.get(sd.get('eje', 'tecnico'), '🔒')
                    checked = sd['fecha'] in selected_fechas
                    val = st.checkbox(
                        f"{tipo_b}{eje_b} **{dia_lbl}** — {sd['nombre']}",
                        value=checked,
                        help=f"💡 {sd.get('conexion', '')}",
                        key=f"fd_chk_{sd['fecha']}",
                    )
                    if val and sd['fecha'] not in new_sel:
                        new_sel.append(sd['fecha'])
                    elif not val and sd['fecha'] in new_sel:
                        new_sel.remove(sd['fecha'])

            if medias:
                st.markdown("**📌 Relevancia media**")
                for sd in medias:
                    d_obj   = date.fromisoformat(sd['fecha'])
                    dia_lbl = f"{d_obj.day} {MESES_ES[mes][:3]} ({_DIA_LABEL[d_obj.weekday()]})"
                    tipo_b  = {"nacional": "🇲🇽", "internacional": "🌍", "sector": "🔒"}.get(sd.get('tipo',''), "📌")
                    eje_b   = _eje_icon.get(sd.get('eje', 'tecnico'), '🔒')
                    checked = sd['fecha'] in selected_fechas
                    val = st.checkbox(
                        f"{tipo_b}{eje_b} {dia_lbl} — {sd['nombre']}",
                        value=checked,
                        help=f"💡 {sd.get('conexion', '')}",
                        key=f"fd_chk_{sd['fecha']}",
                    )
                    if val and sd['fecha'] not in new_sel:
                        new_sel.append(sd['fecha'])
                    elif not val and sd['fecha'] in new_sel:
                        new_sel.remove(sd['fecha'])

            if not altas and not medias:
                st.info(
                    f"No se encontraron fechas con conexión directa al sector "
                    f"en {MESES_ES[mes]}. Puedes usar **🔄 Regenerar** o continuar "
                    f"solo con los días regulares de publicación."
                )

            st.session_state[fd_sel_key] = new_sel
            selected_fechas = new_sel
    else:
        st.markdown(
            _render_calendar(año, mes, pub_dates, []),
            unsafe_allow_html=True,
        )
        if not fechas_ya_buscadas:
            st.caption(
                "Pulsa **Buscar fechas del mes** para que Claude identifique "
                "efemérides específicas del sector seguridad pública."
            )

    special_dates_selected = [sd for sd in special_dates if sd['fecha'] in selected_fechas]

    # ── Objetivo mensual ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🎯 Objetivo del Mes")

    obj_preset = st.selectbox("Selecciona el objetivo principal", OBJETIVOS_PRESET,
                               key="parrilla_obj_preset")
    objetivo = ""
    if obj_preset == "Personalizado…":
        objetivo = st.text_input("Describe el objetivo mensual",
                                 placeholder="Ej: Posicionar en el sector público del bajío…",
                                 key="parrilla_obj_custom")
    else:
        objetivo = obj_preset
        st.caption(f"Objetivo seleccionado: **{objetivo}**")

    # ── Resumen del mes ────────────────────────────────────────────────────────
    st.markdown("---")
    ai_insights  = _get_ai_insights_from_session(marca_key, prev_año, prev_mes)
    total_piezas = len(pub_dates) + len(special_dates_selected)

    if ai_insights:
        st.success(
            f"**{brand.get('label','')}** · **{MESES_ES[mes]} {año}**  →  "
            f"{len(pub_dates)} publicaciones regulares + {len(special_dates_selected)} especiales "
            f"= **{total_piezas} piezas**  \n"
            f"✅ Insights de IA de **{MESES_ES[prev_mes]} {prev_año}** disponibles "
            f"({', '.join(ai_insights.keys())}) — se usarán como base estratégica."
        )
    else:
        st.info(
            f"**{brand.get('label','')}** · **{MESES_ES[mes]} {año}**  →  "
            f"{len(pub_dates)} publicaciones regulares + {len(special_dates_selected)} especiales "
            f"= **{total_piezas} piezas**  \n"
            f"ℹ️ Sin análisis de Insights guardado para {MESES_ES[prev_mes]} {prev_año}. "
            "Para mejor resultado, genera primero el análisis en **🤖 Insights para IA**."
        )

    # ── Botones principales ────────────────────────────────────────────────────
    col_gen, col_clear = st.columns([3, 1])
    with col_gen:
        generate = st.button(
            "✨  Generar Parrilla con IA",
            type="primary", use_container_width=True,
            disabled=not objetivo.strip(),
            key="btn_generar_parrilla",
        )
    with col_clear:
        if st.button("🗑️  Limpiar", use_container_width=True, key="btn_limpiar_parrilla"):
            for k in ('parrilla_df', 'parrilla_meta', 'parrilla_historial'):
                st.session_state.pop(k, None)
            st.rerun()

    if not objetivo.strip():
        st.caption("Selecciona o escribe un objetivo para habilitar la generación.")

    # ── Generación ─────────────────────────────────────────────────────────────
    if generate and objetivo.strip():
        with st.status("Generando parrilla con IA…", expanded=True) as status:
            raw_ctx = None
            if ai_insights:
                st.write(f"Cargando análisis de Insights de {MESES_ES[prev_mes]} {prev_año}…")
            else:
                st.write(f"Consultando datos de {MESES_ES[prev_mes]} {prev_año}…")
                raw_ctx = _get_raw_insights_context(brand.get('label', ''), prev_año, prev_mes)

            n_esp = len(special_dates_selected)
            st.write(f"Construyendo {len(pub_dates)} piezas regulares"
                     + (f" + {n_esp} especiales" if n_esp else "") + "…")

            prompt = _build_main_prompt(
                brand, año, mes, objetivo, pub_dates,
                special_dates_selected, ai_insights, raw_ctx,
            )

            _lbl = "Gemini 2.5 Flash" if _ai_provider() == 'gemini' else "Claude Sonnet"
            st.write(f"Llamando a {_lbl} (20-60 segundos)…")
            try:
                raw   = _call_claude_json(prompt)
                posts = _parse_json(raw)
                df    = _posts_to_df(posts)

                st.session_state['parrilla_df']        = df
                st.session_state['parrilla_historial'] = []
                st.session_state['parrilla_meta'] = {
                    'marca':        brand.get('label', ''),
                    'año':          año,
                    'mes':          mes,
                    'objetivo':     objetivo,
                    'con_insights': bool(ai_insights),
                    'insights_mes': f"{MESES_ES[prev_mes]} {prev_año}",
                    'brand':        brand,
                }
                # Guardar en DB automáticamente
                try:
                    _save_df_to_db(df, brand.get('label', ''), año, mes)
                    st.write("✅ Guardado en base de datos.")
                except Exception:
                    pass

                status.update(label=f"Parrilla lista: {len(df)} piezas", state="complete")
                st.rerun()
            except Exception as e:
                status.update(label="Error al generar", state="error")
                st.error(f"Error: {e}")

    # ── Intentar cargar desde DB si no hay en sesión ───────────────────────────
    if 'parrilla_df' not in st.session_state:
        marca_nombre = brand.get('label', '')
        try:
            from database import get_parrilla_posts
            db_posts = get_parrilla_posts(marca_nombre, año, mes)
            if db_posts:
                df_loaded = _posts_from_db(db_posts)
                st.session_state['parrilla_df']        = df_loaded
                st.session_state['parrilla_historial'] = []
                st.session_state['parrilla_meta'] = {
                    'marca': marca_nombre, 'año': año, 'mes': mes,
                    'objetivo': '(guardada en base de datos)',
                    'con_insights': False, 'insights_mes': '', 'brand': brand,
                }
                st.info(f"📂 Parrilla de **{MESES_ES[mes]} {año}** cargada desde la base de datos.")
        except Exception:
            pass

    if 'parrilla_df' not in st.session_state:
        return

    # ── Header de la parrilla ──────────────────────────────────────────────────
    meta      = st.session_state.get('parrilla_meta', {})
    mes_label = MESES_ES.get(meta.get('mes', 1), '')
    historial = st.session_state.get('parrilla_historial', [])

    st.markdown(f"### {meta.get('marca','')} · {mes_label} {meta.get('año','')}")
    badge = (f"✅ Basada en Insights de **{meta.get('insights_mes','')}**"
             if meta.get('con_insights')
             else f"ℹ️ Basada en datos de **{meta.get('insights_mes','')}**"
             if meta.get('insights_mes')
             else "📂 Cargada desde base de datos")
    st.caption(f"Objetivo: {meta.get('objetivo','')}  ·  {badge}")

    # Normalize Estado column to display format (handles legacy clean values from DB/old sessions)
    _df_norm = st.session_state['parrilla_df']
    if 'Estado' in _df_norm.columns:
        _df_norm = _df_norm.copy()
        _df_norm['Estado'] = _df_norm['Estado'].apply(
            lambda x: x if x in _ESTADOS_DISPLAY
                      else _to_display(_from_display(x) if x in _DISPLAY_TO_ESTADO
                                       else (x if x in _ESTADOS else 'Borrador'))
        )
        st.session_state['parrilla_df'] = _df_norm

    df = st.session_state['parrilla_df']

    # ── TABS ───────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Parrilla", "📅 Calendario", "🟦 Monday.com", "🎨 Prompts de Imagen"])

    # ═══ TAB 1: PARRILLA ════════════════════════════════════════════════════════
    with tab1:
        pilar_opts   = [p['label'] for p in pilares] if pilares else None
        formato_opts = formatos if formatos else None
        col_cfg = {
            'Copy LinkedIn':             st.column_config.TextColumn(width='large'),
            'Copy Facebook / Instagram': st.column_config.TextColumn(width='large'),
            'Arte Sugerida':             st.column_config.TextColumn(width='large'),
            'Hashtags':                  st.column_config.TextColumn(width='medium'),
            'CTA':                       st.column_config.TextColumn(width='medium'),
            'Tema':                      st.column_config.TextColumn(width='medium'),
            'Tipo':                      st.column_config.SelectboxColumn(
                                             options=['regular', 'especial'], width='small'),
            'Estado':                    st.column_config.SelectboxColumn(
                                             options=_ESTADOS_DISPLAY, width='small'),
        }
        if pilar_opts:
            col_cfg['Pilar']   = st.column_config.SelectboxColumn(options=pilar_opts,   width='medium')
        if formato_opts:
            col_cfg['Formato'] = st.column_config.SelectboxColumn(options=formato_opts, width='medium')

        edited_df = st.data_editor(
            df, use_container_width=True, num_rows="dynamic",
            column_config=col_cfg, height=550, key="parrilla_editor",
        )
        st.session_state['parrilla_df'] = edited_df

        # Botones de guardar y descargar
        col_save, col_dl, col_info = st.columns([1.5, 1.5, 3])
        with col_save:
            if st.button("💾  Guardar cambios", use_container_width=True, key="btn_guardar_parrilla"):
                try:
                    _save_df_to_db(edited_df, meta.get('marca', ''), año, mes)
                    # Sync estados to Monday if configured
                    updated, skipped, err = _monday_push_estados(
                        edited_df, meta.get('marca', ''), año, mes
                    )
                    if err:
                        st.warning(f"Guardado en DB ✓ — Monday: {err}")
                    elif updated > 0:
                        st.success(
                            f"Guardado ✓ · {updated} estado(s) actualizados en Monday.com"
                            + (f" · {skipped} sin ítem en Monday" if skipped else "")
                        )
                    elif _monday_configured():
                        from database import get_parrilla_posts as _gpp2
                        _has_ids = any(
                            p.get('monday_item_id')
                            for p in _gpp2(meta.get('marca', ''), año, mes)
                        )
                        if _has_ids:
                            st.warning(
                                "Guardado en DB ✓ — Monday no actualizó (0 ítems). "
                                "Revisa el tab 🟦 → 🔍 Diagnóstico de columnas."
                            )
                        else:
                            st.success(
                                "Guardado en DB ✓ — Monday: sincroniza primero en el tab 🟦"
                            )
                    else:
                        st.success("Cambios guardados en la base de datos.")
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
        with col_dl:
            nombre = (f"Parrilla_{meta.get('marca','').replace(' ','_')}_"
                      f"{mes_label}{meta.get('año','')}.xlsx")
            st.download_button(
                "📥  Descargar Excel",
                data=_to_excel(edited_df),
                file_name=nombre,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col_info:
            n = len(edited_df)
            st.caption(
                f"{n} piezas · LinkedIn + Facebook + Instagram · "
                "El Excel incluye columna Instagram separada (espejo de Facebook). "
                "**Cambia el Estado** para dar seguimiento al flujo de trabajo."
            )

        # Semáforo de estados
        estado_counts = {e: 0 for e in _ESTADOS}
        for _, row in edited_df.iterrows():
            e = _from_display(str(row.get('Estado', 'Borrador')))
            if e in estado_counts:
                estado_counts[e] += 1
        total = max(sum(estado_counts.values()), 1)

        cards_html = '<div style="display:flex;gap:10px;margin:12px 0;">'
        for estado in _ESTADOS:
            c   = _ESTADO_COLORS[estado]
            n   = estado_counts[estado]
            pct = int(n / total * 100)
            emoji = _ESTADO_EMOJI[estado]
            cards_html += f"""
            <div style="flex:1;background:{c['bg']};border:1.5px solid {c['solid']};
                        border-radius:10px;padding:14px 12px;text-align:center;">
              <div style="font-size:1.6rem;line-height:1;">{emoji}</div>
              <div style="color:{c['text']};font-weight:700;font-size:1.3rem;
                          margin:4px 0 2px;">{n}</div>
              <div style="color:{c['text']};font-size:.75rem;opacity:.9;">{estado}</div>
              <div style="margin-top:6px;background:#0d1117;border-radius:4px;height:4px;">
                <div style="width:{pct}%;background:{c['solid']};height:4px;
                             border-radius:4px;"></div>
              </div>
            </div>"""
        cards_html += '</div>'
        st.markdown(cards_html, unsafe_allow_html=True)

        # ── Cuadro de ajustes ──────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 💬 Ajustar Parrilla")
        st.caption(
            "Dile a Claude qué quieres cambiar: temas ya cubiertos, eventos próximos, "
            "tono, redistribución de pilares, o cualquier otro ajuste."
        )

        if historial:
            with st.expander(f"Historial de ajustes ({len(historial)})", expanded=False):
                for i, h in enumerate(historial, 1):
                    st.markdown(f"**Ajuste #{i}:** {h['pedido']}")
                    st.markdown(f"*Claude:* {h['cambios']}")
                    st.markdown("---")

        pedido = st.text_area(
            "¿Qué quieres cambiar?",
            placeholder=(
                "Ej: Los temas de posicionamiento ya los tengo cubiertos con 3 publicaciones. "
                "Cámbiame esos posts por educación técnica o casos de uso. "
                "Además, el post del lunes 7 hazlo sobre el lanzamiento del nuevo módulo de LPR."
            ),
            height=110,
            key="parrilla_pedido_ajuste",
        )

        col_ajustar, col_sp = st.columns([2, 3])
        with col_ajustar:
            ajustar = st.button(
                "🔄  Aplicar Ajuste",
                type="primary", use_container_width=True,
                disabled=not pedido.strip(),
                key="btn_aplicar_ajuste",
            )

        if ajustar and pedido.strip():
            current_posts = _df_to_posts(st.session_state['parrilla_df'])
            adj_prompt    = _build_adjustment_prompt(
                meta.get('brand', brand), current_posts, historial, pedido
            )
            try:
                descripcion, new_posts = _call_adjustment(adj_prompt)
                new_df = _posts_to_df(new_posts)
                st.session_state['parrilla_df'] = new_df
                historial.append({'pedido': pedido, 'cambios': descripcion or "Parrilla ajustada."})
                st.session_state['parrilla_historial'] = historial
                try:
                    _save_df_to_db(new_df, meta.get('marca', ''), año, mes)
                except Exception:
                    pass
                if descripcion:
                    st.success(f"**Cambios realizados:** {descripcion}")
                st.rerun()
            except Exception as e:
                st.error(f"Error al ajustar: {e}")

    # ═══ TAB 2: CALENDARIO ══════════════════════════════════════════════════════
    with tab2:
        st.markdown(
            _render_status_calendar(año, mes, st.session_state['parrilla_df']),
            unsafe_allow_html=True,
        )
        st.caption(
            "El color de cada día refleja el estado actual del post. "
            "Cambia el estado en la pestaña **📋 Parrilla** y pulsa **💾 Guardar cambios**."
        )

        # Listado compacto con estado por pieza
        st.markdown("#### Resumen por publicación")
        df_cal = st.session_state['parrilla_df']
        for _, row in df_cal.iterrows():
            fecha   = str(row.get('Fecha', ''))
            dia     = str(row.get('Día', ''))
            tipo    = str(row.get('Tipo', 'regular'))
            tema    = str(row.get('Tema', ''))
            pilar   = str(row.get('Pilar', ''))
            estado  = str(row.get('Estado', 'Borrador'))
            c       = _ESTADO_COLORS.get(estado, _ESTADO_COLORS['Borrador'])

            label_tipo = "⭐ Especial" if tipo == 'especial' else "📅 Regular"
            emoji      = _ESTADO_EMOJI.get(estado, '⚪')
            badge_html = (
                f'<span style="background:{c["badge"]};color:{c["text"]};border:1px solid {c["solid"]};'
                f'border-radius:6px;padding:3px 10px;font-size:.75rem;font-weight:700;'
                f'white-space:nowrap;">'
                f'{emoji} {estado}</span>'
            )
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;'
                f'padding:6px 0;border-bottom:1px solid #1a2442;">'
                f'<span style="color:#5b8db8;font-size:.78rem;min-width:100px;">{fecha}</span>'
                f'<span style="color:#8892a4;font-size:.75rem;min-width:60px;">{dia}</span>'
                f'<span style="color:#60a5fa;font-size:.75rem;min-width:80px;">{label_tipo}</span>'
                f'<span style="color:#dde3ee;font-size:.78rem;flex:1;">{tema}</span>'
                f'<span style="color:#8892a4;font-size:.72rem;min-width:80px;">{pilar}</span>'
                f'{badge_html}</div>',
                unsafe_allow_html=True,
            )

    # ═══ TAB 3: MONDAY.COM ══════════════════════════════════════════════════════
    with tab3:
        st.markdown("#### 🟦 Sincronizar con Monday.com")
        st.caption(
            "Exporta cada publicación de la parrilla como un ítem en tu tablero de Monday.com. "
            "El contenido completo (copies, arte, hashtags) se agrega como nota en cada ítem."
        )

        configured = _monday_configured()

        if not configured:
            st.warning("Monday.com no está configurado. Sigue estos pasos:")
            st.markdown("""
**Paso 1 — Obtén tu API key:**
- Ve a `monday.com → tu avatar → Developers → My Access Tokens`
- Copia el token personal

**Paso 2 — Obtén el ID de tu tablero:**
- Abre el tablero en Monday.com
- La URL tiene el formato: `monday.com/boards/**1234567890**`
- Ese número es el `MONDAY_BOARD_ID`

**Paso 3 — Agrega al archivo `.env`:**
""")
            st.code("MONDAY_API_KEY=eyJhbGciOiJIUzI1...\nMONDAY_BOARD_ID=1234567890", language="bash")
            env_path = ROOT / '.env'
            st.caption(f"Archivo: `{env_path}`")

            with st.expander("Editar .env directamente aquí"):
                if env_path.exists():
                    current_env = env_path.read_text(encoding='utf-8')
                else:
                    current_env = "ANTHROPIC_API_KEY=\n"
                new_monday_key  = st.text_input("MONDAY_API_KEY", type="password",
                                                key="monday_key_input",
                                                placeholder="eyJhbGciOiJIUzI1...")
                new_monday_board = st.text_input("MONDAY_BOARD_ID",
                                                 key="monday_board_input",
                                                 placeholder="1234567890")
                if st.button("Guardar credenciales Monday.com", key="btn_save_monday_creds"):
                    if new_monday_key and new_monday_board:
                        lines = current_env.splitlines()
                        new_lines, added_key, added_board = [], False, False
                        for line in lines:
                            if line.startswith('MONDAY_API_KEY='):
                                new_lines.append(f"MONDAY_API_KEY={new_monday_key}")
                                added_key = True
                            elif line.startswith('MONDAY_BOARD_ID='):
                                new_lines.append(f"MONDAY_BOARD_ID={new_monday_board}")
                                added_board = True
                            else:
                                new_lines.append(line)
                        if not added_key:
                            new_lines.append(f"MONDAY_API_KEY={new_monday_key}")
                        if not added_board:
                            new_lines.append(f"MONDAY_BOARD_ID={new_monday_board}")
                        env_path.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
                        # Reset env cache so next call picks up new values
                        os.environ.pop('MONDAY_API_KEY', None)
                        os.environ.pop('MONDAY_BOARD_ID', None)
                        st.success("Credenciales guardadas. Recarga la página para activar.")
                        st.rerun()
                    else:
                        st.error("Completa ambos campos.")
        else:
            api_key  = _monday_api_key()
            board_id = _monday_board_id()

            # Board info preview
            board_info_key = f"monday_board_info_{board_id}"
            if board_info_key not in st.session_state:
                try:
                    bname, bcols = _monday_get_board_info(api_key, board_id)
                    st.session_state[board_info_key] = {'name': bname, 'cols': bcols}
                except Exception as e:
                    st.session_state[board_info_key] = {'error': str(e)}

            bi = st.session_state.get(board_info_key, {})
            if 'error' in bi:
                st.error(f"Error al conectar con Monday.com: {bi['error']}")
            else:
                bname = bi.get('name', '—')
                bcols = bi.get('cols', [])
                col_map = _monday_match_columns(bcols)
                st.success(f"Conectado a tablero: **{bname}**")

                col_info2, col_map_info = st.columns([1, 1])
                with col_info2:
                    st.metric("Items a crear", len(st.session_state['parrilla_df']))
                with col_map_info:
                    mapped = ', '.join(col_map.keys()) or 'ninguno'
                    st.caption(f"Columnas detectadas: {mapped} · Resto se agrega como nota")

                with st.expander("🔍 Diagnóstico de columnas del tablero", expanded=False):
                    st.markdown("**Todas las columnas en Monday.com:**")
                    for c in bcols:
                        matched_as = next(
                            (k for k, v in col_map.items() if v['id'] == c['id']), None
                        )
                        tag = f" → **mapeada como `{matched_as}`**" if matched_as else ""
                        st.markdown(f"- `{c['id']}` · **{c['title']}** · tipo: `{c['type']}`{tag}")
                    estado_info = col_map.get('estado')
                    if estado_info:
                        st.info(
                            f"Estado se actualizará en columna **'{estado_info['id']}'** "
                            f"(tipo: `{estado_info['type']}`)"
                        )
                    else:
                        st.warning("No se detectó columna Estado — los estados NO se sincronizarán.")

            st.markdown("---")

            # Reset button — always visible so user can re-sync after Monday board changes
            from database import get_parrilla_posts as _gpp, clear_monday_item_ids
            db_posts_mon = _gpp(meta.get('marca', ''), año, mes)
            has_ids = any(p.get('monday_item_id') for p in db_posts_mon)

            col_sync_btn, col_reset = st.columns([3, 1])
            with col_reset:
                if st.button(
                    "🗑️ Limpiar IDs",
                    use_container_width=True,
                    key="btn_monday_reset",
                    disabled=not has_ids,
                    help="Borra los IDs de Monday guardados localmente. "
                         "Úsalo cuando hayas borrado ítems o columnas en Monday "
                         "y quieras volver a sincronizar desde cero."
                ):
                    clear_monday_item_ids(meta.get('marca', ''), año, mes)
                    st.session_state.pop(f"monday_sync_{marca_key}_{año}_{mes}", None)
                    st.success("IDs limpiados. Ahora sincroniza de nuevo.")
                    st.rerun()

            # Sync button
            sync_key = f"monday_sync_{marca_key}_{año}_{mes}"
            with col_sync_btn:
                if st.button("🔄  Sincronizar parrilla con Monday.com",
                             type="primary", use_container_width=True,
                             key="btn_monday_sync"):
                    with st.spinner("Creando ítems en Monday.com…"):
                        try:
                            result = _monday_sync_parrilla(
                                st.session_state['parrilla_df'],
                                meta.get('marca', ''), año, mes, api_key, board_id,
                            )
                            st.session_state[sync_key] = result
                        except Exception as e:
                            st.error(f"Error durante la sincronización: {e}")

            # Show results
            if sync_key in st.session_state:
                res = st.session_state[sync_key]
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("✅ Ítems creados", res.get('created', 0))
                with c2:
                    st.metric("⏭️ Ya sincronizados", res.get('skipped', 0))

                items = res.get('results', [])
                if items:
                    st.markdown("**Ítems en Monday.com:**")
                    for item in items:
                        prefix = "🆕" if item.get('new') else "✅"
                        item_id = item.get('item_id', '')
                        link = f"https://monday.com/boards/{board_id}/pulses/{item_id}"
                        st.markdown(
                            f"{prefix} {item.get('fecha','')} ({item.get('tipo_dia','')}) — "
                            f"[Ver en Monday.com]({link})"
                        )

    # ═══ TAB 4: PROMPTS DE IMAGEN ════════════════════════════════════════════════
    with tab4:
        st.markdown("#### 🎨 Generador de Prompts de Imagen")
        st.caption(
            "Selecciona una publicación y genera prompts profesionales listos para pegar "
            "en **DALL-E 3 (ChatGPT)** y **Gemini Imagen** (Google)."
        )

        _prov_img = _ai_provider()
        _key_img_ok = _get_gemini_key() if _prov_img == 'gemini' else _get_api_key()
        if not _key_img_ok:
            _needed = 'GEMINI_API_KEY' if _prov_img == 'gemini' else 'ANTHROPIC_API_KEY'
            st.warning(f"Configura `{_needed}` en `.env` para usar este módulo.")
        else:
            # Selector de publicación
            opciones = []
            for _, row in df.iterrows():
                fecha = str(row.get('Fecha', ''))
                tema  = str(row.get('Tema', ''))[:50]
                tipo  = str(row.get('Tipo', ''))
                lbl   = f"{fecha} · {tema}" + (" ⭐" if tipo == 'especial' else "")
                opciones.append(lbl)

            if not opciones:
                st.info("No hay publicaciones en la parrilla.")
            else:
                sel_lbl = st.selectbox("Publicación", opciones, key="img_prompt_sel")
                sel_idx = opciones.index(sel_lbl)
                sel_row = df.iloc[sel_idx].to_dict()

                col_red, _ = st.columns([2, 3])
                with col_red:
                    red_img = st.radio(
                        "Formato destino",
                        ["LinkedIn (1200×628)", "Instagram / Facebook (1080×1080)", "Ambos"],
                        horizontal=True,
                        key="img_prompt_red",
                    )

                _img_error_ph = st.empty()

                if st.button("✨  Generar Prompts de Imagen", type="primary",
                             use_container_width=True, key="btn_gen_img_prompt"):
                    cache_key = f"img_prompts_{meta.get('marca','')}_{sel_lbl}_{red_img}"
                    st.session_state.pop(cache_key, None)
                    _img_error_ph.empty()

                    prompt_req = _build_image_prompt_request(sel_row, brand, red_img)
                    _ai_lbl_img = "Gemini" if _ai_provider() == 'gemini' else "Claude"
                    _spin_ph = st.empty()
                    with _spin_ph:
                        with st.spinner(f"{_ai_lbl_img} está creando los prompts… (10-20 seg)"):
                            try:
                                raw = _call_claude_json(prompt_req)
                                result = _parse_json_obj(raw)
                                if not result:
                                    result = {'error': 'No se pudo parsear la respuesta', 'raw': raw}
                                st.session_state[cache_key] = result
                            except Exception as e:
                                err_msg = str(e)
                                if 'credit' in err_msg.lower() or 'balance' in err_msg.lower():
                                    _img_error_ph.error(
                                        "❌ Saldo insuficiente en Anthropic. "
                                        "Cambia a Gemini (gratis) en el sidebar, o agrega créditos en "
                                        "[console.anthropic.com](https://console.anthropic.com)."
                                    )
                                else:
                                    _img_error_ph.error(f"Error al generar: {err_msg}")
                    _spin_ph.empty()

                # Mostrar resultado
                cache_key = f"img_prompts_{meta.get('marca','')}_{sel_lbl}_{red_img}"
                if cache_key in st.session_state:
                    result = st.session_state[cache_key]
                    if 'error' in result:
                        st.error(result['error'])
                        if 'raw' in result:
                            with st.expander("Respuesta cruda"):
                                st.text(result['raw'])
                    else:
                        desc = result.get('descripcion_corta', '')
                        if desc:
                            st.markdown(f"**Imagen:** {desc}")
                        st.markdown("---")

                        col_dalle, col_gemini = st.columns(2)

                        with col_dalle:
                            st.markdown("### 🤖 DALL-E 3 · ChatGPT")
                            dalle = result.get('dalle3', {})
                            prompt_text = dalle.get('prompt', '')
                            st.text_area(
                                "Copia y pega en ChatGPT → DALL-E 3",
                                value=prompt_text,
                                height=260,
                                key="dalle_prompt_area",
                            )
                            notas = dalle.get('notas', '')
                            if notas:
                                st.caption(f"💡 {notas}")

                        with col_gemini:
                            st.markdown("### 🌐 Gemini Imagen · Google")
                            gemini = result.get('gemini', {})
                            prompt_text_g = gemini.get('prompt', '')
                            st.text_area(
                                "Copia y pega en Gemini (gemini.google.com)",
                                value=prompt_text_g,
                                height=260,
                                key="gemini_prompt_area",
                            )
                            notas_g = gemini.get('notas', '')
                            if notas_g:
                                st.caption(f"💡 {notas_g}")

                        # Guía de uso
                        with st.expander("📖 ¿Cómo usar estos prompts?"):
                            st.markdown("""
**ChatGPT / DALL-E 3:**
1. Abre [chatgpt.com](https://chatgpt.com) y crea una nueva conversación
2. Haz clic en el ícono de imagen (🖼️) o escribe el prompt directamente
3. Si quieres variaciones, escribe: *"genera 4 variaciones de este prompt"*

**Gemini Imagen (Google):**
1. Ve a [gemini.google.com](https://gemini.google.com)
2. Pega el prompt en el chat
3. Gemini generará la imagen automáticamente

**Consejo:** Después de generar, pide ajustes con frases como:
- *"Hazla más minimalista"*
- *"Cambia el fondo a azul oscuro"*
- *"Versión sin personas, solo tecnología"*
""")
