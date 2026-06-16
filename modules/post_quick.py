# modules/post_quick.py — Generador de post individual con IA

import os
import json
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).parent.parent

_REDES_OPCIONES = ['LinkedIn', 'Facebook / Instagram', 'Todos (LinkedIn + Facebook/Instagram)']

_CONTEXTO_TIPOS = [
    "Tema / concepto libre",
    "Noticia o novedad del sector",
    "Evento o efeméride",
    "Lanzamiento de producto o módulo",
    "Caso de éxito o testimonio",
    "Contenido educativo / técnico",
]


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


def _load_brand(brand_id):
    p = ROOT / 'marca' / brand_id / 'brand.json'
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}


def _format_section(redes: list) -> str:
    """Instrucciones de formato según las redes solicitadas."""
    li  = 'LinkedIn'  in redes
    fb  = 'Facebook'  in redes

    sections = []
    if li:
        sections.append("## LinkedIn\n\n[copy completo para LinkedIn: hook, cuerpo y emojis si aplica]")
    if fb:
        sections.append("## Facebook / Instagram\n\n[copy completo para Facebook e Instagram: hook, cuerpo y emojis]")
    if not li and not fb:
        sections.append("## Post\n\n[copy completo]")

    sections.append("## Arte Sugerida\n\n[descripción visual en 2-3 líneas: escena, elementos, estilo, colores, composición]")

    lines = '\n\n'.join(sections)
    return (
        f"{lines}\n\n"
        "CTA: [texto del CTA en una sola línea]\n"
        "Hashtags: [todos los hashtags en una sola línea, ej: #Tag1 #Tag2 #Tag3]"
    )


def _parse_post_sections(text: str, redes_str: str) -> dict:
    """Divide el texto en secciones usando los encabezados ## fijos del prompt."""
    import re
    result = {'copy_linkedin': '', 'copy_facebook': '', 'hashtags': '', 'arte_sugerencia': '', 'cta': ''}

    # Split en encabezados ##
    parts = re.split(r'\n##\s+', '\n' + text)
    sections: dict[str, str] = {}
    for part in parts[1:]:
        title_end = part.find('\n')
        title   = part[:title_end].strip().lower() if title_end > 0 else part.strip().lower()
        content = part[title_end:].strip()          if title_end > 0 else ''
        sections[title] = content

    for title, content in sections.items():
        if 'linkedin' in title:
            result['copy_linkedin'] = content
        elif 'facebook' in title or 'instagram' in title or 'post' == title:
            result['copy_facebook'] = content
        elif 'arte' in title:
            result['arte_sugerencia'] = content[:400]

    # CTA y Hashtags como líneas standalone
    cta_m = re.search(r'^CTA:\s*(.+)$',       text, re.M | re.I)
    ht_m  = re.search(r'^Hashtags?:\s*(#.+)$', text, re.M | re.I)
    if cta_m:
        result['cta'] = cta_m.group(1).strip()
    if ht_m:
        result['hashtags'] = ht_m.group(1).strip()
    else:
        tags = list(dict.fromkeys(re.findall(r'#\w+', text)))
        result['hashtags'] = ' '.join(tags[:10])

    # Fallback si no hubo encabezados reconocidos
    if not result['copy_linkedin'] and 'LinkedIn' in redes_str:
        result['copy_linkedin'] = text
    if not result['copy_facebook'] and 'Facebook' in redes_str:
        result['copy_facebook'] = text

    return result


