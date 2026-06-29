# parsers.py — Detección y parseo de archivos CSV/Excel

import pandas as pd
from pathlib import Path
from config import MARCAS, LINKEDIN_COL_MAP


# ── Detección por nombre de archivo ──────────────────────────────────────────

def detect_file(filename):
    """
    Reconoce marca, red y tipo a partir del nombre.
    Convención: {marca}_{red}_{cualquier_cosa}.xlsx/.csv
    Retorna dict o None.
    """
    stem = Path(filename).stem.lower()

    marca_key, marca_nombre, resto = None, None, stem
    for k, n in MARCAS.items():
        prefix = k + '_'
        if stem.startswith(prefix):
            marca_key   = k
            marca_nombre = n
            resto = stem[len(prefix):]
            break

    if 'contenido' in resto:
        if 'facebook' in resto:
            red, parser = 'Facebook', 'contenido_facebook'
        elif 'instagram' in resto:
            red, parser = 'Instagram', 'contenido_instagram'
        else:
            red, parser = 'LinkedIn', 'contenido_linkedin'
        return {
            'marca_key': marca_key, 'marca_nombre': marca_nombre,
            'red': red, 'es_contenido': True, 'parser': parser,
        }

    if 'linkedin' in resto:
        red    = 'LinkedIn'
        parser = 'linkedin_seguidores' if 'seguidores' in resto else 'linkedin_metricas'
    elif 'facebook' in resto:
        red, parser = 'Facebook', 'facebook'
    elif 'instagram' in resto:
        red, parser = 'Instagram', 'instagram'
    else:
        return None

    return {
        'marca_key': marca_key, 'marca_nombre': marca_nombre,
        'red': red, 'es_contenido': False, 'parser': parser,
    }


# ── Facebook ──────────────────────────────────────────────────────────────────

def parse_facebook(file_obj, metrica_key):
    """
    Formato Facebook export: fila 0 'sep=', fila 1 nombre métrica,
    fila 2 encabezados (Fecha / Primary), fila 3+ datos.
    También acepta XLSX ya limpio (sin filas de cabecera Meta).
    """
    for skip in (2, 0, 1):
        try:
            file_obj.seek(0)
            df = pd.read_excel(file_obj, skiprows=skip, header=0, engine='openpyxl')
            df.columns = [str(c).strip() for c in df.columns]
            date_col = _find_col(df, ['fecha', 'date', 'día'])
            val_col  = _find_col(df, ['primary', 'total', 'valor'])
            if val_col is None and len(df.columns) >= 2:
                val_col = df.columns[1]
            if date_col and val_col:
                df = df[[date_col, val_col]].copy()
                df.columns = ['fecha', 'valor']
                df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
                df = df.dropna(subset=['fecha'])
                if df.empty:
                    continue
                df['valor']   = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
                df['fecha']   = df['fecha'].dt.strftime('%Y-%m-%d')
                df['metrica'] = metrica_key
                return df[['metrica', 'fecha', 'valor']].to_dict('records')
        except Exception:
            pass
    raise ValueError("No se encontraron columnas Fecha/Primary en el archivo Facebook.")


# ── Utilidad: nombres de pestañas ────────────────────────────────────────────

def _excel_engine(file_obj):
    """Detecta si el archivo es .xls (xlrd) o .xlsx (openpyxl) por magic bytes."""
    file_obj.seek(0)
    magic = file_obj.read(4)
    file_obj.seek(0)
    return 'xlrd' if magic == b'\xd0\xcf\x11\xe0' else 'openpyxl'


def get_excel_sheet_names(file_obj):
    """Devuelve lista de nombres de hojas sin consumir el file_obj.
    Soporta tanto .xlsx (openpyxl) como .xls (xlrd)."""
    file_obj.seek(0)
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_obj, read_only=True, data_only=True)
        names = wb.sheetnames
        wb.close()
    except Exception:
        import xlrd
        file_obj.seek(0)
        wb = xlrd.open_workbook(file_contents=file_obj.read())
        names = wb.sheet_names()
    file_obj.seek(0)
    return names


# ── LinkedIn métricas ─────────────────────────────────────────────────────────

