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

Responde en español. Sé directo y concreto — nada de copy genérico o corporativo vacío."""


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

        st.markdown("---")
        st.info(
            "**¿Quedó bien?** Puedes agregar este post a la parrilla del mes "
            "directamente en **📅 Parrilla de Contenido** como una fila nueva."
        )
