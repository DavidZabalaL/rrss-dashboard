# modules/data_loader.py — Importar datos desde Excel/CSV

import streamlit as st
from parsers import (
    detect_file, parse_facebook, parse_linkedin_metricas,
    parse_linkedin_seguidores, parse_instagram,
    parse_contenido_linkedin, parse_contenido_facebook, parse_contenido_instagram,
    get_excel_sheet_names,
)
from database import save_metricas_bulk, save_contenido_posts
import sync


def show_uploader():
    user_role = st.session_state.get('current_user', {}).get('role', 'viewer')
    if user_role not in ('admin', 'uploader'):
        st.markdown("""
        <h2 style="color:#1e90ff;font-size:1.5rem;font-weight:700;margin-bottom:2px;">
          📁 Importar Datos
        </h2>""", unsafe_allow_html=True)
        st.warning("⛔ No tienes permisos para importar datos. Contacta al administrador.")
        return

    marca = st.session_state.get('marca_activa', 'k1')
    marca_nombre = 'Kabat One' if marca == 'k1' else 'SYM'

    st.markdown(f"""
    <h2 style="color:#1e90ff;font-size:1.5rem;font-weight:700;margin-bottom:2px;">
      📁 Importar Datos — {marca_nombre}
    </h2>
    <p style="color:#5b8db8;font-size:.85rem;margin-top:0;">
      Sube archivos Excel de las redes sociales. Nomenclatura recomendada:
      <code>k1_linkedin.xlsx</code> · <code>k1_contenido.xlsx</code> · <code>sym_facebook.xlsx</code>
    </p>
    """, unsafe_allow_html=True)

    st.markdown("---")

    uploaded = st.file_uploader(
        "Arrastra o selecciona archivos Excel (.xlsx)",
        type=['xlsx', 'xls', 'csv'],
        accept_multiple_files=True,
        key="uploader_files",
    )

    if not uploaded:
        _show_guide()
        return

    if st.button("⬆️ Procesar archivos", type="primary", use_container_width=True):
        _process_files(uploaded, marca_nombre)


def _process_files(files, marca_nombre):
    total_ok, total_err = 0, 0
    for f in files:
        info = detect_file(f.name)
        if info is None:
            st.warning(f"⚠️ `{f.name}` — nombre no reconocido, omitido.")
            total_err += 1
            continue

        # Usar marca del archivo si está presente; si no, la activa
        marca = info['marca_nombre'] or marca_nombre

        try:
            f.seek(0)
            parser = info['parser']

            if info['es_contenido']:
                if info['parser'] == 'contenido_facebook':
                    rows = parse_contenido_facebook(f, marca, f.name)
                elif info['parser'] == 'contenido_instagram':
                    rows = parse_contenido_instagram(f, marca, f.name)
                else:
                    rows = parse_contenido_linkedin(f, marca, f.name)
                save_contenido_posts(rows)
                msg = f"✅ `{f.name}` — {len(rows)} publicaciones guardadas ({info['red']})"
                # Si el archivo también tiene métricas diarias, procesarlas
                extras = _linkedin_extra_sheets(f, marca, f.name,
                                                skip={'contenido'})
                msg += extras

            elif parser == 'linkedin_metricas':
                rows = parse_linkedin_metricas(f)
                _tag_rows(rows, marca, info['red'], f.name)
                save_metricas_bulk(rows)
                msg = f"✅ `{f.name}` — {len(rows)} registros LinkedIn"
                # Si el archivo también trae publicaciones o seguidores, procesarlos
                extras = _linkedin_extra_sheets(f, marca, f.name,
                                                skip={'metricas'})
                msg += extras

            elif parser == 'linkedin_seguidores':
                rows = parse_linkedin_seguidores(f)
                _tag_rows(rows, marca, info['red'], f.name)
                save_metricas_bulk(rows)
                msg = f"✅ `{f.name}` — {len(rows)} registros seguidores"
                # Si el archivo también trae métricas o publicaciones, procesarlos
                extras = _linkedin_extra_sheets(f, marca, f.name,
                                                skip={'seguidores'})
                msg += extras

            elif parser == 'facebook':
                metrica_key = _guess_metrica_facebook(f.name)
                rows = parse_facebook(f, metrica_key)
                _tag_rows(rows, marca, 'Facebook', f.name)
                save_metricas_bulk(rows)
                msg = f"✅ `{f.name}` — {len(rows)} registros Facebook ({metrica_key})"

            elif parser == 'instagram':
                metrica_key = _guess_metrica_instagram(f.name)
                rows = parse_instagram(f, metrica_key)
                _tag_rows(rows, marca, 'Instagram', f.name)
                save_metricas_bulk(rows)
                msg = f"✅ `{f.name}` — {len(rows)} registros Instagram ({metrica_key})"

            else:
                msg = f"⚠️ `{f.name}` — parser desconocido"

            st.success(msg)
            total_ok += 1

        except Exception as e:
            st.error(f"❌ `{f.name}` — Error: {e}")
            total_err += 1

    if total_ok:
        # Sincronizar con GitHub si está configurado
        if sync.github_configured():
            with st.spinner("Sincronizando con GitHub…"):
                ok = sync.push()
            if ok:
                st.info("☁️ Base de datos sincronizada con GitHub.")
        st.success(f"✅ {total_ok} archivo(s) procesado(s) correctamente.")
        st.rerun()


def _tag_rows(rows, marca, red, archivo):
    for r in rows:
        r.setdefault('marca',   marca)
        r.setdefault('red',     red)
        r.setdefault('archivo', archivo)


