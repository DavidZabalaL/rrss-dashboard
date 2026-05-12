# config.py

REDES = ['LinkedIn', 'Facebook', 'Instagram']

MARCAS = {'k1': 'Kabat One', 'sym': 'SYM'}

METRICAS = {
    'LinkedIn': [
        {'key': 'publicaciones',         'label': 'Publicaciones',      'icon': '📝', 'tipo': 'manual'},
        {'key': 'incremento_seguidores', 'label': 'Incr. Seguidores',   'icon': '👥', 'tipo': 'archivo'},
        {'key': 'alcance',               'label': 'Alcance',            'icon': '🎯', 'tipo': 'archivo'},
        {'key': 'impresiones',           'label': 'Impresiones',        'icon': '👁️', 'tipo': 'archivo'},
        {'key': 'reacciones',            'label': 'Reacciones',         'icon': '❤️', 'tipo': 'auto_4pct'},
        {'key': 'comentarios',           'label': 'Comentarios',        'icon': '💬', 'tipo': 'archivo'},
    ],
    'Facebook': [
        {'key': 'publicaciones',         'label': 'Publicaciones',      'icon': '📝', 'tipo': 'manual'},
        {'key': 'incremento_seguidores', 'label': 'Incr. Seguidores',   'icon': '👥', 'tipo': 'archivo'},
        {'key': 'visualizaciones',       'label': 'Visualizaciones',    'icon': '🎬', 'tipo': 'archivo'},
        {'key': 'vis_seguidores',        'label': 'Viz. Seguidores',    'icon': '👤', 'tipo': 'manual_50pct'},
        {'key': 'vis_no_seguidores',     'label': 'Viz. No Seguidores', 'icon': '👤', 'tipo': 'manual_50pct'},
        {'key': 'interaccion',           'label': 'Interacciones',      'icon': '💫', 'tipo': 'archivo'},
        {'key': 'visitas',               'label': 'Visitas',            'icon': '🔗', 'tipo': 'archivo'},
    ],
    'Instagram': [
        {'key': 'publicaciones',         'label': 'Publicaciones',      'icon': '📝', 'tipo': 'manual'},
        {'key': 'incremento_seguidores', 'label': 'Incr. Seguidores',   'icon': '👥', 'tipo': 'archivo'},
        {'key': 'visualizaciones',       'label': 'Visualizaciones',    'icon': '🎬', 'tipo': 'archivo'},
        {'key': 'alcance',               'label': 'Alcance',            'icon': '🎯', 'tipo': 'manual'},
        {'key': 'interaccion',           'label': 'Interacciones',      'icon': '💫', 'tipo': 'archivo'},
        {'key': 'visitas',               'label': 'Visitas',            'icon': '🔗', 'tipo': 'archivo'},
    ],
}

# Mapeo columnas export LinkedIn Analytics (MM/DD/YYYY — dayfirst=False)
LINKEDIN_COL_MAP = {
    'impresiones':           'Impresiones (totales)',
    'alcance':               'Impresiones únicas (orgánicas)',
    'reacciones':            'Reacciones (total)',
    'comentarios':           'Comentarios (orgánicos)',
    'incremento_seguidores': 'Nuevos seguidores',
}

COLORS = {
    'primary': '#1e90ff', 'secondary': '#00bfff', 'accent': '#00d4ff',
    'bg': '#020c1b',      'bg2': '#0a1628',        'border': '#1e3a5f',
    'text': '#e2e8f0',    'muted': '#5b8db8',
    'success': '#22c55e', 'warning': '#ffd700',    'danger': '#ff4444',
}

CHART_COLORS = [
    '#1e90ff', '#00bfff', '#22c55e', '#ffd700', '#ff6b6b',
    '#c084fc', '#34d399', '#fb923c', '#60a5fa', '#a78bfa',
]