def _build_quick_prompt(brand, tipo_contexto, tema, contexto_extra, redes):
    rrss     = brand.get('rrss', {})
    htags    = rrss.get('hashtags', {})
    cta_list = rrss.get('cta_opciones', [])
    pilares  = rrss.get('pilares', [])
    formatos = rrss.get('formatos', [])
    tone     = brand.get('tone', {})

    all_tags   = [t for tags in htags.values() for t in tags]
    marca_tags = htags.get('marca', [])
    pilares_txt = ' | '.join(p['label'] for p in pilares)

    redes_instrucciones = ""
    if 'LinkedIn' in redes and 'Facebook' in redes:
        redes_instrucciones = """Genera el post para AMBAS redes:
- LinkedIn: tono formal, autoridad, 2-3 párrafos, lenguaje técnico pero accesible
- Facebook/Instagram: tono conversacional, 1-2 párrafos cortos, emojis moderados, COPY IDÉNTICO para ambas"""
    elif 'LinkedIn' in redes:
        redes_instrucciones = "Genera el post SOLO para LinkedIn: tono formal, autoridad, 2-3 párrafos, lenguaje técnico pero accesible."
    else:
        redes_instrucciones = "Genera el post SOLO para Facebook/Instagram: tono conversacional, 1-2 párrafos cortos, emojis moderados."

    extra_section = ""
    if contexto_extra.strip():
        extra_section = f"\nCONTEXTO ADICIONAL / MATERIAL:\n{contexto_extra[:3000]}\n"

    return f"""Eres un Community Manager y Creador de Contenido Senior especializado en marcas B2G del sector tecnología y seguridad pública en México.

=== BRIEF: {brand.get('label','')} ===
Tagline: "{brand.get('tagline','')}"
Audiencia: {brand.get('audience','')}
Tono: {tone.get('style','')}
Evitar: {', '.join(tone.get('avoid',[]))}
Pilares: {pilares_txt}
Formatos disponibles: {', '.join(formatos[:6])}
Hashtags de marca (SIEMPRE incluir): {' '.join(marca_tags)}
Pool de hashtags: {' '.join(all_tags[:16])}
CTAs disponibles: {' | '.join(cta_list[:4])}

=== SOLICITUD DE POST INDIVIDUAL ===
Tipo de contenido: {tipo_contexto}
Tema principal: {tema}
{extra_section}
=== INSTRUCCIONES ===
{redes_instrucciones}

Para CADA red que corresponda, genera:
1. HOOK — primera línea que detiene el scroll (no puede ser genérica)
2. CUERPO — mensaje principal con el valor/dato/historia
3. CTA — llamado a la acción específico
4. HASHTAGS — 5-7 del pool + al menos uno de marca
5. ARTE SUGERIDA — descripción concreta y accionable para el diseñador

IMPORTANTE:
- El hook debe ser específico y provocador, NO genérico
- Si tienes material extra, úsalo para datos concretos o citas
- Mantén el pilar temático más relevante para el tema dado
- El CTA debe ser específico a la audiencia

Responde en español. Sé directo y concreto — nada de copy genérico o corporativo vacío.

FORMATO OBLIGATORIO — usa EXACTAMENTE estos encabezados (son markers de parseo, no los modifiques):

{_format_section(redes)}"""