def parse_linkedin_metricas(file_obj, sheet_name=None):
    """
    Export LinkedIn Analytics (alcance / impresiones / reacciones / comentarios).
    Encabezados en fila 1 (skiprows=1). Fechas en formato MM/DD/YYYY → dayfirst=False.
    Acepta sheet_name para leer una pestaña específica de un archivo multi-hoja.
    """
    kwargs = {'skiprows': 1, 'header': 0, 'engine': _excel_engine(file_obj)}
    if sheet_name:
        kwargs['sheet_name'] = sheet_name
    df = pd.read_excel(file_obj, **kwargs)
    df.columns = [str(c).strip() for c in df.columns]

    date_col = _find_col(df, ['fecha', 'date'])
    if not date_col:
        raise ValueError("No se encontró columna Fecha en el archivo LinkedIn.")

    df[date_col] = pd.to_datetime(df[date_col], dayfirst=False, errors='coerce')
    df = df.dropna(subset=[date_col])

    rows = []
    for metrica_key, col_nombre in LINKEDIN_COL_MAP.items():
        match = next((c for c in df.columns if col_nombre.lower() in c.lower()), None)
        if match:
            serie = pd.to_numeric(df[match], errors='coerce').fillna(0)
            for fecha, valor in zip(df[date_col], serie):
                rows.append({
                    'metrica': metrica_key,
                    'fecha':   fecha.strftime('%Y-%m-%d'),
                    'valor':   float(valor),
                })
    return rows


# ── LinkedIn seguidores ───────────────────────────────────────────────────────

def parse_linkedin_seguidores(file_obj, sheet_name=None):
    """
    Export de seguidores LinkedIn. Encabezados en fila 0.
    Fechas en formato MM/DD/YYYY → dayfirst=False.
    """
    kw = {'sheet_name': sheet_name} if sheet_name else {}
    df = pd.read_excel(file_obj, header=0, engine='openpyxl', **kw)
    df.columns = [str(c).strip() for c in df.columns]

    date_col = _find_col(df, ['fecha', 'date'])
    val_col  = _find_col(df, ['total de seguidores', 'total seguidores', 'total followers',
                               'nuevos seguidores', 'new followers'])
    if not date_col or not val_col:
        raise ValueError("No se encontraron columnas en el archivo de seguidores LinkedIn.")

    df[date_col] = pd.to_datetime(df[date_col], dayfirst=False, errors='coerce')
    df = df.dropna(subset=[date_col])
    df[val_col]  = pd.to_numeric(df[val_col], errors='coerce').fillna(0)

    return [{
        'metrica': 'incremento_seguidores',
        'fecha':   row[date_col].strftime('%Y-%m-%d'),
        'valor':   float(row[val_col]),
    } for _, row in df.iterrows()]


# ── Instagram ─────────────────────────────────────────────────────────────────

def parse_instagram(file_obj, metrica_key):
    """Formato similar a Facebook (2 columnas: Fecha + valor)."""
    for skip in (0, 1, 2):
        try:
            df = pd.read_excel(file_obj, skiprows=skip, header=0, engine='openpyxl')
            df.columns = [str(c).strip() for c in df.columns]
            date_col = _find_col(df, ['fecha', 'date', 'día'])
            val_col  = _find_col(df, ['valor', 'total', 'primary', 'count',
                                       'reach', 'alcance', 'impresiones',
                                       'interaccion', 'visitas'])
            if val_col is None and len(df.columns) >= 2:
                val_col = df.columns[1]
            if date_col and val_col:
                df = df[[date_col, val_col]].copy()
                df.columns = ['fecha', 'valor']
                df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=False, errors='coerce')
                df = df.dropna(subset=['fecha'])
                df['valor']   = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
                df['fecha']   = df['fecha'].dt.strftime('%Y-%m-%d')
                df['metrica'] = metrica_key
                return df[['metrica', 'fecha', 'valor']].to_dict('records')
        except Exception:
            pass
    raise ValueError("No se pudo parsear el archivo Instagram. Revisa el formato.")


# ── Contenido LinkedIn ────────────────────────────────────────────────────────