def _linkedin_extra_sheets(file_obj, marca, archivo, skip):
    """
    Lee las pestañas adicionales de un export LinkedIn multi-hoja y procesa
    las que no fueron el parser principal (controlado por `skip`).
    Retorna string con mensajes adicionales para concatenar al msg principal.
    """
    from database import save_metricas_bulk, save_contenido_posts

    try:
        sheets = get_excel_sheet_names(file_obj)
    except Exception:
        return ''

    extra = ''

    # Pestaña de métricas diarias
    if 'metricas' not in skip:
        indicadores = next((s for s in sheets if 'indicador' in s.lower()), None)
        if indicadores:
            try:
                file_obj.seek(0)
                rows = parse_linkedin_metricas(file_obj, sheet_name=indicadores)
                _tag_rows(rows, marca, 'LinkedIn', archivo)
                save_metricas_bulk(rows)
                extra += f'\n   ↳ Pestaña **{indicadores}**: {len(rows)} registros de métricas'
            except Exception as e:
                extra += f'\n   ↳ ⚠️ No se pudo leer **{indicadores}**: {e}'

    # Pestaña de publicaciones individuales
    if 'contenido' not in skip:
        publicaciones = next((s for s in sheets if 'publicacion' in s.lower()), None)
        if publicaciones:
            try:
                file_obj.seek(0)
                rows = parse_contenido_linkedin(file_obj, marca, archivo,
                                                sheet_name=publicaciones)
                save_contenido_posts(rows)
                extra += f'\n   ↳ Pestaña **{publicaciones}**: {len(rows)} publicaciones guardadas'
            except Exception as e:
                extra += f'\n   ↳ ⚠️ No se pudo leer **{publicaciones}**: {e}'

    # Pestaña de seguidores
    if 'seguidores' not in skip:
        seg_sheet = next((s for s in sheets if 'seguidor' in s.lower()), None)
        if seg_sheet:
            try:
                file_obj.seek(0)
                rows = parse_linkedin_seguidores(file_obj, sheet_name=seg_sheet)
                _tag_rows(rows, marca, 'LinkedIn', archivo)
                save_metricas_bulk(rows)
                extra += f'\n   ↳ Pestaña **{seg_sheet}**: {len(rows)} registros de seguidores'
            except Exception as e:
                extra += f'\n   ↳ ⚠️ No se pudo leer **{seg_sheet}**: {e}'

    return extra


def _guess_metrica_facebook(filename):
    stem = filename.lower()
    mapping = {
        'visualizaciones': 'visualizaciones', 'views': 'visualizaciones',
        'seguidores': 'incremento_seguidores', 'followers': 'incremento_seguidores',
        'interaccion': 'interaccion', 'engagement': 'interaccion',
        'visitas': 'visitas', 'visits': 'visitas',
        'alcance': 'alcance', 'reach': 'alcance',
    }
    for kw, key in mapping.items():
        if kw in stem:
            return key
    return 'visualizaciones'


def _guess_metrica_instagram(filename):
    stem = filename.lower()
    mapping = {
        'visualizaciones': 'visualizaciones', 'views': 'visualizaciones',
        'seguidores': 'incremento_seguidores', 'followers': 'incremento_seguidores',
        'alcance': 'alcance', 'reach': 'alcance',
        'interaccion': 'interaccion', 'engagement': 'interaccion',
        'visitas': 'visitas',
    }
    for kw, key in mapping.items():
        if kw in stem:
            return key
    return 'visualizaciones'


def _show_guide():
    st.markdown("#### 📖 Nomenclatura de archivos")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
**Métricas diarias**

| Archivo | Métrica |
|---|---|
| `k1_linkedin_impresiones.xlsx` | Impresiones + Alcance + Reacciones + Comentarios |
| `k1_linkedin_incremento_seguidores.xlsx` | Nuevos seguidores LinkedIn |
| `k1_facebook_visualizaciones.xlsx` | Visualizaciones Facebook |
| `k1_facebook_incremento_seguidores.xlsx` | Nuevos seguidores Facebook |
| `k1_facebook_interaccion.xlsx` | Interacciones Facebook |
| `k1_facebook_visitas.xlsx` | Visitas Facebook |
| `k1_instagram_visualizaciones.xlsx` | Visualizaciones Instagram |
| `k1_instagram_incremento_seguidores.xlsx` | Nuevos seguidores Instagram |
| `k1_instagram_interaccion.xlsx` | Interacciones Instagram |
| `k1_instagram_visitas.xlsx` | Visitas Instagram |

> Sustituye `k1_` por `sym_` para archivos de SYM.
        """)

    with col2:
        st.markdown("""
**Contenido (publicaciones)**

| Archivo | Descripción |
|---|---|
| `k1_contenido_linkedin.xlsx` | Posts LinkedIn Kabat One |
| `k1_contenido_facebook.xlsx` | Posts Facebook Kabat One |
| `k1_contenido_instagram.xlsx` | Posts Instagram Kabat One |
| `sym_contenido_linkedin.xlsx` | Posts LinkedIn SYM |
| `sym_contenido_facebook.xlsx` | Posts Facebook SYM |
| `sym_contenido_instagram.xlsx` | Posts Instagram SYM |

**Formato por tipo de archivo:**

| Tipo | Origen |
|---|---|
| LinkedIn métricas | Export LinkedIn Analytics |
| LinkedIn contenido | Export LinkedIn Analytics → Publicaciones |
| Facebook / Instagram métricas | Export Meta Business Suite (CSV → xlsx) |
| Facebook / Instagram contenido | Export Meta Business Suite → Publicaciones |
        """)
