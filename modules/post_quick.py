# modules/post_quick.py — Generador de post individual con IA

import os
import json
import re
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
    li = 'LinkedIn' in redes
    fb = 'Facebook' in redes

    sections = []
    if li:
        sections.append("## LinkedIn\n\n[copy completo para LinkedIn: hook, cuerpo y emojis si aplica]")
    if fb:
        sections.append("## Facebook / Instagram\n\n[copy completo para Facebook e Instagram: hook, cuerpo y emojis]")
    if not li and not fb:
        sections.append("## Post\n\n[copy completo]")

    sections.append("## Arte Sugerida\n\n[descripción visual en 2-3 líneas: escena, elementos, estilo, colores, composición]")
    sections.append("## Texto en Imagen\n\nHeadline: [título impactante, máx 8 palabras]\nSubtítulo: [complemento o dato clave, máx 10 palabras]")

    return (
        '\n\n'.join(sections)
        + "\n\nCTA: [texto del CTA en una sola línea]\n"
        + "Hashtags: [todos los hashtags en una sola línea, ej: #Tag1 #Tag2 #Tag3]"
    )


def _parse_post_sections(text: str, redes_str: str) -> dict:
    result = {
        'copy_linkedin': '', 'copy_facebook': '',
        'hashtags': '', 'arte_sugerencia': '', 'cta': '', 'texto_imagen': '',
    }

    # Split on any ## heading (works with Gemini's actual output format)
    parts = re.split(r'\n(?=#{1,3}\s)', '\n' + text)

    for part in parts:
        part = part.strip()
        if not part:
            continue
        lines = part.split('\n')
        heading = re.sub(r'^#{1,3}\s*|\*\*', '', lines[0]).strip().lower()
        content = '\n'.join(lines[1:]).strip()

        if re.search(r'linkedin', heading):
            result['copy_linkedin'] = content
        elif re.search(r'facebook|instagram', heading):
            result['copy_facebook'] = content
        elif re.search(r'arte\s*sugerid', heading):
            result['arte_sugerencia'] = content[:500]
        elif re.search(r'texto\s*en\s*imagen', heading):
            result['texto_imagen'] = content[:400]

    # CTA y Hashtags aparecen como líneas sueltas al final
    cta_m = re.search(r'^CTA:\s*(.+)$', text, re.M | re.I)
    ht_m  = re.search(r'^Hashtags?:\s*(.+)$', text, re.M | re.I)
    if cta_m:
        result['cta'] = cta_m.group(1).strip()
    if ht_m:
        result['hashtags'] = ht_m.group(1).strip()
    else:
        all_tags = list(dict.fromkeys(re.findall(r'#\w[\w\d]*', text)))
        result['hashtags'] = ' '.join(all_tags[:12])

    # Fallback solo si el modelo no usó encabezados reconocibles
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

    all_tags    = [t for tags in htags.values() for t in tags]
    marca_tags  = htags.get('marca', [])
    pilares_txt = ' | '.join(p['label'] for p in pilares)

    if 'LinkedIn' in redes and 'Facebook' in redes:
        redes_instrucciones = (
            "Genera el post para AMBAS redes:\n"
            "- LinkedIn: tono formal, autoridad, 2-3 párrafos\n"
            "- Facebook/Instagram: tono conversacional, 1-2 párrafos cortos, emojis moderados"
        )
    elif 'LinkedIn' in redes:
        redes_instrucciones = "Genera SOLO para LinkedIn: tono formal, autoridad, 2-3 párrafos."
    else:
        redes_instrucciones = "Genera SOLO para Facebook/Instagram: tono conversacional, 1-2 párrafos, emojis moderados."

    extra_section = f"\nCONTEXTO ADICIONAL:\n{contexto_extra[:3000]}\n" if contexto_extra.strip() else ""

    return f"""Eres un Community Manager Senior especializado en marcas B2G de tecnología y seguridad pública en México.

=== BRIEF: {brand.get('label','')} ===
Tagline: "{brand.get('tagline','')}"
Audiencia: {brand.get('audience','')}
Tono: {tone.get('style','')}
Evitar: {', '.join(tone.get('avoid',[]))}
Pilares: {pilares_txt}
Formatos: {', '.join(formatos[:6])}
Hashtags de marca (SIEMPRE incluir): {' '.join(marca_tags)}
Pool de hashtags: {' '.join(all_tags[:16])}
CTAs disponibles: {' | '.join(cta_list[:4])}

=== SOLICITUD ===
Tipo: {tipo_contexto}
Tema: {tema}
{extra_section}
=== INSTRUCCIONES ===
{redes_instrucciones}

Genera:
1. HOOK específico que detenga el scroll (no genérico)
2. CUERPO con el valor/dato/historia
3. CTA específico para la audiencia
4. HASHTAGS (5-7 del pool + al menos uno de marca)
5. ARTE SUGERIDA: descripción concreta y accionable para el diseñador
6. TEXTO EN IMAGEN: headline y subtítulo que irán impresos dentro del diseño gráfico

FORMATO OBLIGATORIO — usa EXACTAMENTE estos encabezados:

{_format_section(redes)}"""


