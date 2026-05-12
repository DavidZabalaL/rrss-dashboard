# database.py — SQLite persistence

import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "rrss.db"
DB_PATH.parent.mkdir(exist_ok=True)


def _conn():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with _conn() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            nombre   TEXT NOT NULL,
            role     TEXT NOT NULL DEFAULT 'viewer'
        );

        CREATE TABLE IF NOT EXISTS metricas_diarias (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            marca     TEXT NOT NULL,
            red       TEXT NOT NULL,
            metrica   TEXT NOT NULL,
            fecha     TEXT NOT NULL,
            valor     REAL NOT NULL DEFAULT 0,
            archivo   TEXT,
            UNIQUE(marca, red, metrica, fecha)
        );

        CREATE TABLE IF NOT EXISTS kpi_objetivos (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            marca   TEXT NOT NULL,
            red     TEXT NOT NULL,
            año     INTEGER NOT NULL,
            mes     INTEGER NOT NULL,
            metrica TEXT NOT NULL,
            valor   REAL NOT NULL DEFAULT 0,
            UNIQUE(marca, red, año, mes, metrica)
        );

        CREATE TABLE IF NOT EXISTS kpi_manuales (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            marca   TEXT NOT NULL,
            red     TEXT NOT NULL,
            año     INTEGER NOT NULL,
            mes     INTEGER NOT NULL,
            metrica TEXT NOT NULL,
            valor   REAL NOT NULL DEFAULT 0,
            UNIQUE(marca, red, año, mes, metrica)
        );

        CREATE TABLE IF NOT EXISTS contenido_posts (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            marca             TEXT NOT NULL,
            red               TEXT NOT NULL,
            fecha             TEXT,
            titulo            TEXT,
            tipo              TEXT,
            url               TEXT,
            impresiones       REAL DEFAULT 0,
            visualizaciones   REAL DEFAULT 0,
            clics             REAL DEFAULT 0,
            reacciones        REAL DEFAULT 0,
            comentarios       REAL DEFAULT 0,
            compartidos       REAL DEFAULT 0,
            seguidores_ganados REAL DEFAULT 0,
            tasa_interaccion  REAL DEFAULT 0,
            archivo           TEXT,
            UNIQUE(marca, red, fecha, titulo)
        );
        """)


# ── Métricas diarias ──────────────────────────────────────────────────────────

def save_metricas_bulk(rows):
    with _conn() as con:
        con.executemany("""
        INSERT INTO metricas_diarias (marca, red, metrica, fecha, valor, archivo)
        VALUES (:marca, :red, :metrica, :fecha, :valor, :archivo)
        ON CONFLICT(marca, red, metrica, fecha) DO UPDATE SET
            valor   = excluded.valor,
            archivo = excluded.archivo
        """, rows)


def get_metricas_mensuales(marca, red, año, mes):
    sql = """
    SELECT metrica, SUM(valor) as total
    FROM metricas_diarias
    WHERE marca=? AND red=? AND strftime('%Y',fecha)=? AND strftime('%m',fecha)=?
    GROUP BY metrica
    """
    with _conn() as con:
        rows = con.execute(sql, (marca, red, str(año), f"{mes:02d}")).fetchall()
    return {r['metrica']: r['total'] for r in rows}


def get_metricas_historico_mensual(marca, red):
    sql = """
    SELECT metrica,
           CAST(strftime('%Y',fecha) AS INTEGER) AS año,
           CAST(strftime('%m',fecha) AS INTEGER) AS mes,
           SUM(valor) AS valor
    FROM metricas_diarias
    WHERE marca=? AND red=?
    GROUP BY metrica, año, mes
    ORDER BY año, mes
    """
    with _conn() as con:
        rows = con.execute(sql, (marca, red)).fetchall()
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


def get_redes_con_datos(marca):
    with _conn() as con:
        rows = con.execute(
            "SELECT DISTINCT red FROM metricas_diarias WHERE marca=?", (marca,)
        ).fetchall()
    return [r['red'] for r in rows]


def get_last_data_month(marca, red):
    """Returns (año, mes) of the most recent month with data, or None."""
    sql = """
    SELECT CAST(strftime('%Y',fecha) AS INTEGER) AS año,
           CAST(strftime('%m',fecha) AS INTEGER) AS mes
    FROM metricas_diarias
    WHERE marca=? AND red=?
    ORDER BY fecha DESC LIMIT 1
    """
    with _conn() as con:
        row = con.execute(sql, (marca, red)).fetchone()
    return (row['año'], row['mes']) if row else None


# ── KPI objetivos ─────────────────────────────────────────────────────────────

def save_kpi_objetivos_bulk(marca, red, año, mes, data):
    rows = [
        {'marca': marca, 'red': red, 'año': año, 'mes': mes,
         'metrica': k, 'valor': float(v or 0)}
        for k, v in data.items()
    ]
    with _conn() as con:
        con.executemany("""
        INSERT INTO kpi_objetivos (marca, red, año, mes, metrica, valor)
        VALUES (:marca, :red, :año, :mes, :metrica, :valor)
        ON CONFLICT(marca, red, año, mes, metrica) DO UPDATE SET valor=excluded.valor
        """, rows)


def get_kpi_objetivos(marca, red, año, mes):
    with _conn() as con:
        rows = con.execute(
            "SELECT metrica, valor FROM kpi_objetivos WHERE marca=? AND red=? AND año=? AND mes=?",
            (marca, red, año, mes)
        ).fetchall()
    return {r['metrica']: r['valor'] for r in rows}


# ── KPI manuales ──────────────────────────────────────────────────────────────

def save_kpi_manuales_bulk(marca, red, año, mes, data):
    rows = [
        {'marca': marca, 'red': red, 'año': año, 'mes': mes,
         'metrica': k, 'valor': float(v or 0)}
        for k, v in data.items()
    ]
    with _conn() as con:
        con.executemany("""
        INSERT INTO kpi_manuales (marca, red, año, mes, metrica, valor)
        VALUES (:marca, :red, :año, :mes, :metrica, :valor)
        ON CONFLICT(marca, red, año, mes, metrica) DO UPDATE SET valor=excluded.valor
        """, rows)


def get_kpi_manual(marca, red, metrica, año, mes):
    with _conn() as con:
        row = con.execute(
            "SELECT valor FROM kpi_manuales WHERE marca=? AND red=? AND metrica=? AND año=? AND mes=?",
            (marca, red, metrica, año, mes)
        ).fetchone()
    return float(row['valor']) if row else 0.0


# ── Contenido posts ───────────────────────────────────────────────────────────

def save_contenido_posts(rows):
    with _conn() as con:
        con.executemany("""
        INSERT INTO contenido_posts
            (marca, red, fecha, titulo, tipo, url, impresiones, visualizaciones,
             clics, reacciones, comentarios, compartidos, seguidores_ganados,
             tasa_interaccion, archivo)
        VALUES
            (:marca, :red, :fecha, :titulo, :tipo, :url, :impresiones, :visualizaciones,
             :clics, :reacciones, :comentarios, :compartidos, :seguidores_ganados,
             :tasa_interaccion, :archivo)
        ON CONFLICT(marca, red, fecha, titulo) DO UPDATE SET
            tipo=excluded.tipo, url=excluded.url,
            impresiones=excluded.impresiones, visualizaciones=excluded.visualizaciones,
            clics=excluded.clics, reacciones=excluded.reacciones,
            comentarios=excluded.comentarios, compartidos=excluded.compartidos,
            seguidores_ganados=excluded.seguidores_ganados,
            tasa_interaccion=excluded.tasa_interaccion,
            archivo=excluded.archivo
        """, rows)


def get_contenido_posts(marca, red, año, mes=None):
    if mes:
        sql = """SELECT * FROM contenido_posts
                 WHERE marca=? AND red=? AND strftime('%Y',fecha)=? AND strftime('%m',fecha)=?
                 ORDER BY fecha DESC"""
        params = (marca, red, str(año), f"{mes:02d}")
    else:
        sql = """SELECT * FROM contenido_posts
                 WHERE marca=? AND red=? AND strftime('%Y',fecha)=?
                 ORDER BY fecha DESC"""
        params = (marca, red, str(año))
    with _conn() as con:
        rows = con.execute(sql, params).fetchall()
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


def get_contenido_redes(marca):
    with _conn() as con:
        rows = con.execute(
            "SELECT DISTINCT red FROM contenido_posts WHERE marca=?", (marca,)
        ).fetchall()
    return [r['red'] for r in rows]


# ── Usuarios ──────────────────────────────────────────────────────────────────

_DEFAULT_USERS = [
    ('admin',     'kabat2026', 'Administrador', 'admin'),
    ('Marketing', 'mkt2026',   'Marketing',     'uploader'),
]


def seed_usuarios():
    """Inserta usuarios por defecto solo si la tabla está vacía."""
    with _conn() as con:
        if con.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
            con.executemany(
                "INSERT OR IGNORE INTO usuarios (username, password, nombre, role) VALUES (?,?,?,?)",
                _DEFAULT_USERS,
            )
        # Migración: Marketing debe tener role='uploader', no 'viewer'
        con.execute(
            "UPDATE usuarios SET role='uploader' WHERE username='Marketing' AND role='viewer'"
        )


def get_usuarios():
    """Devuelve dict {username: {password, nombre, role}} para auth."""
    with _conn() as con:
        rows = con.execute(
            "SELECT username, password, nombre, role FROM usuarios"
        ).fetchall()
    return {r['username']: {'password': r['password'], 'nombre': r['nombre'], 'role': r['role']}
            for r in rows}


def get_usuarios_lista():
    """Devuelve lista de dicts para mostrar en UI (incluye password)."""
    with _conn() as con:
        rows = con.execute(
            "SELECT username, password, nombre, role FROM usuarios ORDER BY role DESC, username"
        ).fetchall()
    return [dict(r) for r in rows]


def update_usuario_password(username, new_password):
    with _conn() as con:
        con.execute("UPDATE usuarios SET password=? WHERE username=?",
                    (new_password, username))


def add_usuario(username, password, nombre, role='viewer'):
    with _conn() as con:
        con.execute(
            "INSERT OR REPLACE INTO usuarios (username, password, nombre, role) VALUES (?,?,?,?)",
            (username, password, nombre, role),
        )


def delete_usuario(username):
    with _conn() as con:
        con.execute("DELETE FROM usuarios WHERE username != 'admin' AND username=?",
                    (username,))