def _parse_post_sections(text: str, redes_str: str) -> dict:
    """Divide el texto de la IA en secciones LinkedIn/Facebook y extrae metadata."""
    import re
    result = {'copy_linkedin': '', 'copy_facebook': '', 'hashtags': '', 'arte_sugerencia': '', 'cta': ''}

    # Detectar límites de cada sección por encabezado
    li_idx = fb_idx = -1
    for pat in [r'##\s*linkedin', r'###\s*linkedin', r'\*\*linkedin\*\*']:
        m = re.search(pat, text, re.I)
        if m:
            li_idx = m.start(); break
    for pat in [r'##\s*facebook', r'###\s*facebook', r'\*\*facebook\*\*',
                r'##\s*instagram', r'facebook/instagram']:
        m = re.search(pat, text, re.I)
        if m:
            fb_idx = m.start(); break

    if li_idx >= 0 and fb_idx >= 0:
        if li_idx < fb_idx:
            li_text = text[li_idx:fb_idx].strip()
            fb_text = text[fb_idx:].strip()
        else:
            fb_text = text[fb_idx:li_idx].strip()
            li_text = text[li_idx:].strip()
    elif li_idx >= 0:
        li_text, fb_text = text[li_idx:].strip(), ''
    elif fb_idx >= 0:
        fb_text, li_text = text[fb_idx:].strip(), ''
    else:
        if 'Facebook' in redes_str:
            fb_text, li_text = text, ''
        else:
            li_text, fb_text = text, ''

    result['copy_linkedin'] = li_text
    result['copy_facebook'] = fb_text

    # Extraer hashtags
    src = li_text or fb_text or text
    htag_m = re.search(r'\*\*HASHTAGS[^*]*\*+\s*\n?((?:#\w+\s*)+)', src, re.I)
    if htag_m:
        result['hashtags'] = htag_m.group(1).strip()
    else:
        all_tags = list(dict.fromkeys(re.findall(r'#\w+', src)))
        result['hashtags'] = ' '.join(all_tags[:10])

    # Extraer arte sugerida
    arte_m = re.search(r'\*\*ARTE\s+SUGERID[AO][^*]*\*+\s*[\n:]?\s*(.+?)(?=\n\n|\*\*|$)', src, re.I | re.S)
    if arte_m:
        result['arte_sugerencia'] = arte_m.group(1).strip()[:300]

    # Extraer CTA
    cta_m = re.search(r'\*\*CTA[^*]*\*+\s*[\n:]?\s*(.+?)(?=\n\n|\*\*|$)', src, re.I | re.S)
    if cta_m:
        result['cta'] = cta_m.group(1).strip()[:200]

    return result