def _stream_quick_post(prompt):
    if _ai_provider() == 'gemini':
        import urllib.request
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
    _role = st.session_state.get('current_user', {}).get('role', 'visita')
    if _role == 'visita':
        st.warning("No tienes permiso para usar este módulo.")
        return

    st.title("✍️ Generador de Post Individual")
    st.caption(
        "Define el tema y contexto — Nebula genera el copy completo con "
        "CTA, hashtags, texto en imagen y sugerencia de arte lista para usar."
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
        "Generar para", _REDES_OPCIONES, index=2, horizontal=True, key="pq_redes",
    )
    redes = (['LinkedIn'] if red_sel == 'LinkedIn'
             else ['Facebook'] if red_sel == 'Facebook / Instagram'
             else ['LinkedIn', 'Facebook'])

    st.markdown("### 4. Contexto adicional (opcional)")
    contexto_extra = st.text_area(
        "Pega aquí noticias, datos, descripción de producto, comunicado, etc.",
        placeholder=(
            "Ej: La Secretaría de Seguridad de [Estado] implementó el sistema en julio 2026, "
            "logrando reducir el tiempo de respuesta ante incidentes de 12 a 4 minutos…"
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

    col_sp, col_clear = st.columns([4, 1])
    with col_clear:
        if st.button("🗑️ Limpiar", use_container_width=True, key="btn_pq_clear"):
            st.session_state.pop(result_key, None)
            st.rerun()

    # ── Streaming ──────────────────────────────────────────────────────────────
    if gen_btn and can_generate:
        st.session_state.pop(result_key, None)
        prompt = _build_quick_prompt(brand, tipo_ctx, tema.strip(), contexto_extra, redes)

        thinking_ph = st.empty()
        thinking_ph.info(f"⏳ {_prov_lbl} está creando el post…")
        full_text = ""

        try:
            for chunk in _stream_quick_post(prompt):
                full_text += chunk
                thinking_ph.info(f"✍️ Generando… {len(full_text)} caracteres")
            thinking_ph.empty()

            sections = _parse_post_sections(full_text, red_sel)
            st.session_state[result_key] = {
                'text':     full_text,
                'tema':     tema.strip(),
                'redes':    red_sel,
                'tipo':     tipo_ctx,
                'sections': sections,
            }
        except Exception as e:
            thinking_ph.empty()
            st.error(f"Error al generar: {e}")
            return

    # ── Resultado estructurado ─────────────────────────────────────────────────
    if result_key not in st.session_state:
        return

    saved    = st.session_state[result_key]
    sections = saved.get('sections') or _parse_post_sections(saved['text'], saved.get('redes', ''))

    st.markdown("---")
    st.markdown(
        f"### ✅ Post generado — {saved.get('tipo','')} · {saved.get('redes','')}  \n"
        f"**Tema:** {saved.get('tema','')}"
    )

    # Copy LinkedIn
    if sections.get('copy_linkedin'):
        st.markdown("**💼 Copy LinkedIn**")
        _li_val = st.text_area(
            "Copy LinkedIn", value=sections['copy_linkedin'],
            height=220, key=f"pq_edit_li_{result_key}", label_visibility="collapsed",
        )

    # Copy Facebook
    if sections.get('copy_facebook'):
        st.markdown("**📱 Copy Facebook / Instagram**")
        _fb_val = st.text_area(
            "Copy Facebook", value=sections['copy_facebook'],
            height=220, key=f"pq_edit_fb_{result_key}", label_visibility="collapsed",
        )

    # Texto en Imagen
    st.markdown("**✏️ Texto en Imagen**")
    _ti_val = st.text_area(
        "Texto en Imagen", value=sections.get('texto_imagen', ''),
        height=100, key=f"pq_edit_ti_{result_key}", label_visibility="collapsed",
        help="Headline y subtítulo que irán impresos dentro del diseño gráfico",
    )

    # Hashtags + CTA en columnas
    _hc1, _hc2 = st.columns(2)
    with _hc1:
        st.markdown("**🏷️ Hashtags**")
        _ht_val = st.text_area(
            "Hashtags", value=sections.get('hashtags', ''),
            height=75, key=f"pq_edit_ht_{result_key}", label_visibility="collapsed",
        )
    with _hc2:
        st.markdown("**📢 CTA**")
        _cta_val = st.text_input(
            "CTA", value=sections.get('cta', ''),
            key=f"pq_edit_cta_{result_key}", label_visibility="collapsed",
        )

    # Arte Sugerida
    st.markdown("**🎨 Arte Sugerida**")
    _arte_val = st.text_area(
        "Arte Sugerida", value=sections.get('arte_sugerencia', ''),
        height=100, key=f"pq_edit_arte_{result_key}", label_visibility="collapsed",
    )

    # Descarga completa
    st.markdown("---")
    nombre = f"Post_{brand.get('label','').replace(' ','_')}_{saved.get('redes','').replace('/','_').replace(' ','')}.txt"
    st.download_button(
        "📥  Descargar post completo como .txt",
        data=saved['text'].encode('utf-8'),
        file_name=nombre,
        mime="text/plain",
        use_container_width=False,
    )

    # ── Imagen: Prompts + Generación directa + Editor completo ────────────────
    st.markdown("---")
    with st.expander("🎨  Imagen — Prompts, Generación y Editor", expanded=False, key=f"pq_exp_img_{result_key}"):
        from modules.parrilla import (
            _build_image_prompt_request, _call_claude_json, _parse_json_obj,
            _MASTER_PROMPTS, _generate_imagen, _edit_imagen_gemini,
            _pleca_ui, _logo_adder_ui,
        )

        _img_row = {
            'Tema':            saved.get('tema', ''),
            'Pilar':           (brand.get('rrss', {}).get('pilares', [{}]) or [{}])[0].get('label', ''),
            'Arte Sugerida':   sections.get('arte_sugerencia', ''),
            'Copy LinkedIn':   sections.get('copy_linkedin', ''),
            'Texto en Imagen': sections.get('texto_imagen', ''),
            'Formato':         'Imagen estática',
            'Fecha':           '',
            'Tipo':            'regular',
        }

        # Estilo + formato
        _pq_style_map = {
            'Libre (sin estilo fijo)': 'libre',
            'Isométrico':              'isometric',
            'Cards corporativo':       'cards',
            'Infografía':              'infographic',
        }
        _sc1, _sc2 = st.columns([3, 2])
        _pq_style_sel = _sc1.radio(
            "Estilo visual", list(_pq_style_map.keys()), key="pq_img_style",
        )
        _pq_style_val = _pq_style_map[_pq_style_sel]
        _pq_red_img = _sc2.radio(
            "Formato destino",
            ["LinkedIn (1200×628)", "Instagram / Facebook (1080×1080)", "Ambos"],
            key="pq_img_red",
        )

        _ti_img = sections.get('texto_imagen', '')
        if _ti_img and str(_ti_img).strip().lower() not in ('nan', 'none', ''):
            st.caption(f"✏️ Texto en imagen detectado: *{str(_ti_img)[:100]}*")

        # ── Prompts ──────────────────────────────────────────────────────────
        _pq_img_cache = f"pq_img_prompts_{marca_key}"
        if st.button("✨  Generar Prompts (ChatGPT + Gemini)",
                     use_container_width=True, key="btn_pq_img_prompt"):
            st.session_state.pop(_pq_img_cache, None)
            _pq_req = _build_image_prompt_request(_img_row, brand, _pq_red_img, _pq_style_val)
            with st.spinner("Generando prompts… (10-20 seg)"):
                try:
                    _pq_raw = _call_claude_json(_pq_req)
                    _pq_res = _parse_json_obj(_pq_raw)
                    if not _pq_res:
                        _pq_res = {'error': 'No se pudo parsear', 'raw': _pq_raw}
                    st.session_state[_pq_img_cache] = _pq_res
                except Exception as _e_pq:
                    st.error(f"Error al generar prompts: {_e_pq}")

        _pq_prompt_gen = ''
        if _pq_img_cache in st.session_state:
            _pq_res = st.session_state[_pq_img_cache]
            if 'error' not in _pq_res:
                _pq_desc = _pq_res.get('descripcion_corta', '')
                if _pq_desc:
                    st.caption(f"**Descripción:** {_pq_desc}")
                _col_d, _col_g = st.columns(2)
                with _col_d:
                    st.markdown("**🤖 DALL-E 3 · ChatGPT**")
                    _pq_dalle  = _pq_res.get('dalle3', {})
                    _pq_pt     = _pq_dalle.get('prompt', '')
                    _pq_full_d = f"{_pq_pt}\n\n{_MASTER_PROMPTS[_pq_style_val]}" if _pq_style_val in _MASTER_PROMPTS else _pq_pt
                    st.code(_pq_full_d, language=None)
                    if _pq_dalle.get('notas'):
                        st.caption(f"💡 {_pq_dalle['notas']}")
                with _col_g:
                    st.markdown("**🌐 Gemini Imagen · Google**")
                    _pq_gem    = _pq_res.get('gemini', {})
                    _pq_ptg    = _pq_gem.get('prompt', '')
                    _pq_full_g = f"{_pq_ptg}\n\n{_MASTER_PROMPTS[_pq_style_val]}" if _pq_style_val in _MASTER_PROMPTS else _pq_ptg
                    st.code(_pq_full_g, language=None)
                    if _pq_gem.get('notas'):
                        st.caption(f"💡 {_pq_gem['notas']}")
                _pq_prompt_gen = _pq_full_g

        # ── Generación directa con Imagen 4 ──────────────────────────────────
        st.markdown("---")
        st.markdown("### 🖼️ Generar imagen con Imagen 4")

        if 'LinkedIn' in _pq_red_img and 'Instagram' not in _pq_red_img:
            _pq_aspect  = '16:9'
            _pq_asp_lbl = 'LinkedIn 16:9'
        elif 'Instagram' in _pq_red_img or 'Facebook' in _pq_red_img:
            _asp_sel = st.radio(
                "Formato", ["Cuadrado (1:1 · 1080×1080)", "Vertical (4:5 · 1080×1350)"],
                horizontal=True, key="pq_asp_ig",
            )
            _pq_aspect  = '4:5' if '4:5' in _asp_sel else '1:1'
            _pq_asp_lbl = _asp_sel
        else:
            _asp_sel = st.radio(
                "Formato", ["LinkedIn (16:9)", "Cuadrado (1:1)", "Vertical (4:5)"],
                horizontal=True, key="pq_asp_all",
            )
            _pq_aspect  = '16:9' if 'LinkedIn' in _asp_sel else ('4:5' if '4:5' in _asp_sel else '1:1')
            _pq_asp_lbl = _asp_sel

        _qual_sel = st.radio(
            "Motor", ["⚡ Rápida", "⭐ Estándar", "💎 Ultra", "🍌 Nano Banana"],
            index=1, horizontal=True, key="pq_img_quality",
        )
        _qual_map = {
            "⚡ Rápida": "fast", "⭐ Estándar": "standard",
            "💎 Ultra": "ultra", "🍌 Nano Banana": "nano_banana",
        }
        _pq_quality = _qual_map[_qual_sel]
        _time_est   = {"fast": "~10 seg", "standard": "~20 seg", "ultra": "~40 seg", "nano_banana": "~30 seg"}

        _pq_gen_key  = f"pq_gen_img_{marca_key}"
        _pq_edit_key = f"pq_gen_edits_{marca_key}"

        _gc1, _gc2 = st.columns([4, 1])
        _pq_gen_btn = _gc1.button(
            "🎨  Generar imagen con Imagen 4",
            type="primary", use_container_width=True,
            key="btn_pq_gen_img",
            disabled=not _pq_prompt_gen,
        )
        _gc2.caption(_time_est[_pq_quality])

        if not _pq_prompt_gen:
            st.caption("⬆️ Genera los prompts primero para habilitar la generación directa.")

        _pq_gen_err = st.empty()
        if _pq_gen_btn and _pq_prompt_gen:
            st.session_state.pop(_pq_gen_key, None)
            st.session_state.pop(_pq_edit_key, None)
            _spin_map = {"fast": "10-15", "standard": "20-30", "ultra": "35-50", "nano_banana": "30-60"}
            with st.spinner(f"Generando imagen… ({_spin_map.get(_pq_quality, '20-40')} segundos)"):
                try:
                    _gen_bytes = _generate_imagen(_pq_prompt_gen, _pq_aspect, _pq_quality)
                    st.session_state[_pq_gen_key] = {'bytes': _gen_bytes, 'aspect': _pq_asp_lbl}
                except Exception as _ge:
                    _pq_gen_err.error(f"Error al generar imagen: {_ge}")

        # Alternativa: subir imagen externa
        st.markdown("---")
        _pq_upload = st.file_uploader(
            "O sube una imagen externa (JPG/PNG/WEBP)",
            type=['png', 'jpg', 'jpeg', 'webp'],
            key="pq_img_upload",
        )
        if _pq_upload:
            _up_bytes = _pq_upload.read()
            _prev = st.session_state.get(_pq_gen_key, {})
            if _prev.get('bytes') != _up_bytes:
                st.session_state[_pq_gen_key] = {'bytes': _up_bytes, 'aspect': 'subida'}
                st.session_state.pop(_pq_edit_key, None)

        # ── Editor completo ───────────────────────────────────────────────────
        if _pq_gen_key in st.session_state:
            _pq_saved_img = st.session_state[_pq_gen_key]
            _pq_edits     = st.session_state.setdefault(_pq_edit_key, [])
            _pq_cur       = _pq_edits[-1]['bytes'] if _pq_edits else _pq_saved_img['bytes']
            _pq_ver       = len(_pq_edits) + 1

            st.markdown("---")
            _pq_col_img, _pq_col_ctrl = st.columns([1, 1], gap="large")

            with _pq_col_img:
                st.image(_pq_cur, use_container_width=True)
                if _pq_edits:
                    st.caption(f"Versión {_pq_ver} · {len(_pq_edits)} edición(es) aplicada(s)")

                _pq_fname = (
                    f"post_{brand.get('label','').replace(' ','_')}_"
                    f"{saved.get('tema','')[:25].replace(' ','_')}_v{_pq_ver}.png"
                )
                st.download_button(
                    f"📥 Descargar v{_pq_ver} (.png)",
                    data=_pq_cur, file_name=_pq_fname, mime="image/png",
                    use_container_width=True, key="pq_dl_img",
                )

                _pq_logo_res = _logo_adder_ui(f"pq_{marca_key}", _pq_cur, brand)
                if _pq_logo_res is not None:
                    if _pq_edits and _pq_edits[-1].get('instruction') == '[logo agregado]':
                        _pq_edits[-1] = {'instruction': '[logo agregado]', 'bytes': _pq_logo_res}
                    else:
                        _pq_edits.append({'instruction': '[logo agregado]', 'bytes': _pq_logo_res})
                    st.rerun()

                _pq_pleca_res = _pleca_ui(
                    f"pq_{marca_key}", _pq_cur, brand,
                    texto=sections.get('texto_imagen', ''),
                )
                if _pq_pleca_res is not None:
                    if _pq_edits and _pq_edits[-1].get('instruction') == '[pleca agregada]':
                        _pq_edits[-1] = {'instruction': '[pleca agregada]', 'bytes': _pq_pleca_res}
                    else:
                        _pq_edits.append({'instruction': '[pleca agregada]', 'bytes': _pq_pleca_res})
                    st.rerun()

            with _pq_col_ctrl:
                st.markdown("#### ✏️ Editar imagen con IA")
                st.caption("Describe qué quieres cambiar. Cada edición genera una nueva versión.")

                _pq_edit_instr = st.text_area(
                    "Instrucción",
                    placeholder=(
                        "Ejemplos:\n"
                        "• Cambia el fondo a azul oscuro\n"
                        "• Agrega iluminación tecnológica\n"
                        "• Hazla más minimalista\n"
                        "• Elimina el texto y deja la escena"
                    ),
                    height=150,
                    key="pq_img_ai_instr",
                )

                _pq_apply_col, _pq_undo_col = st.columns([3, 1])
                with _pq_apply_col:
                    _pq_apply = st.button(
                        "🪄 Aplicar edición",
                        type="primary", use_container_width=True,
                        disabled=not _pq_edit_instr.strip(),
                        key="pq_img_ai_btn",
                    )
                with _pq_undo_col:
                    if st.button("↩️", use_container_width=True,
                                 disabled=not _pq_edits, key="pq_img_undo",
                                 help="Deshacer última edición"):
                        _pq_edits.pop()
                        st.rerun()

                if _pq_edits:
                    st.markdown("**Historial:**")
                    for _ei, _eh in enumerate(_pq_edits):
                        st.caption(f"v{_ei+2}: {_eh['instruction'][:60]}")

                if _pq_apply and _pq_edit_instr.strip():
                    with st.spinner("Aplicando edición… (15-30 seg)"):
                        try:
                            _pq_edited = _edit_imagen_gemini(_pq_cur, _pq_edit_instr.strip())
                            _pq_edits.append({
                                'instruction': _pq_edit_instr.strip(),
                                'bytes': _pq_edited,
                            })
                            st.rerun()
                        except Exception as _ee:
                            st.error(f"Error al editar: {_ee}")

    # ── Agregar a Parrilla ─────────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("➕  Agregar a Parrilla del mes", expanded=False, key=f"pq_exp_par_{result_key}"):
        from datetime import date as _date
        from database import save_parrilla_posts
        import sync as _sync

        _MESES_ES = {1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",
                     7:"Julio",8:"Agosto",9:"Septiembre",10:"Octubre",
                     11:"Noviembre",12:"Diciembre"}
        _DIAS_ES  = {0:'Lunes',1:'Martes',2:'Miércoles',3:'Jueves',
                     4:'Viernes',5:'Sábado',6:'Domingo'}

        st.caption("Revisa y edita — se guardará exactamente como lo ves aquí.")

        c1, c2, c3, c4 = st.columns([1.1, 1.6, 1.6, 1.2])
        fecha_post  = c1.date_input("📅 Fecha", value=_date.today(), key="pq_par_fecha")
        pilares_opts  = ([p['label'] for p in brand.get('rrss', {}).get('pilares', [])] or ['General'])
        formatos_opts = (brand.get('rrss', {}).get('formatos', []) or ['Post', 'Carrusel', 'Video', 'Historia'])
        pilar_sel   = c2.selectbox("Pilar",   pilares_opts,  key="pq_par_pilar")
        formato_sel = c3.selectbox("Formato", formatos_opts, key="pq_par_formato")
        estado_sel  = c4.selectbox("Estado",  ['Borrador','En diseño','Aprobado','Publicado'], key="pq_par_estado")

        tema_val = st.text_input("Tema", value=saved.get('tema', ''), key="pq_par_tema")

        cl, cf = st.columns(2)
        copy_li = cl.text_area("Copy LinkedIn",
                               value=sections.get('copy_linkedin', ''),
                               height=200, key="pq_par_li")
        copy_fb = cf.text_area("Copy Facebook / Instagram",
                               value=sections.get('copy_facebook', ''),
                               height=200, key="pq_par_fb")

        ch, cc = st.columns(2)
        hashtags_val = ch.text_input("Hashtags",
                                     value=sections.get('hashtags', ''),
                                     key="pq_par_ht")
        cta_val      = cc.text_input("CTA",
                                     value=sections.get('cta', ''),
                                     key="pq_par_cta")

        copy_imagen_val = st.text_area(
            "✏️ Texto en Imagen",
            value=sections.get('texto_imagen', ''),
            height=100, key="pq_par_copy_img",
        )
        arte_val = st.text_area("Arte Sugerida",
                                value=sections.get('arte_sugerencia', ''),
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
                'copy_imagen':     copy_imagen_val,
                'arte_sugerencia': arte_val,
                'hashtags':        hashtags_val,
                'cta':             cta_val,
                'estado':          estado_sel,
            }
            marca_db = 'Kabat One' if marca_key == 'k1' else 'SYM'
            save_parrilla_posts(marca_db, fecha_post.year, fecha_post.month, [post_row])

            for _k in ('parrilla_df', 'parrilla_meta', 'parrilla_historial'):
                st.session_state.pop(_k, None)

            if _sync.github_configured():
                with st.spinner("Sincronizando con GitHub…"):
                    _sync.push()

            st.success(
                f"✅ Post guardado en la parrilla de "
                f"**{_MESES_ES[fecha_post.month]} {fecha_post.year}** "
                f"({_DIAS_ES[fecha_post.weekday()]} {str(fecha_post)}). "
                "Ve a **📅 Parrilla de Contenido** para verlo."
            )
