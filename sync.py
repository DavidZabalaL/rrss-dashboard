# sync.py — Sincronización opcional con GitHub
#
# Configura en .streamlit/secrets.toml:
#   GITHUB_TOKEN   = "ghp_..."
#   GITHUB_REPO    = "usuario/repositorio"
#   GITHUB_DB_PATH = "data/rrss.db"   # ruta dentro del repo

import base64
import requests
import streamlit as st
from database import DB_PATH


def _cfg():
    try:
        return (
            st.secrets.get("GITHUB_TOKEN", ""),
            st.secrets.get("GITHUB_REPO",  ""),
            st.secrets.get("GITHUB_DB_PATH", "data/rrss.db"),
        )
    except Exception:
        return "", "", ""


def _headers(token):
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}


def github_configured():
    token, repo, _ = _cfg()
    return bool(token and repo)


def pull():
    """Descarga la BD desde GitHub → local. Retorna True si exitoso."""
    token, repo, path = _cfg()
    if not token or not repo:
        return False
    url  = f"https://api.github.com/repos/{repo}/contents/{path}"
    resp = requests.get(url, headers=_headers(token), timeout=15)
    if resp.status_code == 200:
        content = base64.b64decode(resp.json()["content"])
        DB_PATH.parent.mkdir(exist_ok=True)
        DB_PATH.write_bytes(content)
        return True
    return False


def push():
    """Sube la BD local → GitHub. Retorna True si exitoso."""
    token, repo, path = _cfg()
    if not token or not repo or not DB_PATH.exists():
        return False
    content = base64.b64encode(DB_PATH.read_bytes()).decode()
    url     = f"https://api.github.com/repos/{repo}/contents/{path}"
    # Obtener SHA actual si el archivo ya existe
    r = requests.get(url, headers=_headers(token), timeout=15)
    sha = r.json().get("sha", "") if r.status_code == 200 else ""
    payload = {
        "message": "sync: update RRSS database",
        "content": content,
        "committer": {"name": "RRSS Bot", "email": "bot@rrss.local"},
    }
    if sha:
        payload["sha"] = sha
    resp = requests.put(url, json=payload, headers=_headers(token), timeout=30)
    return resp.status_code in (200, 201)