def _stream_quick_post(prompt):
    if _ai_provider() == 'gemini':
        import json, urllib.request
        key = _get_gemini_key()
        url = (f'https://generativelanguage.googleapis.com/v1beta/models/'
               f'gemini-2.5-flash:streamGenerateContent?alt=sse&key={key}')
        body = json.dumps({
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'maxOutputTokens': 4096},
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


def show_post_quick():
    _role = st.session_state.get('current_user', {}).get('role', 'viewer')
    if _role == 'visita':
        st.warning("No tienes permiso para usar este módulo.")
        return

    st.title("✍️ Generador de Post Individual")
    st.caption(
        "Genera el copy para un post reactivo, una noticia del sector o cualquier contenido puntual. "
        "Produce LinkedIn y Facebook/Instagram con un solo clic."
    )

    marca_key = st.session_state.get('marca_activa', 'k1')
    marca_id  = 'kabat-one' if marca_key == 'k1' else 'sym-servicios'
    brand     = _load_brand(marca_id)
    if not brand:
        st.error("No se encontró el brief de la marca.")
        return

    provider = _ai_provider()
    api_key  = _get_gemini_key() if provider == 'gemini' else _get_api_key()
    if not api_key:
        _needed = 'GEMINI_API_KEY' if provider == 'gemini' else 'ANTHROPIC_API_KEY'
        st.warning(f"Configura `{_needed}` en el archivo `.env` para usar este módulo.")
        return

    st.markdown(f"**Marca activa:** {brand.get('label', '')}  ·  cambia con los botones del sidebar.")
    st.markdown("---")

    # ── Formulario ─────────────────────────────────────────────────────────────
    st.markdown("### 1. ¿Qué tipo de contenido es?")
    tipo_ctx = st.selectbox("Tipo de contenido", _CONTEXTO_TIPOS, key="pq_tipo_ctx")

    st.markdown("### 2. Tema principal")
    tema = st.text_input(
        "Describe el tema en una frase",
        placeholder="Ej: Cómo el reconocimiento facial redujo el tiempo de respuesta en CDMX un 40%",
        key="pq_tema",
    )

    st.markdown("### 3. ¿Para qué redes?")
    red_sel = st.radio(
        "Generar para",
        _REDES_OPCIONES,
        index=2,
        horizontal=True,
        key="pq_redes",
    )
    if red_sel == 'LinkedIn':
        redes = ['LinkedIn']
    elif red_sel == 'Facebook / Instagram':
        redes = ['Facebook']
    else:
        redes = ['LinkedIn', 'Facebook']

    st.markdown("### 4. Contexto adicional (opcional)")
    contexto_extra = st.text_area(
        "Pega aquí noticias, datos, descripción de producto, comunicado, etc.",
        placeholder=(
            "Ej: La Secretaría de Seguridad de [Estado] implementó el sistema en julio 2026, "
            "logrando reducir el tiempo de respuesta ante incidentes de 12 a 4 minutos. "
            "El C4 procesa ahora 6,000 cámaras en tiempo real…"
        ),
        height=130,
        key="pq_contexto",
    )

    st.markdown("---")

    # ── Botón generar ──────────────────────────────────────────────────────────
    can_generate = bool(tema.strip())
    _prov_lbl = "Gemini" if _ai_provider() == 'gemini' else "Claude"
    gen_btn = st.button(
        f"✨  Generar Post con {_prov_lbl}",
        type="primary",
        use_container_width=True,
        disabled=not can_generate,
        key="btn_pq_generar",
    )
    if not can_generate:
        st.caption("Escribe el tema principal para habilitar la generación.")

    result_key = f"pq_result_{marca_key}_{red_sel}"

    # ── Limpiar ────────────────────────────────────────────────────────────────
    col_sp, col_clear = st.columns([4, 1])
    with col_clear:
        if st.button("🗑️ Limpiar", use_container_width=True, key="btn_pq_clear"):
            st.session_state.pop(result_key, None)
            st.rerun()

    # ── Generación con streaming ───────────────────────────────────────────────
    if gen_btn and can_generate:
        st.session_state.pop(result_key, None)
        prompt = _build_quick_prompt(brand, tipo_ctx, tema.strip(), contexto_extra, redes)

        _prov_lbl2    = "Gemini" if _ai_provider() == 'gemini' else "Claude"
        thinking_ph   = st.info(f"⏳ {_prov_lbl2} está creando el post… (10-30 segundos)")
        result_holder = st.empty()
        full_text     = ""

        try:
            for chunk in _stream_quick_post(prompt):
                if not full_text:
                    thinking_ph.empty()
                full_text += chunk
                result_holder.markdown(full_text + "▌")
            result_holder.markdown(full_text)
            st.session_state[result_key] = {
                'text':  full_text,
                'tema':  tema.strip(),
                'redes': red_sel,
                'tipo':  tipo_ctx,
            }
        except Exception as e:
            thinking_ph.empty()
            result_holder.empty()
            st.error(f"Error al conectar con Claude: {e}")
            return

    # ── Mostrar resultado guardado ─────────────────────────────────────────────
    elif result_key in st.session_state:
        saved = st.session_state[result_key]
        st.markdown("---")
        st.markdown(
            f"### Resultado — {saved.get('tipo','')} · {saved.get('redes','')}  \n"
            f"**Tema:** {saved.get('tema','')}"
        )
        st.markdown(saved['text'])

    # ── Acciones post-generación ───────────────────────────────────────────────
    if result_key in st.session_state:
        saved = st.session_state[result_key]
        st.markdown("---")
        col_dl, col_copy = st.columns([2, 3])
        with col_dl:
            nombre = f"Post_{brand.get('label','').replace(' ','_')}_{saved.get('redes','').replace('/','_').replace(' ','')}.txt"
            st.download_button(
                "📥  Descargar como .txt",
                data=saved['text'].encode('utf-8'),
                file_name=nombre,
                mime="text/plain",
                use_container_width=True,
            )
        with col_copy:
            with st.expander("📋 Ver texto completo para copiar"):
                st.text_area(
                    "Selecciona todo y copia (Ctrl+A, Ctrl+C)",
                    value=saved['text'],
                    height=300,
                    key="pq_copy_area",
                )

        # ── Agregar a Parrilla ─────────────────────────────────────────────────
        st.markdown("---")
        with st.expander("➕  Agregar a Parrilla del mes", expanded=False):
            from datetime import date as _date
            from database import save_parrilla_posts
            import sync as _sync

            _MESES_ES = {1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",
                         7:"Julio",8:"Agosto",9:"Septiembre",10:"Octubre",
                         11:"Noviembre",12:"Diciembre"}
            _DIAS_ES  = {0:'Lunes',1:'Martes',2:'Miércoles',3:'Jueves',
                         4:'Viernes',5:'Sábado',6:'Domingo'}

            sections = _parse_post_sections(saved['text'], saved.get('redes', ''))

            st.caption("Revisa y edita los campos — se guardarán exactamente como los ves aquí.")

            # ── Fila 1: fecha · pilar · formato · estado ──────────────────────
            c1, c2, c3, c4 = st.columns([1.1, 1.6, 1.6, 1.2])
            fecha_post  = c1.date_input("📅 Fecha", value=_date.today(), key="pq_par_fecha")
            pilares_opts   = ([p['label'] for p in brand.get('rrss', {}).get('pilares', [])]
                              or ['General'])
            formatos_opts  = (brand.get('rrss', {}).get('formatos', [])
                              or ['Post', 'Carrusel', 'Video', 'Historia'])
            pilar_sel   = c2.selectbox("Pilar",   pilares_opts,                       key="pq_par_pilar")
            formato_sel = c3.selectbox("Formato", formatos_opts,                      key="pq_par_formato")
            estado_sel  = c4.selectbox("Estado",  ['Borrador','En diseño','Aprobado','Publicado'],
                                                                                       key="pq_par_estado")

            # ── Tema ──────────────────────────────────────────────────────────
            tema_val = st.text_input("Tema (título corto del post)",
                                     value=saved.get('tema', ''), key="pq_par_tema")

            # ── Copys ─────────────────────────────────────────────────────────
            cl, cf = st.columns(2)
            copy_li = cl.text_area("Copy LinkedIn",
                                   value=sections['copy_linkedin'],
                                   height=240, key="pq_par_li",
                                   help="Copy formal para LinkedIn")
            copy_fb = cf.text_area("Copy Facebook / Instagram",
                                   value=sections['copy_facebook'],
                                   height=240, key="pq_par_fb",
                                   help="Copy conversacional — mismo texto para ambas redes")

            # ── Hashtags · CTA ────────────────────────────────────────────────
            ch, cc = st.columns(2)
            hashtags_val = ch.text_input("Hashtags", value=sections['hashtags'], key="pq_par_ht")
            cta_val      = cc.text_input("CTA",      value=sections['cta'],      key="pq_par_cta")

            # ── Arte sugerida ─────────────────────────────────────────────────
            arte_val = st.text_area("Arte Sugerida (descripción para el diseñador)",
                                    value=sections['arte_sugerencia'],
                                    height=90, key="pq_par_arte")

            st.markdown("---")
            if st.button("✅  Guardar en Parrilla", type="primary",
                         use_container_width=True, key="btn_pq_par_save"):
                post_row = {
                    'fecha':           str(fecha_post),
                    'dia_semana':      _DIAS_ES[fecha_post.weekday()],
                    'tipo_dia':        'regular',
                    'pilar':           pilar_sel,
                    'formato':         formato_sel,
                    'tema':            tema_val,
                    'copy_linkedin':   copy_li,
                    'copy_facebook':   copy_fb,
                    'arte_sugerencia': arte_val,
                    'hashtags':        hashtags_val,
                    'cta':             cta_val,
                    'estado':          estado_sel,
                }
                marca_db = 'Kabat One' if marca_key == 'k1' else 'SYM'
                save_parrilla_posts(marca_db, fecha_post.year, fecha_post.month, [post_row])

                if _sync.github_configured():
                    with st.spinner("Sincronizando con GitHub…"):
                        _sync.push()

                st.success(
                    f"✅ Post guardado en la parrilla de "
                    f"**{_MESES_ES[fecha_post.month]} {fecha_post.year}** "
                    f"({_DIAS_ES[fecha_post.weekday()]} {str(fecha_post)}). "
                    "Ve a **📅 Parrilla de Contenido** para verlo."
                )