def parse_contenido_linkedin(file_obj, marca_nombre, archivo, sheet_name=None):
    """
    Parsea k1_contenido.xlsx / sym_contenido.xlsx (export LinkedIn Analytics).
    Encabezados en fila 0. Fechas en formato MM/DD/YYYY → dayfirst=False.
    Acepta sheet_name para leer la pestaña 'Todas las publicaciones' de un export multi-hoja
    (en ese caso la fila 0 es descripción, los headers están en fila 1 → skiprows=1).
    """
    kwargs = {'header': 0, 'engine': _excel_engine(file_obj)}
    if sheet_name:
        kwargs['sheet_name'] = sheet_name
        kwargs['skiprows']   = 1
    df = pd.read_excel(file_obj, **kwargs)
    df.columns = [str(c).strip() for c in df.columns]

    def fc(*kws):
        for kw in kws:
            m = next((c for c in df.columns if kw.lower() in c.lower()), None)
            if m:
                return m
        return None

    fecha_col  = fc('fecha de creación', 'fecha', 'date', 'día')
    titulo_col = fc('título', 'titulo', 'title', 'copy', 'caption', 'texto')
    tipo_col   = fc('tipo', 'type', 'formato')
    url_col    = fc('enlace', 'url', 'link', 'permalink')
    imp_col    = fc('impresiones', 'impressions')
    viz_col    = fc('visualizaciones', 'views', 'video views')
    clics_col  = fc('clics', 'clicks')
    reac_col   = fc('recomendaciones', 'reacciones', 'likes', 'reactions')
    com_col    = fc('comentarios', 'comments')
    comp_col   = fc('veces compartido', 'compartidas', 'shares', 'reposts')
    seg_col    = fc('seguidores', 'followers')
    tasa_col   = fc('tasa de interacción', 'engagement rate', 'tasa interaccion')

    if not fecha_col:
        raise ValueError("No se encontró columna de fecha en el archivo de contenido.")

    df[fecha_col] = pd.to_datetime(df[fecha_col], dayfirst=False, errors='coerce')
    df = df.dropna(subset=[fecha_col])

    def n(col):
        if col and col in df.columns:
            return pd.to_numeric(df[col], errors='coerce').fillna(0)
        return pd.Series([0.0] * len(df), index=df.index)

    posts = []
    for _, row in df.iterrows():
        posts.append({
            'marca':              marca_nombre,
            'red':                'LinkedIn',
            'fecha':              row[fecha_col].strftime('%Y-%m-%d'),
            'titulo':             str(row.get(titulo_col, ''))[:500] if titulo_col else '',
            'tipo':               str(row.get(tipo_col,  ''))        if tipo_col  else '',
            'url':                str(row.get(url_col,   ''))        if url_col   else '',
            'impresiones':        float(pd.to_numeric(row.get(imp_col,   0), errors='coerce') or 0),
            'visualizaciones':    float(pd.to_numeric(row.get(viz_col,   0), errors='coerce') or 0),
            'clics':              float(pd.to_numeric(row.get(clics_col, 0), errors='coerce') or 0),
            'reacciones':         float(pd.to_numeric(row.get(reac_col,  0), errors='coerce') or 0),
            'comentarios':        float(pd.to_numeric(row.get(com_col,   0), errors='coerce') or 0),
            'compartidos':        float(pd.to_numeric(row.get(comp_col,  0), errors='coerce') or 0),
            'seguidores_ganados': float(pd.to_numeric(row.get(seg_col,   0), errors='coerce') or 0),
            'tasa_interaccion':   float(pd.to_numeric(row.get(tasa_col,  0), errors='coerce') or 0),
            'archivo':            archivo,
        })
    return posts


# ── Contenido Facebook ───────────────────────────────────────────────────────

def parse_contenido_facebook(file_obj, marca_nombre, archivo):
    """
    Parsea k1_contenido_facebook.xlsx — export de Meta Business Suite → Publicaciones.
    Encabezados en fila 0. Fecha en columna 'Hora de publicación' (MM/DD/YYYY HH:MM).
    """
    df = pd.read_excel(file_obj, header=0, engine='openpyxl')
    df.columns = [str(c).strip() for c in df.columns]

    def fc(*kws):
        for kw in kws:
            m = next((c for c in df.columns if kw.lower() in c.lower()), None)
            if m:
                return m
        return None

    fecha_col  = fc('hora de publicación', 'fecha de publicación', 'fecha', 'date')
    titulo_col = fc('título', 'titulo', 'title')
    desc_col   = fc('descripción', 'descripcion', 'description')
    tipo_col   = fc('tipo de publicación', 'tipo', 'type')
    url_col    = fc('enlace permanente', 'enlace', 'url', 'permalink')
    imp_col    = fc('alcance', 'reach', 'impresiones')
    viz_col    = fc('visualizaciones', 'views', 'video views')
    clics_col  = fc('total de clics', 'clics', 'clicks')
    reac_col   = fc('reacciones', 'reactions', 'likes')
    com_col    = fc('comentarios', 'comments')
    comp_col   = fc('veces que se compartió', 'veces compartido', 'shares')
    tasa_col   = fc('tasa de interacción', 'engagement rate')

    if not fecha_col:
        raise ValueError("No se encontró columna de fecha en el archivo de contenido Facebook.")

    df[fecha_col] = pd.to_datetime(df[fecha_col], dayfirst=False, errors='coerce')
    df = df.dropna(subset=[fecha_col])

    def n(col, idx):
        if col and col in df.columns:
            return float(pd.to_numeric(df.loc[idx, col], errors='coerce') or 0)
        return 0.0

    posts = []
    for idx, row in df.iterrows():
        titulo = str(row.get(titulo_col, '') if titulo_col else '')
        if not titulo or titulo == 'nan':
            titulo = str(row.get(desc_col, '') if desc_col else '')

        alcance  = n(imp_col, idx)
        reac_v   = n(reac_col, idx)
        com_v    = n(com_col, idx)
        comp_v   = n(comp_col, idx)

        if tasa_col:
            tasa = float(pd.to_numeric(row.get(tasa_col, 0), errors='coerce') or 0)
        else:
            tasa = (reac_v + com_v + comp_v) / alcance if alcance > 0 else 0.0

        posts.append({
            'marca':              marca_nombre,
            'red':                'Facebook',
            'fecha':              row[fecha_col].strftime('%Y-%m-%d'),
            'titulo':             titulo[:500],
            'tipo':               str(row.get(tipo_col, '') if tipo_col else ''),
            'url':                str(row.get(url_col,  '') if url_col  else ''),
            'impresiones':        alcance,
            'visualizaciones':    n(viz_col, idx),
            'clics':              n(clics_col, idx),
            'reacciones':         reac_v,
            'comentarios':        com_v,
            'compartidos':        comp_v,
            'seguidores_ganados': 0.0,
            'tasa_interaccion':   tasa,
            'archivo':            archivo,
        })
    return posts


# ── Contenido Instagram ───────────────────────────────────────────────────────

def parse_contenido_instagram(file_obj, marca_nombre, archivo):
    """
    Parsea k1_contenido_instagram.xlsx — export de Meta Business Suite → Instagram Publicaciones.
    Encabezados en fila 0. Fecha en 'Hora de publicación' (MM/DD/YYYY HH:MM).
    """
    df = pd.read_excel(file_obj, header=0, engine='openpyxl')
    df.columns = [str(c).strip() for c in df.columns]

    def fc(*kws):
        for kw in kws:
            m = next((c for c in df.columns if kw.lower() in c.lower()), None)
            if m:
                return m
        return None

    fecha_col  = fc('hora de publicación', 'fecha de publicación', 'fecha', 'date')
    desc_col   = fc('descripción', 'descripcion', 'caption', 'título', 'titulo')
    tipo_col   = fc('tipo de publicación', 'tipo', 'type')
    url_col    = fc('enlace permanente', 'enlace', 'url', 'permalink')
    imp_col    = fc('alcance', 'reach', 'impresiones')
    viz_col    = fc('visualizaciones', 'views', 'reproducciones')
    reac_col   = fc('me gusta', 'likes', 'reacciones', 'reactions')
    com_col    = fc('comentarios', 'comments')
    comp_col   = fc('veces que se compartió', 'compartidos', 'shares')
    seg_col    = fc('seguimientos', 'seguidores', 'followers gained')
    guard_col  = fc('veces que se guardó', 'guardados', 'saved')

    if not fecha_col:
        raise ValueError("No se encontró columna de fecha en el archivo de contenido Instagram.")

    df[fecha_col] = pd.to_datetime(df[fecha_col], dayfirst=False, errors='coerce')
    df = df.dropna(subset=[fecha_col])

    def n(col, idx):
        if col and col in df.columns:
            return float(pd.to_numeric(df.loc[idx, col], errors='coerce') or 0)
        return 0.0

    posts = []
    for idx, row in df.iterrows():
        alcance = n(imp_col, idx)
        reac_v  = n(reac_col, idx)
        com_v   = n(com_col, idx)
        comp_v  = n(comp_col, idx)
        tasa    = (reac_v + com_v + comp_v) / alcance if alcance > 0 else 0.0

        posts.append({
            'marca':              marca_nombre,
            'red':                'Instagram',
            'fecha':              row[fecha_col].strftime('%Y-%m-%d'),
            'titulo':             str(row.get(desc_col, '') if desc_col else '')[:500],
            'tipo':               str(row.get(tipo_col,  '') if tipo_col  else ''),
            'url':                str(row.get(url_col,   '') if url_col   else ''),
            'impresiones':        alcance,
            'visualizaciones':    n(viz_col, idx),
            'clics':              n(guard_col, idx),   # "Veces que se guardó" → clics
            'reacciones':         reac_v,
            'comentarios':        com_v,
            'compartidos':        comp_v,
            'seguidores_ganados': n(seg_col, idx),
            'tasa_interaccion':   tasa,
            'archivo':            archivo,
        })
    return posts


# ── Utilidad interna ──────────────────────────────────────────────────────────

def _find_col(df, keywords):
    for kw in keywords:
        m = next((c for c in df.columns if kw.lower() in c.lower()), None)
        if m:
            return m
    return None
